import { useMutation } from '@tanstack/react-query'
import {
  Alert,
  Box,
  Button,
  FormControl,
  FormControlLabel,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Stack,
  Switch,
  Tab,
  Tabs,
  TextField,
  Typography,
} from '@mui/material'
import { useSnackbar } from 'notistack'
import { useState } from 'react'
import { importApi, type ImportKind } from '../api'
import type { ImportResult } from '../types'
import { PageHeader } from '../components/PageHelpers'

const kinds: { value: ImportKind; label: string; example: string; columns: string }[] = [
  {
    value: 'pcs',
    label: 'PCs',
    columns: 'name',
    example: 'name\nTEST-PC-01\nTEST-PC-02',
  },
  {
    value: 'dongles',
    label: 'Dongles',
    columns: 'dongle_id',
    example: 'dongle_id\nDNG-1001\nDNG-1002',
  },
  {
    value: 'categories',
    label: 'Categories',
    columns: 'name',
    example: 'name\nFull Inspection\nBasic Safety',
  },
  {
    value: 'test-modules',
    label: 'Test modules',
    columns: 'name',
    example: 'name\nBrake Test\nEmissions Check',
  },
]

export function ImportPage() {
  const { enqueueSnackbar } = useSnackbar()
  const [kind, setKind] = useState<ImportKind>('pcs')
  const [tab, setTab] = useState(0)
  const [text, setText] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [previewOnly, setPreviewOnly] = useState(true)
  const [result, setResult] = useState<ImportResult | null>(null)

  const current = kinds.find((k) => k.value === kind)!

  const mutation = useMutation({
    mutationFn: async () => {
      if (tab === 0) {
        if (!file) throw new Error('Choose a CSV file first')
        return importApi.upload(kind, file, previewOnly)
      }
      if (!text.trim()) throw new Error('Paste import text first')
      return importApi.text(kind, text, previewOnly)
    },
    onSuccess: (data) => {
      setResult(data)
      enqueueSnackbar(
        previewOnly
          ? `Preview: ${data.created} create, ${data.updated} update, ${data.skipped} skip`
          : `Imported: ${data.created} created, ${data.updated} updated, ${data.skipped} skipped`,
        { variant: data.errors.length ? 'warning' : 'success' },
      )
    },
    onError: (err: Error) => enqueueSnackbar(err.message, { variant: 'error' }),
  })

  return (
    <>
      <PageHeader
        title="Import"
        subtitle="Upsert PCs, dongles, categories, or test modules from CSV or pasted text. Matching is case-insensitive; names are trimmed."
      />

      <Stack spacing={2} maxWidth={900}>
        <Paper sx={{ p: 2 }}>
          <Stack spacing={2}>
            <FormControl sx={{ maxWidth: 280 }}>
              <InputLabel>Data type</InputLabel>
              <Select
                label="Data type"
                value={kind}
                onChange={(e) => {
                  setKind(e.target.value as ImportKind)
                  setResult(null)
                }}
              >
                {kinds.map((k) => (
                  <MenuItem key={k.value} value={k.value}>
                    {k.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            <Alert severity="info">
              Required column: <strong>{current.columns}</strong>. Header row is optional. Duplicate names in
              the same file are skipped. Existing records are updated rather than duplicated.
            </Alert>

            <Box
              component="pre"
              sx={{
                m: 0,
                p: 1.5,
                bgcolor: '#EEF2F6',
                borderRadius: 1,
                fontFamily: '"IBM Plex Mono", monospace',
                fontSize: 13,
                overflow: 'auto',
              }}
            >
              {current.example}
            </Box>

            <Tabs value={tab} onChange={(_, v) => setTab(v)}>
              <Tab label="CSV upload" />
              <Tab label="Paste text" />
            </Tabs>

            {tab === 0 ? (
              <Button variant="outlined" component="label">
                {file ? file.name : 'Choose CSV file'}
                <input
                  hidden
                  type="file"
                  accept=".csv,text/csv,text/plain"
                  onChange={(e) => setFile(e.target.files?.[0] || null)}
                />
              </Button>
            ) : (
              <TextField
                label="One value per line (or CSV text)"
                multiline
                minRows={8}
                value={text}
                onChange={(e) => setText(e.target.value)}
                fullWidth
              />
            )}

            <FormControlLabel
              control={
                <Switch checked={previewOnly} onChange={(_, v) => setPreviewOnly(v)} />
              }
              label="Preview only (do not save)"
            />

            <Box>
              <Button
                variant="contained"
                onClick={() => mutation.mutate()}
                disabled={mutation.isPending}
              >
                {previewOnly ? 'Preview import' : 'Run import'}
              </Button>
            </Box>
          </Stack>
        </Paper>

        {result && (
          <Paper sx={{ p: 2 }}>
            <Typography fontWeight={700} mb={1}>
              Result
            </Typography>
            <Typography>
              Created: {result.created} · Updated: {result.updated} · Skipped: {result.skipped} · Errors:{' '}
              {result.errors.length}
            </Typography>
            {result.errors.length > 0 && (
              <Box mt={1}>
                {result.errors.map((err, i) => (
                  <Typography key={i} color="error">
                    Row {err.row}: {err.message}
                    {err.value ? ` (${err.value})` : ''}
                  </Typography>
                ))}
              </Box>
            )}
          </Paper>
        )}
      </Stack>
    </>
  )
}
