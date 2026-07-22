import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Alert,
  Box,
  Button,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControl,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from '@mui/material'
import { useSnackbar } from 'notistack'
import { useMemo, useState } from 'react'
import { Link as RouterLink, useNavigate, useParams } from 'react-router-dom'
import { useForm, Controller } from 'react-hook-form'
import { z } from 'zod'
import { zodResolver } from '@hookform/resolvers/zod'
import { categoriesApi, donglesApi, pcsApi } from '../api'
import { ConfirmDialog, EmptyState, ErrorState, LoadingState, PageHeader } from '../components/PageHelpers'

const schema = z.object({
  dongle_id: z.string().trim().min(1, 'Dongle ID is required'),
  pc_id: z.union([z.number(), z.literal('')]).optional(),
  description: z.string().optional(),
})

type FormValues = z.infer<typeof schema>

export function DonglesPage() {
  const { enqueueSnackbar } = useSnackbar()
  const navigate = useNavigate()
  const qc = useQueryClient()
  const [search, setSearch] = useState('')
  const donglesQuery = useQuery({
    queryKey: ['dongles', search],
    queryFn: () => donglesApi.list(search || undefined),
  })
  const pcsQuery = useQuery({ queryKey: ['pcs'], queryFn: pcsApi.list })
  const [open, setOpen] = useState(false)
  const [editId, setEditId] = useState<number | null>(null)
  const [deleteId, setDeleteId] = useState<number | null>(null)

  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { dongle_id: '', pc_id: '', description: '' },
  })

  const saveMutation = useMutation({
    mutationFn: async (values: FormValues) => {
      const payload = {
        dongle_id: values.dongle_id,
        description: values.description,
        pc_id: values.pc_id === '' || values.pc_id === undefined ? null : Number(values.pc_id),
      }
      if (editId) return donglesApi.update(editId, payload)
      return donglesApi.create(payload)
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['dongles'] })
      enqueueSnackbar(editId ? 'Dongle updated' : 'Dongle created', { variant: 'success' })
      setOpen(false)
    },
    onError: (err: Error) => enqueueSnackbar(err.message, { variant: 'error' }),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => donglesApi.remove(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['dongles'] })
      enqueueSnackbar('Dongle deleted', { variant: 'success' })
      setDeleteId(null)
    },
    onError: (err: Error) => enqueueSnackbar(err.message, { variant: 'error' }),
  })

  return (
    <>
      <PageHeader
        title="Dongles"
        subtitle="Physical software dongles and their PC assignments"
        actions={
          <Button
            variant="contained"
            onClick={() => {
              setEditId(null)
              form.reset({ dongle_id: '', pc_id: '', description: '' })
              setOpen(true)
            }}
          >
            Add dongle
          </Button>
        }
      />
      <TextField
        size="small"
        placeholder="Filter by dongle ID, PC, or location"
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        sx={{ mb: 2, maxWidth: 420, width: '100%' }}
      />
      {donglesQuery.isLoading && <LoadingState />}
      {donglesQuery.error && (
        <ErrorState
          message={(donglesQuery.error as Error).message}
          onRetry={() => donglesQuery.refetch()}
        />
      )}
      {donglesQuery.data && donglesQuery.data.length === 0 && (
        <EmptyState message="No dongles found." />
      )}
      {donglesQuery.data && donglesQuery.data.length > 0 && (
        <TableContainer component={Paper}>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Dongle ID</TableCell>
                <TableCell>Assigned PC</TableCell>
                <TableCell>Location</TableCell>
                <TableCell align="right">Enabled modules</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {donglesQuery.data.map((d) => (
                <TableRow key={d.id} hover>
                  <TableCell>
                    <Typography fontFamily='"IBM Plex Mono", monospace' fontWeight={600}>
                      {d.dongle_id}
                    </Typography>
                  </TableCell>
                  <TableCell>{d.pc?.name || '—'}</TableCell>
                  <TableCell>{d.pc?.location?.name || '—'}</TableCell>
                  <TableCell align="right">{d.enabled_module_count}</TableCell>
                  <TableCell align="right">
                    <Button size="small" onClick={() => navigate(`/dongles/${d.id}`)}>
                      Open
                    </Button>
                    <Button
                      size="small"
                      onClick={() => {
                        setEditId(d.id)
                        form.reset({
                          dongle_id: d.dongle_id,
                          pc_id: d.pc_id ?? '',
                          description: d.description ?? '',
                        })
                        setOpen(true)
                      }}
                    >
                      Edit
                    </Button>
                    <Button size="small" color="error" onClick={() => setDeleteId(d.id)}>
                      Delete
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      <Dialog open={open} onClose={() => setOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{editId ? 'Edit dongle' : 'Add dongle'}</DialogTitle>
        <form onSubmit={form.handleSubmit((v) => saveMutation.mutate(v))}>
          <DialogContent>
            <Stack spacing={2} mt={1}>
              <TextField
                label="Dongle ID"
                fullWidth
                {...form.register('dongle_id')}
                error={!!form.formState.errors.dongle_id}
                helperText={form.formState.errors.dongle_id?.message}
              />
              <Controller
                name="pc_id"
                control={form.control}
                render={({ field }) => (
                  <FormControl fullWidth>
                    <InputLabel>Assigned PC</InputLabel>
                    <Select
                      label="Assigned PC"
                      value={field.value === undefined || field.value === null ? '' : field.value}
                      onChange={(e) =>
                        field.onChange(e.target.value === '' ? '' : Number(e.target.value))
                      }
                    >
                      <MenuItem value="">Unassigned</MenuItem>
                      {(pcsQuery.data || []).map((pc) => (
                        <MenuItem key={pc.id} value={pc.id}>
                          {pc.name}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                )}
              />
              <TextField label="Description" fullWidth multiline minRows={2} {...form.register('description')} />
            </Stack>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setOpen(false)}>Cancel</Button>
            <Button type="submit" variant="contained" disabled={saveMutation.isPending}>
              Save
            </Button>
          </DialogActions>
        </form>
      </Dialog>

      <ConfirmDialog
        open={deleteId !== null}
        title="Delete dongle"
        message="This will permanently delete the dongle and its module assignments."
        onClose={() => setDeleteId(null)}
        onConfirm={() => deleteId && deleteMutation.mutate(deleteId)}
        loading={deleteMutation.isPending}
      />
    </>
  )
}

export function DongleDetailPage() {
  const { id } = useParams()
  const dongleId = Number(id)
  const dongleQuery = useQuery({
    queryKey: ['dongles', dongleId],
    queryFn: () => donglesApi.get(dongleId),
    enabled: Number.isFinite(dongleId),
  })
  const categoriesQuery = useQuery({ queryKey: ['categories'], queryFn: categoriesApi.list })
  const [categoryId, setCategoryId] = useState<number | ''>('')

  const completenessQuery = useQuery({
    queryKey: ['completeness', dongleId, categoryId],
    queryFn: () => donglesApi.completeness(dongleId, { category_id: Number(categoryId) }),
    enabled: Number.isFinite(dongleId) && categoryId !== '',
  })

  const enabledModules = useMemo(
    () => (dongleQuery.data?.modules || []).filter((m) => m.enabled),
    [dongleQuery.data],
  )

  if (dongleQuery.isLoading) return <LoadingState />
  if (dongleQuery.error) {
    return <ErrorState message={(dongleQuery.error as Error).message} onRetry={() => dongleQuery.refetch()} />
  }
  if (!dongleQuery.data) return <EmptyState message="Dongle not found." />

  const d = dongleQuery.data

  return (
    <>
      <PageHeader
        title={d.dongle_id}
        subtitle="Dongle detail and category completeness"
        actions={
          <>
            <Button component={RouterLink} to="/dongles">
              Back
            </Button>
            <Button component={RouterLink} to="/quick-entry" variant="outlined">
              Quick entry
            </Button>
          </>
        }
      />
      <Stack spacing={2}>
        <Paper sx={{ p: 2 }}>
          <Stack spacing={1}>
            <Typography>
              <strong>PC:</strong> {d.pc?.name || 'Unassigned'}
            </Typography>
            <Typography>
              <strong>Location:</strong> {d.pc?.location?.name || '—'}
            </Typography>
            <Typography>
              <strong>Description:</strong> {d.description || '—'}
            </Typography>
            <Typography>
              <strong>Enabled modules:</strong> {d.enabled_module_count}
            </Typography>
          </Stack>
        </Paper>

        <Paper sx={{ p: 2 }}>
          <Typography fontWeight={600} mb={1}>
            Enabled test modules
          </Typography>
          {enabledModules.length === 0 ? (
            <Typography color="text.secondary">No modules enabled.</Typography>
          ) : (
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
              {enabledModules.map((m) => (
                <Chip key={m.test_module_id} label={m.test_module?.name || m.test_module_id} />
              ))}
            </Box>
          )}
        </Paper>

        <Paper sx={{ p: 2 }}>
          <Typography fontWeight={600} mb={2}>
            Completeness check
          </Typography>
          <FormControl sx={{ minWidth: 260, mb: 2 }}>
            <InputLabel>Category</InputLabel>
            <Select
              label="Category"
              value={categoryId}
              onChange={(e) => setCategoryId(e.target.value === '' ? '' : Number(e.target.value))}
            >
              <MenuItem value="">Select category</MenuItem>
              {(categoriesQuery.data || []).map((c) => (
                <MenuItem key={c.id} value={c.id}>
                  {c.name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          {completenessQuery.data && (
            <Stack spacing={1}>
              <Alert severity={completenessQuery.data.is_complete ? 'success' : 'warning'}>
                {completenessQuery.data.is_complete ? 'Complete' : 'Incomplete'} —{' '}
                {completenessQuery.data.enabled_required_modules}/
                {completenessQuery.data.total_required_modules} required modules enabled
              </Alert>
              {completenessQuery.data.missing_modules.length > 0 && (
                <Box>
                  <Typography fontWeight={600}>Missing modules</Typography>
                  {completenessQuery.data.missing_modules.map((m) => (
                    <Typography key={m.id}>• {m.name}</Typography>
                  ))}
                </Box>
              )}
              {completenessQuery.data.extra_enabled_modules.length > 0 && (
                <Box>
                  <Typography fontWeight={600}>Extra enabled (outside category)</Typography>
                  {completenessQuery.data.extra_enabled_modules.map((m) => (
                    <Typography key={m.id}>• {m.name}</Typography>
                  ))}
                </Box>
              )}
            </Stack>
          )}
        </Paper>
      </Stack>
    </>
  )
}
