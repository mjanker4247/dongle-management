<#
.SYNOPSIS
  Dongle Manager - local process manager for backend + frontend on Windows.

.DESCRIPTION
  Mirrors ./manage (bash) for Windows PowerShell.

.EXAMPLE
  .\manage.ps1 setup
  .\manage.ps1 start
  .\manage.ps1 status
  .\manage.ps1 stop
#>
[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [ValidateSet(
        'setup', 'install',
        'update', 'upgrade',
        'start', 'up',
        'stop', 'down',
        'restart',
        'status', 'ps',
        'logs', 'log',
        'migrate', 'db',
        'seed',
        'test', 'tests',
        'backend', 'be', 'api',
        'frontend', 'fe', 'ui',
        'doctor', 'check',
        'help', '-h', '--help'
    )]
    [string]$Command = 'help',

    [Parameter(Position = 1, ValueFromRemainingArguments = $true)]
    [string[]]$ArgsRest
)

$ErrorActionPreference = 'Stop'

$RootDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackendDir = Join-Path $RootDir 'backend'
$FrontendDir = Join-Path $RootDir 'frontend'
$RuntimeDir = Join-Path $RootDir '.run'
$LogDir = Join-Path $RuntimeDir 'logs'
$PidDir = Join-Path $RuntimeDir 'pids'

$BackendHost = if ($env:BACKEND_HOST) { $env:BACKEND_HOST } else { '127.0.0.1' }
$BackendPort = if ($env:BACKEND_PORT) { [int]$env:BACKEND_PORT } else { 8000 }
$FrontendHost = if ($env:FRONTEND_HOST) { $env:FRONTEND_HOST } else { '127.0.0.1' }
$FrontendPort = if ($env:FRONTEND_PORT) { [int]$env:FRONTEND_PORT } else { 5173 }
$SeedOnStartup = if ($env:SEED_ON_STARTUP) { $env:SEED_ON_STARTUP } else { 'true' }

$BackendPidFile = Join-Path $PidDir 'backend.pid'
$FrontendPidFile = Join-Path $PidDir 'frontend.pid'
$BackendLog = Join-Path $LogDir 'backend.log'
$BackendErrLog = Join-Path $LogDir 'backend.err.log'
$FrontendLog = Join-Path $LogDir 'frontend.log'
$FrontendErrLog = Join-Path $LogDir 'frontend.err.log'

function Write-Info([string]$Message) { Write-Host "➜ $Message" -ForegroundColor Cyan }
function Write-Ok([string]$Message) { Write-Host "✔ $Message" -ForegroundColor Green }
function Write-Warn([string]$Message) { Write-Host "⚠ $Message" -ForegroundColor Yellow }
function Write-Err([string]$Message) { Write-Host "✖ $Message" -ForegroundColor Red }

function Ensure-Dirs {
    New-Item -ItemType Directory -Force -Path $LogDir, $PidDir | Out-Null
}

function Test-CommandExists([string]$Name) {
    return [bool](Get-Command $Name -ErrorAction SilentlyContinue)
}

function Ensure-Uv {
    if (Test-CommandExists 'uv') { return }

    Write-Info 'Installing uv...'
    # Official Windows installer from Astral
    powershell -NoProfile -ExecutionPolicy Bypass -Command "irm https://astral.sh/uv/install.ps1 | iex"
    $env:Path = [System.Environment]::GetEnvironmentVariable('Path', 'User') + ';' +
                [System.Environment]::GetEnvironmentVariable('Path', 'Machine') + ';' +
                $env:Path

    if (-not (Test-CommandExists 'uv')) {
        Write-Err 'uv installation finished but uv is not on PATH. Restart the shell and retry.'
        exit 1
    }
}

function Ensure-Node {
    if (-not (Test-CommandExists 'node')) {
        Write-Err 'Missing required command: node'
        exit 1
    }
    if (-not (Test-CommandExists 'npm')) {
        Write-Err 'Missing required command: npm'
        exit 1
    }
}

function Ensure-EnvFiles {
    $backendEnv = Join-Path $BackendDir '.env'
    $backendExample = Join-Path $BackendDir '.env.example'
    if (-not (Test-Path $backendEnv)) {
        if (Test-Path $backendExample) {
            Copy-Item $backendExample $backendEnv
            Write-Ok 'Created backend/.env from .env.example'
        }
        else {
            Write-Warn 'No backend/.env or .env.example found'
        }
    }

    $frontendEnv = Join-Path $FrontendDir '.env'
    $frontendExample = Join-Path $FrontendDir '.env.example'
    if (-not (Test-Path $frontendEnv) -and (Test-Path $frontendExample)) {
        Copy-Item $frontendExample $frontendEnv
        Write-Ok 'Created frontend/.env from .env.example'
    }
}

function Invoke-BackendUv {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$UvArgs)
    Push-Location $BackendDir
    try {
        & uv @UvArgs
        if ($LASTEXITCODE -ne 0) { throw "uv $($UvArgs -join ' ') failed with exit code $LASTEXITCODE" }
    }
    finally {
        Pop-Location
    }
}

function Test-NeedsPostgresExtra {
    $dbUrl = $env:DATABASE_URL
    if ([string]::IsNullOrWhiteSpace($dbUrl)) {
        $envFile = Join-Path $BackendDir '.env'
        if (Test-Path $envFile) {
            $line = Get-Content $envFile | Where-Object { $_ -match '^DATABASE_URL=' } | Select-Object -First 1
            if ($line) {
                $dbUrl = ($line -split '=', 2)[1].Trim().Trim('"').Trim("'")
            }
        }
    }
    return ($dbUrl -like 'postgresql*' -or $dbUrl -like 'postgres*')
}

function Invoke-BackendUvSync {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$SyncArgs)
    if (Test-NeedsPostgresExtra) {
        Write-Info 'DATABASE_URL uses PostgreSQL — installing postgres extra (psycopg)'
        Invoke-BackendUv sync --extra postgres @SyncArgs
    }
    else {
        Invoke-BackendUv sync @SyncArgs
    }
}

function Read-PidFile([string]$Path) {
    if (-not (Test-Path $Path)) { return $null }
    $raw = (Get-Content -Path $Path -Raw).Trim()
    if ([string]::IsNullOrWhiteSpace($raw)) { return $null }
    return [int]$raw
}

function Test-PidRunning([Nullable[int]]$ProcessId) {
    if (-not $ProcessId) { return $false }
    try {
        $proc = Get-Process -Id $ProcessId -ErrorAction Stop
        return $null -ne $proc
    }
    catch {
        return $false
    }
}

function Test-PortInUse([int]$Port) {
    try {
        $listeners = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
        return $null -ne $listeners
    }
    catch {
        # Fallback when Get-NetTCPConnection is unavailable
        $lines = netstat -ano | Select-String ":$Port\s+.*LISTENING"
        return $null -ne $lines
    }
}

function Stop-TrackedProcess {
    param(
        [string]$Name,
        [string]$PidFile,
        [int]$Port = 0
    )

    $processId = Read-PidFile $PidFile
    if (Test-PidRunning $processId) {
        Write-Info "Stopping $Name (pid $processId)..."
        try {
            # Kill process tree (uvicorn reloader / npm -> vite children)
            & taskkill /PID $processId /T /F 2>$null | Out-Null
        }
        catch {
            Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
        }
        Start-Sleep -Milliseconds 400
        Write-Ok "Stopped $Name"
    }
    else {
        Write-Info "$Name is not running"
    }

    if (Test-Path $PidFile) { Remove-Item $PidFile -Force }

    if ($Port -gt 0 -and (Test-PortInUse $Port)) {
        Write-Info "Freeing port $Port still held by $Name child processes..."
        try {
            $conns = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
            foreach ($conn in $conns) {
                & taskkill /PID $conn.OwningProcess /T /F 2>$null | Out-Null
            }
        }
        catch {
            $matches = netstat -ano | Select-String ":$Port\s+.*LISTENING"
            foreach ($match in $matches) {
                $parts = ($match.ToString() -split '\s+') | Where-Object { $_ }
                $owner = $parts[-1]
                if ($owner -match '^\d+$') {
                    & taskkill /PID $owner /T /F 2>$null | Out-Null
                }
            }
        }
    }
}

function Start-BackendBackground {
    Ensure-Dirs
    Ensure-Uv
    Ensure-EnvFiles

    $existing = Read-PidFile $BackendPidFile
    if (Test-PidRunning $existing) {
        Write-Warn "Backend already running (pid $existing)"
        return
    }
    if (Test-PortInUse $BackendPort) {
        Write-Err "Port $BackendPort is already in use"
        exit 1
    }

    Write-Info "Starting backend on http://${BackendHost}:${BackendPort} ..."
    $env:SEED_ON_STARTUP = $SeedOnStartup

    $argList = @(
        'run', 'uvicorn', 'app.main:app',
        '--host', $BackendHost,
        '--port', "$BackendPort",
        '--reload'
    )

    $proc = Start-Process -FilePath 'uv' `
        -ArgumentList $argList `
        -WorkingDirectory $BackendDir `
        -RedirectStandardOutput $BackendLog `
        -RedirectStandardError $BackendErrLog `
        -WindowStyle Hidden `
        -PassThru

    Set-Content -Path $BackendPidFile -Value $proc.Id -NoNewline
    Start-Sleep -Seconds 1

    if (Test-PidRunning $proc.Id) {
        Write-Ok "Backend started (pid $($proc.Id)) â€” log: $BackendLog"
    }
    else {
        Write-Err "Backend failed to start; see $BackendLog"
        exit 1
    }
}

function Start-FrontendBackground {
    Ensure-Dirs
    Ensure-Node
    Ensure-EnvFiles

    $existing = Read-PidFile $FrontendPidFile
    if (Test-PidRunning $existing) {
        Write-Warn "Frontend already running (pid $existing)"
        return
    }
    if (Test-PortInUse $FrontendPort) {
        Write-Err "Port $FrontendPort is already in use"
        exit 1
    }

    Write-Info "Starting frontend on http://${FrontendHost}:${FrontendPort} ..."

    # Use cmd /c so npm.cmd works reliably under Start-Process on Windows
    $cmd = "npm run dev -- --host $FrontendHost --port $FrontendPort"
    $proc = Start-Process -FilePath 'cmd.exe' `
        -ArgumentList '/c', $cmd `
        -WorkingDirectory $FrontendDir `
        -RedirectStandardOutput $FrontendLog `
        -RedirectStandardError $FrontendErrLog `
        -WindowStyle Hidden `
        -PassThru

    Set-Content -Path $FrontendPidFile -Value $proc.Id -NoNewline
    Start-Sleep -Seconds 1

    if (Test-PidRunning $proc.Id) {
        Write-Ok "Frontend started (pid $($proc.Id)) â€” log: $FrontendLog"
    }
    else {
        Write-Err "Frontend failed to start; see $FrontendLog"
        exit 1
    }
}

function Invoke-Setup {
    Ensure-Dirs
    Ensure-Uv
    Ensure-Node
    Ensure-EnvFiles

    Write-Info 'Syncing backend dependencies with uv...'
    Invoke-BackendUvSync
    Write-Ok 'Backend dependencies ready'

    Write-Info 'Installing frontend dependencies...'
    Push-Location $FrontendDir
    try {
        & npm install
        if ($LASTEXITCODE -ne 0) { throw "npm install failed with exit code $LASTEXITCODE" }
    }
    finally {
        Pop-Location
    }
    Write-Ok 'Frontend dependencies ready'

    Write-Info 'Running database migrations...'
    Invoke-BackendUv run alembic upgrade head
    Write-Ok 'Migrations applied'
    Write-Ok 'Setup complete. Start the app with: .\manage.ps1 start'
}

function Invoke-Update {
    Ensure-Dirs
    Ensure-Uv
    Ensure-Node
    Ensure-EnvFiles

    Write-Info 'Updating backend lock / dependencies...'
    if ($ArgsRest -contains '--refresh') {
        Invoke-BackendUv lock --upgrade
    }
    Invoke-BackendUvSync
    Write-Ok 'Backend updated'

    Write-Info 'Updating frontend packages (npm install)...'
    Push-Location $FrontendDir
    try {
        & npm install
        if ($LASTEXITCODE -ne 0) { throw "npm install failed with exit code $LASTEXITCODE" }
    }
    finally {
        Pop-Location
    }
    Write-Ok 'Frontend updated'

    Write-Info 'Applying migrations...'
    Invoke-BackendUv run alembic upgrade head
    Write-Ok 'Update complete'
}

function Invoke-Start {
    Start-BackendBackground
    Start-FrontendBackground
    Write-Host ''
    Write-Ok 'Dongle Manager is running'
    Write-Host "  UI:      http://${FrontendHost}:${FrontendPort}"
    Write-Host "  API:     http://${BackendHost}:${BackendPort}/api"
    Write-Host "  Docs:    http://${BackendHost}:${BackendPort}/docs"
    Write-Host '  Status:  .\manage.ps1 status'
    Write-Host '  Logs:    .\manage.ps1 logs'
    Write-Host '  Stop:    .\manage.ps1 stop'
}

function Invoke-Stop {
    Ensure-Dirs
    Stop-TrackedProcess -Name 'frontend' -PidFile $FrontendPidFile -Port $FrontendPort
    Stop-TrackedProcess -Name 'backend' -PidFile $BackendPidFile -Port $BackendPort

    if (Test-PortInUse $FrontendPort) {
        Write-Warn "Port $FrontendPort still in use (may be an external process)"
    }
    if (Test-PortInUse $BackendPort) {
        Write-Warn "Port $BackendPort still in use (may be an external process)"
    }
}

function Invoke-Restart {
    Invoke-Stop
    Start-Sleep -Milliseconds 500
    Invoke-Start
}

function Invoke-Status {
    Ensure-Dirs
    $bpid = Read-PidFile $BackendPidFile
    $fpid = Read-PidFile $FrontendPidFile

    Write-Host 'Dongle Manager status'
    Write-Host '---------------------'

    if (Test-PidRunning $bpid) {
        Write-Ok "Backend  running  pid=$bpid  http://${BackendHost}:${BackendPort}"
    }
    else {
        Write-Warn 'Backend  stopped'
    }

    if (Test-PidRunning $fpid) {
        Write-Ok "Frontend running  pid=$fpid  http://${FrontendHost}:${FrontendPort}"
    }
    else {
        Write-Warn 'Frontend stopped'
    }

    if ((Test-PidRunning $bpid) -and (Test-CommandExists 'curl.exe')) {
        try {
            & curl.exe -fsS "http://${BackendHost}:${BackendPort}/health" | Out-Null
            Write-Ok 'Health   /health OK'
        }
        catch {
            Write-Warn 'Health   /health not responding yet'
        }
    }
}

function Get-ServiceLogPaths([string]$Service) {
    switch ($Service) {
        'backend' { return @($BackendLog, $BackendErrLog) }
        'frontend' { return @($FrontendLog, $FrontendErrLog) }
        default { return @($BackendLog, $BackendErrLog, $FrontendLog, $FrontendErrLog) }
    }
}

function Invoke-Logs {
    Ensure-Dirs
    $target = if ($ArgsRest -and $ArgsRest.Count -gt 0) { $ArgsRest[0].ToLowerInvariant() } else { 'all' }

    switch -Regex ($target) {
        '^(backend|be|api)$' {
            $paths = Get-ServiceLogPaths 'backend'
            foreach ($p in $paths) {
                if (-not (Test-Path $p)) { New-Item -ItemType File -Path $p -Force | Out-Null }
            }
            Write-Info "Tailing backend logs (Ctrl+C to stop)"
            Get-Content -Path $paths -Wait -Tail 100
        }
        '^(frontend|fe|ui)$' {
            $paths = Get-ServiceLogPaths 'frontend'
            foreach ($p in $paths) {
                if (-not (Test-Path $p)) { New-Item -ItemType File -Path $p -Force | Out-Null }
            }
            Write-Info "Tailing frontend logs (Ctrl+C to stop)"
            Get-Content -Path $paths -Wait -Tail 100
        }
        default {
            $paths = Get-ServiceLogPaths 'all'
            foreach ($p in $paths) {
                if (-not (Test-Path $p)) { New-Item -ItemType File -Path $p -Force | Out-Null }
            }
            Write-Info 'Showing combined logs (Ctrl+C to stop)'
            try {
                Get-Content -Path $paths -Wait -Tail 50
            }
            catch {
                Write-Warn 'Combined wait not supported in this PowerShell version. Use:'
                Write-Host '  .\manage.ps1 logs backend'
                Write-Host '  .\manage.ps1 logs frontend'
                Get-Content -Path $paths -Tail 50
            }
        }
    }
}

function Invoke-Migrate {
    Ensure-Uv
    Invoke-BackendUv run alembic upgrade head
    Write-Ok 'Migrations applied'
}

function Invoke-Test {
    Ensure-Uv
    Write-Info 'Running backend tests...'
    Push-Location $BackendDir
    try {
        $env:SEED_ON_STARTUP = 'false'
        & uv run pytest app/tests -v @ArgsRest
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    }
    finally {
        Pop-Location
    }
}

function Invoke-BackendForeground {
    Ensure-Uv
    Ensure-EnvFiles
    Write-Info 'Starting backend in foreground...'
    $env:SEED_ON_STARTUP = $SeedOnStartup
    Set-Location $BackendDir
    & uv run uvicorn app.main:app --host $BackendHost --port $BackendPort --reload
}

function Invoke-FrontendForeground {
    Ensure-Node
    Ensure-EnvFiles
    Write-Info 'Starting frontend in foreground...'
    Set-Location $FrontendDir
    & npm run dev -- --host $FrontendHost --port $FrontendPort
}

function Invoke-Seed {
    Ensure-Uv
    Ensure-EnvFiles
    Write-Info 'Ensuring migrations are applied...'
    Invoke-BackendUv run alembic upgrade head
    Write-Info 'Seeding database (no-op if data already exists)...'

    $seedScript = @'
from app.db.session import SessionLocal
from app.db.base_models import Base
from app.db.session import engine
from app.services.seed import seed_database

Base.metadata.create_all(bind=engine)
db = SessionLocal()
try:
    seed_database(db)
    print("Seed completed (or skipped if data already present).")
finally:
    db.close()
'@
    Push-Location $BackendDir
    try {
        $seedScript | & uv run python -
        if ($LASTEXITCODE -ne 0) { throw "seed failed with exit code $LASTEXITCODE" }
    }
    finally {
        Pop-Location
    }
    Write-Ok 'Seed finished'
}

function Invoke-Doctor {
    Write-Host 'Doctor'
    Write-Host '------'

    if (Test-CommandExists 'uv') {
        $uvVersion = (& uv --version) -replace '^uv\s+', ''
        Write-Ok "uv $uvVersion"
    }
    else {
        Write-Warn 'uv not installed (.\manage.ps1 setup will install it)'
    }

    if (Test-CommandExists 'node') {
        Write-Ok "node $(& node --version)"
    }
    else {
        Write-Err 'node missing'
    }

    if (Test-CommandExists 'npm') {
        Write-Ok "npm $(& npm --version)"
    }
    else {
        Write-Err 'npm missing'
    }

    if (Test-Path (Join-Path $BackendDir 'pyproject.toml')) {
        Write-Ok 'backend/pyproject.toml present'
    }
    else {
        Write-Err 'backend/pyproject.toml missing'
    }

    if (Test-Path (Join-Path $BackendDir 'uv.lock')) {
        Write-Ok 'backend/uv.lock present'
    }
    else {
        Write-Warn 'backend/uv.lock missing (run .\manage.ps1 setup)'
    }

    if (Test-Path (Join-Path $FrontendDir 'package.json')) {
        Write-Ok 'frontend/package.json present'
    }
    else {
        Write-Err 'frontend/package.json missing'
    }

    if (Test-Path (Join-Path $BackendDir '.env')) {
        Write-Ok 'backend/.env present'
    }
    else {
        Write-Warn 'backend/.env missing'
    }

    Invoke-Status
}

function Show-Help {
    @"
Dongle Manager â€” local process manager for backend + frontend on Windows.

Usage:
  .\manage.ps1 <command> [options]

Commands:
  setup | install   Install UV deps, npm deps, env files, migrate DB
  update            Re-sync deps and apply migrations
  update --refresh  Also refresh uv.lock upgrades
  start             Start backend + frontend (background)
  stop              Stop backend + frontend
  restart           Restart both services
  status            Show process / port status
  logs [backend|frontend|all]
  migrate           Run Alembic migrations
  seed              Insert example seed data (skips if present)
  test              Run backend tests
  backend           Start only backend (foreground)
  frontend          Start only frontend (foreground)
  doctor            Check prerequisites and project health
  help              Show this help

Environment overrides:
  BACKEND_HOST / BACKEND_PORT     default 127.0.0.1 / 8000
  FRONTEND_HOST / FRONTEND_PORT   default 127.0.0.1 / 5173
  SEED_ON_STARTUP                 default true

Examples:
  .\manage.ps1 setup
  .\manage.ps1 start
  .\manage.ps1 status
  .\manage.ps1 logs backend
  .\manage.ps1 update
  .\manage.ps1 test
  .\manage.ps1 stop

If scripts are blocked, run once:
  Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
"@ | Write-Host
}

switch -Regex ($Command.ToLowerInvariant()) {
    '^(setup|install)$' { Invoke-Setup }
    '^(update|upgrade)$' { Invoke-Update }
    '^(start|up)$' { Invoke-Start }
    '^(stop|down)$' { Invoke-Stop }
    '^restart$' { Invoke-Restart }
    '^(status|ps)$' { Invoke-Status }
    '^(logs|log)$' { Invoke-Logs }
    '^(migrate|db)$' { Invoke-Migrate }
    '^seed$' { Invoke-Seed }
    '^(test|tests)$' { Invoke-Test }
    '^(backend|be|api)$' { Invoke-BackendForeground }
    '^(frontend|fe|ui)$' { Invoke-FrontendForeground }
    '^(doctor|check)$' { Invoke-Doctor }
    '^(help|-h|--help)$' { Show-Help }
    default {
        Write-Err "Unknown command: $Command"
        Show-Help
        exit 1
    }
}
