import { useQuery } from '@tanstack/react-query'
import {
  Box,
  Button,
  Paper,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material'
import { Link as RouterLink } from 'react-router-dom'
import { dashboardApi } from '../api'
import { ErrorState, LoadingState, PageHeader } from '../components/PageHelpers'

function StatCard({ label, value, to }: { label: string; value: number; to: string }) {
  return (
    <Paper
      component={RouterLink}
      to={to}
      sx={{
        p: 2.5,
        textDecoration: 'none',
        color: 'inherit',
        display: 'block',
        flex: '1 1 160px',
        minWidth: 140,
        background: 'linear-gradient(180deg, #FFFFFF 0%, #F7F9FC 100%)',
        transition: 'border-color 0.15s ease, transform 0.15s ease',
        '&:hover': { borderColor: 'primary.main', transform: 'translateY(-1px)' },
      }}
    >
      <Typography variant="body2" color="text.secondary">
        {label}
      </Typography>
      <Typography variant="h4" color="primary" mt={0.5}>
        {value}
      </Typography>
    </Paper>
  )
}

export function DashboardPage() {
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['dashboard'],
    queryFn: dashboardApi.get,
  })

  if (isLoading) return <LoadingState />
  if (error) return <ErrorState message={(error as Error).message} onRetry={() => refetch()} />
  if (!data) return null

  return (
    <>
      <PageHeader
        title="Dashboard"
        subtitle="Overview of dongles, PCs, and test module inventory"
        actions={
          <Button component={RouterLink} to="/quick-entry" variant="contained">
            Quick Dongle Entry
          </Button>
        }
      />

      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, mb: 3 }}>
        <StatCard label="Dongles" value={data.dongle_count} to="/dongles" />
        <StatCard label="PCs" value={data.pc_count} to="/pcs" />
        <StatCard label="Locations" value={data.location_count} to="/locations" />
        <StatCard label="Categories" value={data.category_count} to="/categories" />
        <StatCard label="Test modules" value={data.test_module_count} to="/test-modules" />
      </Box>

      <Stack spacing={2}>
        <Paper sx={{ p: 2 }}>
          <Typography fontWeight={700} mb={1.5}>
            Dongles without PC assignment
          </Typography>
          {data.unassigned_dongles.length === 0 ? (
            <Typography color="text.secondary">All dongles are assigned.</Typography>
          ) : (
            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Dongle ID</TableCell>
                    <TableCell align="right">Enabled modules</TableCell>
                    <TableCell align="right">Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {data.unassigned_dongles.map((d) => (
                    <TableRow key={d.id}>
                      <TableCell>
                        <Typography fontFamily='"IBM Plex Mono", monospace'>{d.dongle_id}</Typography>
                      </TableCell>
                      <TableCell align="right">{d.enabled_module_count}</TableCell>
                      <TableCell align="right">
                        <Button size="small" component={RouterLink} to={`/dongles/${d.id}`}>
                          Open
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </Paper>

        <Paper sx={{ p: 2 }}>
          <Typography fontWeight={700} mb={1.5}>
            Recently changed dongles
          </Typography>
          <TableContainer>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Dongle ID</TableCell>
                  <TableCell>PC</TableCell>
                  <TableCell>Updated</TableCell>
                  <TableCell align="right">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {data.recently_changed_dongles.map((d) => (
                  <TableRow key={d.id}>
                    <TableCell>
                      <Typography fontFamily='"IBM Plex Mono", monospace'>{d.dongle_id}</Typography>
                    </TableCell>
                    <TableCell>{d.pc?.name || '—'}</TableCell>
                    <TableCell>{new Date(d.updated_at).toLocaleString()}</TableCell>
                    <TableCell align="right">
                      <Button size="small" component={RouterLink} to={`/dongles/${d.id}`}>
                        Open
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      </Stack>
    </>
  )
}
