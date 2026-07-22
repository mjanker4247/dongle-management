import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Paper,
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
import { useForm } from 'react-hook-form'
import { z } from 'zod'
import { zodResolver } from '@hookform/resolvers/zod'
import { locationsApi } from '../api'
import { ConfirmDialog, EmptyState, ErrorState, LoadingState, PageHeader } from '../components/PageHelpers'

const schema = z.object({
  name: z.string().trim().min(1, 'Name is required'),
  description: z.string().optional(),
})

type FormValues = z.infer<typeof schema>

export function LocationsPage() {
  const { enqueueSnackbar } = useSnackbar()
  const qc = useQueryClient()
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['locations'],
    queryFn: locationsApi.list,
  })
  const [open, setOpen] = useState(false)
  const [editId, setEditId] = useState<number | null>(null)
  const [deleteId, setDeleteId] = useState<number | null>(null)

  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { name: '', description: '' },
  })

  const saveMutation = useMutation({
    mutationFn: async (values: FormValues) => {
      if (editId) return locationsApi.update(editId, values)
      return locationsApi.create(values)
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['locations'] })
      enqueueSnackbar(editId ? 'Location updated' : 'Location created', { variant: 'success' })
      setOpen(false)
    },
    onError: (err: Error) => enqueueSnackbar(err.message, { variant: 'error' }),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => locationsApi.remove(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['locations'] })
      enqueueSnackbar('Location deleted', { variant: 'success' })
      setDeleteId(null)
    },
    onError: (err: Error) => enqueueSnackbar(err.message, { variant: 'error' }),
  })

  const openCreate = () => {
    setEditId(null)
    form.reset({ name: '', description: '' })
    setOpen(true)
  }

  const openEdit = (id: number) => {
    const loc = data?.find((l) => l.id === id)
    if (!loc) return
    setEditId(id)
    form.reset({ name: loc.name, description: loc.description ?? '' })
    setOpen(true)
  }

  return (
    <>
      <PageHeader
        title="Locations"
        subtitle="Rooms and places where PCs are installed"
        actions={
          <Button variant="contained" onClick={openCreate}>
            Add location
          </Button>
        }
      />
      {isLoading && <LoadingState />}
      {error && <ErrorState message={(error as Error).message} onRetry={() => refetch()} />}
      {data && data.length === 0 && <EmptyState message="No locations yet." />}
      {data && data.length > 0 && (
        <TableContainer component={Paper}>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Name</TableCell>
                <TableCell>Description</TableCell>
                <TableCell align="right">PCs</TableCell>
                <TableCell align="right">Dongles</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {data.map((loc) => (
                <TableRow key={loc.id} hover>
                  <TableCell>
                    <Typography fontWeight={600}>{loc.name}</Typography>
                  </TableCell>
                  <TableCell>{loc.description || '—'}</TableCell>
                  <TableCell align="right">{loc.pc_count ?? 0}</TableCell>
                  <TableCell align="right">{loc.dongle_count ?? 0}</TableCell>
                  <TableCell align="right">
                    <Button size="small" onClick={() => openEdit(loc.id)}>
                      Edit
                    </Button>
                    <Button size="small" color="error" onClick={() => setDeleteId(loc.id)}>
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
        <DialogTitle>{editId ? 'Edit location' : 'Add location'}</DialogTitle>
        <form onSubmit={form.handleSubmit((v) => saveMutation.mutate(v))}>
          <DialogContent>
            <Stack spacing={2} mt={1}>
              <TextField
                label="Name"
                fullWidth
                {...form.register('name')}
                error={!!form.formState.errors.name}
                helperText={form.formState.errors.name?.message}
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
        title="Delete location"
        message="PCs in this location will be unassigned. Continue?"
        onClose={() => setDeleteId(null)}
        onConfirm={() => deleteId && deleteMutation.mutate(deleteId)}
        loading={deleteMutation.isPending}
      />
    </>
  )
}
