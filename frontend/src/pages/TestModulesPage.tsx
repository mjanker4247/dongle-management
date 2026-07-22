import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Box,
  Button,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControl,
  FormControlLabel,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Stack,
  Switch,
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
import ArrowUpwardIcon from '@mui/icons-material/ArrowUpward'
import ArrowDownwardIcon from '@mui/icons-material/ArrowDownward'
import { useSnackbar } from 'notistack'
import { useState } from 'react'
import { useForm, Controller } from 'react-hook-form'
import { z } from 'zod'
import { zodResolver } from '@hookform/resolvers/zod'
import { categoriesApi, testModulesApi } from '../api'
import { ConfirmDialog, EmptyState, ErrorState, LoadingState, PageHeader } from '../components/PageHelpers'

const schema = z.object({
  name: z.string().trim().min(1, 'Name is required'),
  description: z.string().optional(),
  sort_index: z.number().int().optional().or(z.nan().transform(() => undefined)),
  is_active: z.boolean(),
})

type FormValues = {
  name: string
  description?: string
  sort_index?: number
  is_active: boolean
}

export function TestModulesPage() {
  const { enqueueSnackbar } = useSnackbar()
  const qc = useQueryClient()
  const [search, setSearch] = useState('')
  const [categoryId, setCategoryId] = useState<number | ''>('')
  const [status, setStatus] = useState<'all' | 'active' | 'inactive'>('all')
  const [order, setOrder] = useState<'manual' | 'alpha'>('manual')

  const query = useQuery({
    queryKey: ['test-modules', search, categoryId, status, order],
    queryFn: () =>
      testModulesApi.list({
        search: search || undefined,
        category_id: categoryId === '' ? undefined : categoryId,
        is_active: status === 'all' ? undefined : status === 'active',
        order,
      }),
  })
  const categoriesQuery = useQuery({ queryKey: ['categories'], queryFn: categoriesApi.list })

  const [open, setOpen] = useState(false)
  const [editId, setEditId] = useState<number | null>(null)
  const [deleteId, setDeleteId] = useState<number | null>(null)

  const form = useForm<FormValues>({
    resolver: zodResolver(schema) as never,
    defaultValues: { name: '', description: '', sort_index: undefined, is_active: true },
  })

  const saveMutation = useMutation({
    mutationFn: async (values: FormValues) => {
      const payload = {
        name: values.name,
        description: values.description,
        is_active: values.is_active,
        sort_index:
          values.sort_index === undefined || Number.isNaN(values.sort_index)
            ? undefined
            : Number(values.sort_index),
      }
      if (editId) return testModulesApi.update(editId, payload)
      return testModulesApi.create(payload)
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['test-modules'] })
      enqueueSnackbar(editId ? 'Module updated' : 'Module created', { variant: 'success' })
      setOpen(false)
    },
    onError: (err: Error) => enqueueSnackbar(err.message, { variant: 'error' }),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => testModulesApi.remove(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['test-modules'] })
      enqueueSnackbar('Module deleted', { variant: 'success' })
      setDeleteId(null)
    },
    onError: (err: Error) => enqueueSnackbar(err.message, { variant: 'error' }),
  })

  const reorderMutation = useMutation({
    mutationFn: (items: { id: number; sort_index: number }[]) => testModulesApi.reorder(items),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['test-modules'] })
      enqueueSnackbar('Order saved', { variant: 'success' })
    },
    onError: (err: Error) => enqueueSnackbar(err.message, { variant: 'error' }),
  })

  const modules = query.data || []

  const move = (index: number, direction: -1 | 1) => {
    const target = index + direction
    if (target < 0 || target >= modules.length) return
    const next = [...modules]
    const tmp = next[index]
    next[index] = next[target]
    next[target] = tmp
    const items = next.map((m, i) => ({ id: m.id, sort_index: (i + 1) * 10 }))
    reorderMutation.mutate(items)
  }

  return (
    <>
      <PageHeader
        title="Test Modules"
        subtitle="Modules activated by dongles — manual order matches external software UI"
        actions={
          <Button
            variant="contained"
            onClick={() => {
              setEditId(null)
              form.reset({ name: '', description: '', sort_index: undefined, is_active: true })
              setOpen(true)
            }}
          >
            Add module
          </Button>
        }
      />

      <Stack direction={{ xs: 'column', md: 'row' }} spacing={1.5} mb={2} alignItems={{ md: 'center' }}>
        <TextField
          size="small"
          placeholder="Search by name or category"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          sx={{ minWidth: 240 }}
        />
        <FormControl size="small" sx={{ minWidth: 180 }}>
          <InputLabel>Category</InputLabel>
          <Select
            label="Category"
            value={categoryId}
            onChange={(e) => setCategoryId(e.target.value === '' ? '' : Number(e.target.value))}
          >
            <MenuItem value="">All</MenuItem>
            {(categoriesQuery.data || []).map((c) => (
              <MenuItem key={c.id} value={c.id}>
                {c.name}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
        <FormControl size="small" sx={{ minWidth: 140 }}>
          <InputLabel>Status</InputLabel>
          <Select
            label="Status"
            value={status}
            onChange={(e) => setStatus(e.target.value as typeof status)}
          >
            <MenuItem value="all">All</MenuItem>
            <MenuItem value="active">Active</MenuItem>
            <MenuItem value="inactive">Inactive</MenuItem>
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

      {query.isLoading && <LoadingState />}
      {query.error && (
        <ErrorState message={(query.error as Error).message} onRetry={() => query.refetch()} />
      )}
      {query.data && query.data.length === 0 && <EmptyState message="No test modules found." />}
      {query.data && query.data.length > 0 && (
        <TableContainer component={Paper}>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Module name</TableCell>
                <TableCell>Active</TableCell>
                <TableCell align="right">Sort</TableCell>
                <TableCell>Categories</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {modules.map((m, index) => (
                <TableRow key={m.id} hover>
                  <TableCell>
                    <Typography fontWeight={600}>{m.name}</Typography>
                  </TableCell>
                  <TableCell>
                    <Chip
                      size="small"
                      label={m.is_active ? 'Active' : 'Inactive'}
                      color={m.is_active ? 'success' : 'default'}
                      variant="outlined"
                    />
                  </TableCell>
                  <TableCell align="right">
                    <Stack direction="row" spacing={0.5} justifyContent="flex-end" alignItems="center">
                      <Typography fontFamily='"IBM Plex Mono", monospace'>{m.sort_index}</Typography>
                      {order === 'manual' && (
                        <>
                          <Button size="small" onClick={() => move(index, -1)} disabled={index === 0}>
                            <ArrowUpwardIcon fontSize="small" />
                          </Button>
                          <Button
                            size="small"
                            onClick={() => move(index, 1)}
                            disabled={index === modules.length - 1}
                          >
                            <ArrowDownwardIcon fontSize="small" />
                          </Button>
                        </>
                      )}
                    </Stack>
                  </TableCell>
                  <TableCell>
                    <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                      {m.categories.map((c) => (
                        <Chip key={c.id} size="small" label={c.name} />
                      ))}
                    </Box>
                  </TableCell>
                  <TableCell align="right">
                    <Button
                      size="small"
                      onClick={() => {
                        setEditId(m.id)
                        form.reset({
                          name: m.name,
                          description: m.description ?? '',
                          sort_index: m.sort_index,
                          is_active: m.is_active,
                        })
                        setOpen(true)
                      }}
                    >
                      Edit
                    </Button>
                    <Button size="small" color="error" onClick={() => setDeleteId(m.id)}>
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
        <DialogTitle>{editId ? 'Edit module' : 'Add module'}</DialogTitle>
        <form onSubmit={form.handleSubmit((v) => saveMutation.mutate(v))}>
          <DialogContent>
            <Stack spacing={2} mt={1}>
              <TextField
                label="Module name"
                fullWidth
                {...form.register('name')}
                error={!!form.formState.errors.name}
                helperText={form.formState.errors.name?.message}
              />
              <TextField label="Description" fullWidth multiline minRows={2} {...form.register('description')} />
              <TextField
                label="Sort index"
                type="number"
                fullWidth
                value={form.watch('sort_index') ?? ''}
                onChange={(e) => {
                  const v = e.target.value
                  form.setValue('sort_index', v === '' ? undefined : Number(v), {
                    shouldDirty: true,
                  })
                }}
                helperText="Lower values appear first in manual order"
              />
              <Controller
                name="is_active"
                control={form.control}
                render={({ field }) => (
                  <FormControlLabel
                    control={<Switch checked={field.value} onChange={(_, v) => field.onChange(v)} />}
                    label="Active"
                  />
                )}
              />
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
        title="Delete test module"
        message="This removes the module from categories and dongles. Continue?"
        onClose={() => setDeleteId(null)}
        onConfirm={() => deleteId && deleteMutation.mutate(deleteId)}
        loading={deleteMutation.isPending}
      />
    </>
  )
}
