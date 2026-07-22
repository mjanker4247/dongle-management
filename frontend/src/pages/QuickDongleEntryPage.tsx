import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Alert,
  Autocomplete,
  Box,
  Button,
  Checkbox,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControl,
  InputLabel,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  MenuItem,
  Paper,
  Select,
  Stack,
  TextField,
  ToggleButton,
  ToggleButtonGroup,
  Typography,
} from '@mui/material'
import { useSnackbar } from 'notistack'
import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type KeyboardEvent,
} from 'react'
import { categoriesApi, donglesApi, pcsApi, testModulesApi } from '../api'
import type { CompletenessResult, Dongle, PC, TestModule } from '../types'
import { ErrorState, LoadingState, PageHeader } from '../components/PageHelpers'

export function QuickDongleEntryPage() {
  const { enqueueSnackbar } = useSnackbar()
  const qc = useQueryClient()
  const listRef = useRef<HTMLUListElement | null>(null)

  const pcsQuery = useQuery({ queryKey: ['pcs'], queryFn: pcsApi.list })
  const donglesQuery = useQuery({ queryKey: ['dongles'], queryFn: () => donglesApi.list() })
  const categoriesQuery = useQuery({ queryKey: ['categories'], queryFn: categoriesApi.list })
  const modulesQuery = useQuery({
    queryKey: ['test-modules', 'all-active'],
    queryFn: () => testModulesApi.list({ is_active: true, order: 'manual' }),
  })

  const [pcInput, setPcInput] = useState('')
  const [selectedPc, setSelectedPc] = useState<PC | null>(null)
  const [dongleInput, setDongleInput] = useState('')
  const [selectedDongle, setSelectedDongle] = useState<Dongle | null>(null)
  const [enabledMap, setEnabledMap] = useState<Record<number, boolean>>({})
  const [savedMap, setSavedMap] = useState<Record<number, boolean>>({})
  const [order, setOrder] = useState<'manual' | 'alpha'>('manual')
  const [categoryFilter, setCategoryFilter] = useState<number | ''>('')
  const [filterText, setFilterText] = useState('')
  const [focusedIndex, setFocusedIndex] = useState(0)
  const [createPcOpen, setCreatePcOpen] = useState(false)
  const [createDongleOpen, setCreateDongleOpen] = useState(false)
  const [pendingPcName, setPendingPcName] = useState('')
  const [pendingDongleId, setPendingDongleId] = useState('')
  const [completeness, setCompleteness] = useState<CompletenessResult | null>(null)

  const loadDongleState = useCallback(async (dongle: Dongle) => {
    const detail = await donglesApi.get(dongle.id)
    const map: Record<number, boolean> = {}
    for (const link of detail.modules || []) {
      map[link.test_module_id] = link.enabled
    }
    setSelectedDongle(detail)
    setEnabledMap(map)
    setSavedMap(map)
    setDongleInput(detail.dongle_id)
    if (detail.pc) {
      const pc = (pcsQuery.data || []).find((p) => p.id === detail.pc_id) || null
      if (pc) {
        setSelectedPc(pc)
        setPcInput(pc.name)
      }
    }
  }, [pcsQuery.data])

  const dirty = useMemo(() => {
    const keys = new Set([...Object.keys(enabledMap), ...Object.keys(savedMap)].map(Number))
    for (const id of keys) {
      if (Boolean(enabledMap[id]) !== Boolean(savedMap[id])) return true
    }
    if (selectedDongle && selectedPc && selectedDongle.pc_id !== selectedPc.id) return true
    return false
  }, [enabledMap, savedMap, selectedDongle, selectedPc])

  useEffect(() => {
    const handler = (e: BeforeUnloadEvent) => {
      if (dirty) {
        e.preventDefault()
        e.returnValue = ''
      }
    }
    window.addEventListener('beforeunload', handler)
    return () => window.removeEventListener('beforeunload', handler)
  }, [dirty])

  const modules: TestModule[] = useMemo(() => {
    let list = [...(modulesQuery.data || [])]
    if (categoryFilter !== '') {
      list = list.filter((m) => m.categories.some((c) => c.id === categoryFilter))
    }
    if (filterText.trim()) {
      const q = filterText.trim().toLowerCase()
      list = list.filter((m) => m.name.toLowerCase().includes(q))
    }
    if (order === 'alpha') {
      list.sort((a, b) => a.name.localeCompare(b.name))
    } else {
      list.sort((a, b) => a.sort_index - b.sort_index || a.name.localeCompare(b.name))
    }
    return list
  }, [modulesQuery.data, categoryFilter, filterText, order])

  useEffect(() => {
    setFocusedIndex(0)
  }, [modules.length, filterText, categoryFilter, order])

  useEffect(() => {
    if (!selectedDongle || categoryFilter === '') {
      setCompleteness(null)
      return
    }
    let cancelled = false
    donglesApi
      .completeness(selectedDongle.id, { category_id: Number(categoryFilter) })
      .then((res) => {
        if (!cancelled) setCompleteness(res)
      })
      .catch(() => {
        if (!cancelled) setCompleteness(null)
      })
    return () => {
      cancelled = true
    }
  }, [selectedDongle, categoryFilter, savedMap])

  const createPcMutation = useMutation({
    mutationFn: (name: string) => pcsApi.create({ name }),
    onSuccess: async (pc) => {
      await qc.invalidateQueries({ queryKey: ['pcs'] })
      setSelectedPc(pc)
      setPcInput(pc.name)
      setCreatePcOpen(false)
      enqueueSnackbar(`PC "${pc.name}" created`, { variant: 'success' })
    },
    onError: (err: Error) => enqueueSnackbar(err.message, { variant: 'error' }),
  })

  const createDongleMutation = useMutation({
    mutationFn: (dongle_id: string) =>
      donglesApi.create({ dongle_id, pc_id: selectedPc?.id ?? null }),
    onSuccess: async (dongle) => {
      await qc.invalidateQueries({ queryKey: ['dongles'] })
      await loadDongleState(dongle)
      setCreateDongleOpen(false)
      enqueueSnackbar(`Dongle "${dongle.dongle_id}" created`, { variant: 'success' })
    },
    onError: (err: Error) => enqueueSnackbar(err.message, { variant: 'error' }),
  })

  const saveMutation = useMutation({
    mutationFn: async () => {
      if (!selectedDongle) throw new Error('Select or create a dongle first')
      if (selectedPc && selectedDongle.pc_id !== selectedPc.id) {
        await donglesApi.assignPc(selectedDongle.id, selectedPc.id)
      }
      const modulesPayload = Object.entries(enabledMap).map(([id, enabled]) => ({
        test_module_id: Number(id),
        enabled,
      }))
      // Include currently known modules; ensure all toggled states are sent
      const allIds = new Set([
        ...modules.map((m) => m.id),
        ...Object.keys(enabledMap).map(Number),
      ])
      const payload = [...allIds].map((id) => ({
        test_module_id: id,
        enabled: Boolean(enabledMap[id]),
      }))
      void modulesPayload
      return donglesApi.updateModules(selectedDongle.id, payload)
    },
    onSuccess: async (dongle) => {
      await qc.invalidateQueries({ queryKey: ['dongles'] })
      await loadDongleState(dongle)
      enqueueSnackbar('Changes saved', { variant: 'success' })
    },
    onError: (err: Error) => enqueueSnackbar(err.message, { variant: 'error' }),
  })

  const toggleModule = (id: number) => {
    setEnabledMap((prev) => ({ ...prev, [id]: !prev[id] }))
  }

  const onListKeyDown = (e: KeyboardEvent) => {
    if (!modules.length) return
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      setFocusedIndex((i) => Math.min(i + 1, modules.length - 1))
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setFocusedIndex((i) => Math.max(i - 1, 0))
    } else if (e.key === ' ') {
      e.preventDefault()
      const mod = modules[focusedIndex]
      if (mod) toggleModule(mod.id)
    } else if (e.key === 'Enter') {
      e.preventDefault()
      if (dirty) saveMutation.mutate()
    } else if (e.key.length === 1 && !e.ctrlKey && !e.metaKey && !e.altKey) {
      setFilterText((prev) => prev + e.key)
    } else if (e.key === 'Backspace') {
      setFilterText((prev) => prev.slice(0, -1))
    } else if (e.key === 'Escape') {
      setFilterText('')
    }
  }

  useEffect(() => {
    const el = listRef.current?.querySelector<HTMLElement>(`[data-index="${focusedIndex}"]`)
    el?.scrollIntoView({ block: 'nearest' })
  }, [focusedIndex])

  if (pcsQuery.isLoading || donglesQuery.isLoading || modulesQuery.isLoading) {
    return <LoadingState />
  }
  if (pcsQuery.error || donglesQuery.error || modulesQuery.error) {
    return (
      <ErrorState
        message="Failed to load quick entry data"
        onRetry={() => {
          pcsQuery.refetch()
          donglesQuery.refetch()
          modulesQuery.refetch()
        }}
      />
    )
  }

  return (
    <>
      <PageHeader
        title="Quick Dongle Entry"
        subtitle="Keyboard-first workflow: ↑/↓ move, Space toggle, type to filter, Enter save"
        actions={
          <Stack direction="row" spacing={1} alignItems="center">
            {dirty && <Chip color="warning" label="Unsaved changes" size="small" />}
            <Button
              variant="contained"
              onClick={() => saveMutation.mutate()}
              disabled={!selectedDongle || !dirty || saveMutation.isPending}
            >
              Save
            </Button>
          </Stack>
        }
      />

      <Stack spacing={2}>
        <Paper sx={{ p: 2 }}>
          <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
            <Autocomplete
              freeSolo
              options={pcsQuery.data || []}
              getOptionLabel={(opt) => (typeof opt === 'string' ? opt : opt.name)}
              value={selectedPc}
              inputValue={pcInput}
              onInputChange={(_, v) => setPcInput(v)}
              onChange={(_, value) => {
                if (typeof value === 'string') {
                  setPendingPcName(value.trim())
                  setCreatePcOpen(true)
                  return
                }
                setSelectedPc(value)
              }}
              onBlur={() => {
                const match = (pcsQuery.data || []).find(
                  (p) => p.name.toLowerCase() === pcInput.trim().toLowerCase(),
                )
                if (match) {
                  setSelectedPc(match)
                } else if (pcInput.trim() && (!selectedPc || selectedPc.name !== pcInput.trim())) {
                  setPendingPcName(pcInput.trim())
                  setCreatePcOpen(true)
                }
              }}
              renderInput={(params) => <TextField {...params} label="PC name" />}
              sx={{ flex: 1 }}
            />
            <Autocomplete
              freeSolo
              options={donglesQuery.data || []}
              getOptionLabel={(opt) => (typeof opt === 'string' ? opt : opt.dongle_id)}
              value={selectedDongle}
              inputValue={dongleInput}
              onInputChange={(_, v) => setDongleInput(v)}
              onChange={async (_, value) => {
                if (typeof value === 'string') {
                  setPendingDongleId(value.trim())
                  setCreateDongleOpen(true)
                  return
                }
                if (value) await loadDongleState(value)
                else {
                  setSelectedDongle(null)
                  setEnabledMap({})
                  setSavedMap({})
                }
              }}
              onBlur={() => {
                const match = (donglesQuery.data || []).find(
                  (d) => d.dongle_id.toLowerCase() === dongleInput.trim().toLowerCase(),
                )
                if (match) {
                  void loadDongleState(match)
                } else if (
                  dongleInput.trim() &&
                  (!selectedDongle || selectedDongle.dongle_id !== dongleInput.trim())
                ) {
                  setPendingDongleId(dongleInput.trim())
                  setCreateDongleOpen(true)
                }
              }}
              renderInput={(params) => <TextField {...params} label="Dongle ID" />}
              sx={{ flex: 1 }}
            />
          </Stack>
        </Paper>

        <Paper sx={{ p: 2 }}>
          <Stack
            direction={{ xs: 'column', md: 'row' }}
            spacing={1.5}
            mb={1.5}
            alignItems={{ md: 'center' }}
          >
            <TextField
              size="small"
              label="Filter modules"
              value={filterText}
              onChange={(e) => setFilterText(e.target.value)}
              sx={{ minWidth: 220 }}
              helperText="Also type while list is focused"
            />
            <FormControl size="small" sx={{ minWidth: 200 }}>
              <InputLabel>Category filter</InputLabel>
              <Select
                label="Category filter"
                value={categoryFilter}
                onChange={(e) =>
                  setCategoryFilter(e.target.value === '' ? '' : Number(e.target.value))
                }
              >
                <MenuItem value="">All categories</MenuItem>
                {(categoriesQuery.data || []).map((c) => (
                  <MenuItem key={c.id} value={c.id}>
                    {c.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <ToggleButtonGroup
              exclusive
              size="small"
              value={order}
              onChange={(_, v) => v && setOrder(v)}
            >
              <ToggleButton value="manual">Manual order</ToggleButton>
              <ToggleButton value="alpha">Alphabetical</ToggleButton>
            </ToggleButtonGroup>
          </Stack>

          {completeness && (
            <Alert severity={completeness.is_complete ? 'success' : 'warning'} sx={{ mb: 1.5 }}>
              {completeness.category}: {completeness.enabled_required_modules}/
              {completeness.total_required_modules} required
              {completeness.missing_modules.length > 0 &&
                ` — missing: ${completeness.missing_modules.map((m) => m.name).join(', ')}`}
            </Alert>
          )}

          <Box
            tabIndex={0}
            onKeyDown={onListKeyDown}
            sx={{
              outline: 'none',
              border: '1px solid',
              borderColor: 'divider',
              borderRadius: 1,
              maxHeight: 480,
              overflow: 'auto',
              '&:focus': { borderColor: 'primary.main', boxShadow: '0 0 0 2px rgba(0,87,168,0.15)' },
            }}
          >
            <List ref={listRef} dense disablePadding>
              {modules.map((m, index) => (
                <ListItemButton
                  key={m.id}
                  data-index={index}
                  selected={index === focusedIndex}
                  onClick={() => {
                    setFocusedIndex(index)
                    toggleModule(m.id)
                  }}
                  sx={{
                    borderBottom: '1px solid',
                    borderColor: 'divider',
                    '&.Mui-selected': { bgcolor: 'rgba(0, 87, 168, 0.08)' },
                  }}
                >
                  <ListItemIcon sx={{ minWidth: 36 }}>
                    <Checkbox
                      edge="start"
                      checked={Boolean(enabledMap[m.id])}
                      tabIndex={-1}
                      disableRipple
                    />
                  </ListItemIcon>
                  <ListItemText
                    primary={m.name}
                    secondary={
                      m.categories.length
                        ? m.categories.map((c) => c.name).join(', ')
                        : undefined
                    }
                  />
                </ListItemButton>
              ))}
              {modules.length === 0 && (
                <Box sx={{ p: 3 }}>
                  <Typography color="text.secondary">No modules match the filter.</Typography>
                </Box>
              )}
            </List>
          </Box>
          <Typography variant="caption" color="text.secondary" mt={1} display="block">
            Focus the module list, then use keyboard shortcuts. Save explicitly with Enter or the Save button.
          </Typography>
        </Paper>
      </Stack>

      <Dialog open={createPcOpen} onClose={() => setCreatePcOpen(false)}>
        <DialogTitle>Create PC?</DialogTitle>
        <DialogContent>
          <Typography>
            PC <strong>{pendingPcName}</strong> does not exist. Create it?
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreatePcOpen(false)}>Cancel</Button>
          <Button
            variant="contained"
            onClick={() => createPcMutation.mutate(pendingPcName)}
            disabled={createPcMutation.isPending}
          >
            Create
          </Button>
        </DialogActions>
      </Dialog>

      <Dialog open={createDongleOpen} onClose={() => setCreateDongleOpen(false)}>
        <DialogTitle>Create dongle?</DialogTitle>
        <DialogContent>
          <Typography>
            Dongle <strong>{pendingDongleId}</strong> does not exist. Create it
            {selectedPc ? ` and assign to ${selectedPc.name}` : ''}?
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateDongleOpen(false)}>Cancel</Button>
          <Button
            variant="contained"
            onClick={() => createDongleMutation.mutate(pendingDongleId)}
            disabled={createDongleMutation.isPending}
          >
            Create
          </Button>
        </DialogActions>
      </Dialog>
    </>
  )
}
