import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Button,
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
import { useState } from 'react'
import { useForm, Controller } from 'react-hook-form'
import { z } from 'zod'
import { zodResolver } from '@hookform/resolvers/zod'
import { locationsApi, pcsApi } from '../api'
import { ConfirmDialog, EmptyState, ErrorState, LoadingState, PageHeader } from '../components/PageHelpers'

const schema = z.object({
  name: z.string().trim().min(1, 'Name is required'),
  location_id: z.union([z.number(), z.literal('')]).optional(),
  description: z.string().optional(),
})

type FormValues = z.infer<typeof schema>

export function PCsPage() {
  const { enqueueSnackbar } = useSnackbar()
  const qc = useQueryClient()
  const pcsQuery = useQuery({ queryKey: ['pcs'], queryFn: pcsApi.list })
  const locationsQuery = useQuery({ queryKey: ['locations'], queryFn: locationsApi.list })
  const [open, setOpen] = useState(false)
  const [editId, setEditId] = useState<number | null>(null)
  const [deleteId, setDeleteId] = useState<number | null>(null)
  const [detailId, setDetailId] = useState<number | null>(null)

  const detailQuery = useQuery({
    queryKey: ['pcs', detailId],
    queryFn: () => pcsApi.get(detailId!),
    enabled: detailId !== null,
  })

  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { name: '', location_id: '', description: '' },
  })

  const saveMutation = useMutation({
    mutationFn: async (values: FormValues) => {
      const payload = {
        name: values.name,
        description: values.description,
        location_id: values.location_id === '' || values.location_id === undefined ? null : Number(values.location_id),
      }
      if (editId) return pcsApi.update(editId, payload)
      return pcsApi.create(payload)
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['pcs'] })
      qc.invalidateQueries({ queryKey: ['locations'] })
      enqueueSnackbar(editId ? 'PC updated' : 'PC created', { variant: 'success' })
      setOpen(false)
    },
    onError: (err: Error) => enqueueSnackbar(err.message, { variant: 'error' }),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => pcsApi.remove(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['pcs'] })
      enqueueSnackbar('PC deleted', { variant: 'success' })
      setDeleteId(null)
    },
    onError: (err: Error) => enqueueSnackbar(err.message, { variant: 'error' }),
  })

  const openCreate = () => {
    setEditId(null)
    form.reset({ name: '', location_id: '', description: '' })
    setOpen(true)
  }

  const openEdit = (id: number) => {
    const pc = pcsQuery.data?.find((p) => p.id === id)
    if (!pc) return
    setEditId(id)
    form.reset({
      name: pc.name,
      location_id: pc.location_id ?? '',
      description: pc.description ?? '',
    })
    setOpen(true)
  }

  return (
    <>
      <PageHeader
        title="PCs"
        subtitle="Computers where dongles are installed"
        actions={
          <Button variant="contained" onClick={openCreate}>
            Add PC
          </Button>
        }
      />
      {pcsQuery.isLoading && <LoadingState />}
      {pcsQuery.error && (
        <ErrorState message={(pcsQuery.error as Error).message} onRetry={() => pcsQuery.refetch()} />
      )}
      {pcsQuery.data && pcsQuery.data.length === 0 && <EmptyState message="No PCs yet." />}
      {pcsQuery.data && pcsQuery.data.length > 0 && (
        <TableContainer component={Paper}>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>PC name</TableCell>
                <TableCell>Location</TableCell>
                <TableCell align="right">Dongles</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {pcsQuery.data.map((pc) => (
                <TableRow key={pc.id} hover>
                  <TableCell>
                    <Typography fontWeight={600}>{pc.name}</Typography>
                  </TableCell>
                  <TableCell>{pc.location?.name || '—'}</TableCell>
                  <TableCell align="right">{pc.dongle_count}</TableCell>
                  <TableCell align="right">
                    <Button size="small" onClick={() => setDetailId(pc.id)}>
                      View
                    </Button>
                    <Button size="small" onClick={() => openEdit(pc.id)}>
                      Edit
                    </Button>
                    <Button size="small" color="error" onClick={() => setDeleteId(pc.id)}>
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
        <DialogTitle>{editId ? 'Edit PC' : 'Add PC'}</DialogTitle>
        <form onSubmit={form.handleSubmit((v) => saveMutation.mutate(v))}>
          <DialogContent>
            <Stack spacing={2} mt={1}>
              <TextField
                label="PC name"
                fullWidth
                {...form.register('name')}
                error={!!form.formState.errors.name}
                helperText={form.formState.errors.name?.message}
              />
              <Controller
                name="location_id"
                control={form.control}
                render={({ field }) => (
                  <FormControl fullWidth>
                    <InputLabel>Location</InputLabel>
                    <Select
                      label="Location"
                      value={field.value === undefined || field.value === null ? '' : field.value}
                      onChange={(e) =>
                        field.onChange(e.target.value === '' ? '' : Number(e.target.value))
                      }
                    >
                      <MenuItem value="">None</MenuItem>
                      {(locationsQuery.data || []).map((loc) => (
                        <MenuItem key={loc.id} value={loc.id}>
                          {loc.name}
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

      <Dialog open={detailId !== null} onClose={() => setDetailId(null)} maxWidth="sm" fullWidth>
        <DialogTitle>PC details</DialogTitle>
        <DialogContent>
          {detailQuery.data && (
            <Stack spacing={1} mt={1}>
              <Typography>
                <strong>Name:</strong> {detailQuery.data.name}
              </Typography>
              <Typography>
                <strong>Location:</strong> {detailQuery.data.location?.name || '—'}
              </Typography>
              <Typography fontWeight={600} mt={1}>
                Installed dongles
              </Typography>
              {(detailQuery.data.dongles || []).length === 0 && (
                <Typography color="text.secondary">No dongles assigned.</Typography>
              )}
              {(detailQuery.data.dongles || []).map((d) => (
                <Typography key={d.id} fontFamily='"IBM Plex Mono", monospace'>
                  {d.dongle_id}
                </Typography>
              ))}
            </Stack>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDetailId(null)}>Close</Button>
        </DialogActions>
      </Dialog>

      <ConfirmDialog
        open={deleteId !== null}
        title="Delete PC"
        message="Dongles assigned to this PC will be unassigned. Continue?"
        onClose={() => setDeleteId(null)}
        onConfirm={() => deleteId && deleteMutation.mutate(deleteId)}
        loading={deleteMutation.isPending}
      />
    </>
  )
}
