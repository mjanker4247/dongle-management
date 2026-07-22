import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Box,
  Button,
  Checkbox,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControlLabel,
  FormGroup,
  Paper,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  ToggleButton,
  ToggleButtonGroup,
  Typography,
} from '@mui/material'
import { useSnackbar } from 'notistack'
import { useEffect, useMemo, useState } from 'react'
import { useForm } from 'react-hook-form'
import { z } from 'zod'
import { zodResolver } from '@hookform/resolvers/zod'
import { categoriesApi, testModulesApi } from '../api'
import { ConfirmDialog, EmptyState, ErrorState, LoadingState, PageHeader } from '../components/PageHelpers'

const schema = z.object({
  name: z.string().trim().min(1, 'Name is required'),
  description: z.string().optional(),
})

type FormValues = z.infer<typeof schema>

export function CategoriesPage() {
  const { enqueueSnackbar } = useSnackbar()
  const qc = useQueryClient()
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['categories'],
    queryFn: categoriesApi.list,
  })
  const modulesQuery = useQuery({
    queryKey: ['test-modules', 'manual'],
    queryFn: () => testModulesApi.list({ order: 'manual' }),
  })
  const [open, setOpen] = useState(false)
  const [editId, setEditId] = useState<number | null>(null)
  const [deleteId, setDeleteId] = useState<number | null>(null)
  const [detailId, setDetailId] = useState<number | null>(null)
  const [alphabetical, setAlphabetical] = useState(false)
  const [selectedModuleIds, setSelectedModuleIds] = useState<number[]>([])

  const detailQuery = useQuery({
    queryKey: ['categories', detailId, alphabetical],
    queryFn: () => categoriesApi.get(detailId!, alphabetical),
    enabled: detailId !== null,
  })

  useEffect(() => {
    if (detailQuery.data?.modules) {
      setSelectedModuleIds(detailQuery.data.modules.map((m) => m.id))
    }
  }, [detailQuery.data])

  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { name: '', description: '' },
  })

  const saveMutation = useMutation({
    mutationFn: async (values: FormValues) => {
      if (editId) return categoriesApi.update(editId, values)
      return categoriesApi.create(values)
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['categories'] })
      enqueueSnackbar(editId ? 'Category updated' : 'Category created', { variant: 'success' })
      setOpen(false)
    },
    onError: (err: Error) => enqueueSnackbar(err.message, { variant: 'error' }),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => categoriesApi.remove(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['categories'] })
      enqueueSnackbar('Category deleted', { variant: 'success' })
      setDeleteId(null)
    },
    onError: (err: Error) => enqueueSnackbar(err.message, { variant: 'error' }),
  })

  const modulesMutation = useMutation({
    mutationFn: () => categoriesApi.setModules(detailId!, selectedModuleIds),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['categories'] })
      enqueueSnackbar('Category modules updated', { variant: 'success' })
    },
    onError: (err: Error) => enqueueSnackbar(err.message, { variant: 'error' }),
  })

  const sortedModules = useMemo(() => {
    const mods = modulesQuery.data || []
    if (alphabetical) return [...mods].sort((a, b) => a.name.localeCompare(b.name))
    return [...mods].sort((a, b) => a.sort_index - b.sort_index || a.name.localeCompare(b.name))
  }, [modulesQuery.data, alphabetical])

  return (
    <>
      <PageHeader
        title="Categories"
        subtitle="Groups of test modules used for completeness checks"
        actions={
          <Button
            variant="contained"
            onClick={() => {
              setEditId(null)
              form.reset({ name: '', description: '' })
              setOpen(true)
            }}
          >
            Add category
          </Button>
        }
      />
      {isLoading && <LoadingState />}
      {error && <ErrorState message={(error as Error).message} onRetry={() => refetch()} />}
      {data && data.length === 0 && <EmptyState message="No categories yet." />}
      {data && data.length > 0 && (
        <TableContainer component={Paper}>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Name</TableCell>
                <TableCell>Description</TableCell>
                <TableCell align="right">Modules</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {data.map((cat) => (
                <TableRow key={cat.id} hover>
                  <TableCell>
                    <Typography fontWeight={600}>{cat.name}</Typography>
                  </TableCell>
                  <TableCell>{cat.description || '—'}</TableCell>
                  <TableCell align="right">{cat.module_count}</TableCell>
                  <TableCell align="right">
                    <Button size="small" onClick={() => setDetailId(cat.id)}>
                      Modules
                    </Button>
                    <Button
                      size="small"
                      onClick={() => {
                        setEditId(cat.id)
                        form.reset({ name: cat.name, description: cat.description ?? '' })
                        setOpen(true)
                      }}
                    >
                      Edit
                    </Button>
                    <Button size="small" color="error" onClick={() => setDeleteId(cat.id)}>
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
        <DialogTitle>{editId ? 'Edit category' : 'Add category'}</DialogTitle>
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

      <Dialog open={detailId !== null} onClose={() => setDetailId(null)} maxWidth="md" fullWidth>
        <DialogTitle>Assign modules — {detailQuery.data?.name}</DialogTitle>
        <DialogContent>
          <Box sx={{ mb: 2 }}>
            <ToggleButtonGroup
              exclusive
              size="small"
              value={alphabetical ? 'alpha' : 'manual'}
              onChange={(_, v) => v && setAlphabetical(v === 'alpha')}
            >
              <ToggleButton value="manual">Manual order</ToggleButton>
              <ToggleButton value="alpha">Alphabetical</ToggleButton>
            </ToggleButtonGroup>
          </Box>
          <FormGroup>
            {sortedModules.map((m) => (
              <FormControlLabel
                key={m.id}
                control={
                  <Checkbox
                    checked={selectedModuleIds.includes(m.id)}
                    onChange={(e) => {
                      setSelectedModuleIds((prev) =>
                        e.target.checked ? [...prev, m.id] : prev.filter((id) => id !== m.id),
                      )
                    }}
                  />
                }
                label={`${m.name}${m.is_active ? '' : ' (inactive)'}`}
              />
            ))}
          </FormGroup>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDetailId(null)}>Close</Button>
          <Button
            variant="contained"
            onClick={() => modulesMutation.mutate()}
            disabled={modulesMutation.isPending}
          >
            Save modules
          </Button>
        </DialogActions>
      </Dialog>

      <ConfirmDialog
        open={deleteId !== null}
        title="Delete category"
        message="Test modules themselves will not be deleted. Continue?"
        onClose={() => setDeleteId(null)}
        onConfirm={() => deleteId && deleteMutation.mutate(deleteId)}
        loading={deleteMutation.isPending}
      />
    </>
  )
}
