import api from './client'
import type {
  Category,
  CompletenessResult,
  DashboardStats,
  Dongle,
  DongleModuleLink,
  ImportResult,
  Location,
  PC,
  TestModule,
} from '../types'

export const dashboardApi = {
  get: () => api.get<DashboardStats>('/dashboard').then((r) => r.data),
}

export const locationsApi = {
  list: () => api.get<Location[]>('/locations').then((r) => r.data),
  get: (id: number) => api.get<Location>(`/locations/${id}`).then((r) => r.data),
  create: (data: { name: string; description?: string }) =>
    api.post<Location>('/locations', data).then((r) => r.data),
  update: (id: number, data: Partial<{ name: string; description?: string | null }>) =>
    api.put<Location>(`/locations/${id}`, data).then((r) => r.data),
  remove: (id: number) => api.delete(`/locations/${id}`),
}

export const pcsApi = {
  list: () => api.get<PC[]>('/pcs').then((r) => r.data),
  get: (id: number) => api.get<PC>(`/pcs/${id}`).then((r) => r.data),
  create: (data: { name: string; location_id?: number | null; description?: string }) =>
    api.post<PC>('/pcs', data).then((r) => r.data),
  update: (
    id: number,
    data: Partial<{ name: string; location_id?: number | null; description?: string | null }>,
  ) => api.put<PC>(`/pcs/${id}`, data).then((r) => r.data),
  remove: (id: number) => api.delete(`/pcs/${id}`),
}

export const donglesApi = {
  list: (search?: string) =>
    api.get<Dongle[]>('/dongles', { params: { search } }).then((r) => r.data),
  get: (id: number) => api.get<Dongle>(`/dongles/${id}`).then((r) => r.data),
  create: (data: { dongle_id: string; pc_id?: number | null; description?: string }) =>
    api.post<Dongle>('/dongles', data).then((r) => r.data),
  update: (
    id: number,
    data: Partial<{ dongle_id: string; pc_id?: number | null; description?: string | null }>,
  ) => api.put<Dongle>(`/dongles/${id}`, data).then((r) => r.data),
  remove: (id: number) => api.delete(`/dongles/${id}`),
  assignPc: (id: number, pc_id: number | null) =>
    api.post<Dongle>(`/dongles/${id}/assign-pc`, { pc_id }).then((r) => r.data),
  updateModules: (id: number, modules: DongleModuleLink[]) =>
    api.put<Dongle>(`/dongles/${id}/modules`, { modules }).then((r) => r.data),
  setModules: (id: number, modules: DongleModuleLink[]) =>
    api.post<Dongle>(`/dongles/${id}/modules`, { modules }).then((r) => r.data),
  completeness: (id: number, params: { category_id?: number; category_name?: string }) =>
    api.get<CompletenessResult>(`/dongles/${id}/completeness`, { params }).then((r) => r.data),
}

export const categoriesApi = {
  list: () => api.get<Category[]>('/categories').then((r) => r.data),
  get: (id: number, alphabetical = false) =>
    api.get<Category>(`/categories/${id}`, { params: { alphabetical } }).then((r) => r.data),
  create: (data: { name: string; description?: string }) =>
    api.post<Category>('/categories', data).then((r) => r.data),
  update: (id: number, data: Partial<{ name: string; description?: string | null }>) =>
    api.put<Category>(`/categories/${id}`, data).then((r) => r.data),
  remove: (id: number) => api.delete(`/categories/${id}`),
  setModules: (id: number, test_module_ids: number[]) =>
    api.put<Category>(`/categories/${id}/modules`, { test_module_ids }).then((r) => r.data),
}

export const testModulesApi = {
  list: (params?: {
    search?: string
    category_id?: number
    is_active?: boolean
    order?: 'manual' | 'alpha'
  }) => api.get<TestModule[]>('/test-modules', { params }).then((r) => r.data),
  get: (id: number) => api.get<TestModule>(`/test-modules/${id}`).then((r) => r.data),
  create: (data: {
    name: string
    description?: string
    sort_index?: number
    is_active?: boolean
  }) => api.post<TestModule>('/test-modules', data).then((r) => r.data),
  update: (
    id: number,
    data: Partial<{
      name: string
      description?: string | null
      sort_index?: number
      is_active?: boolean
    }>,
  ) => api.put<TestModule>(`/test-modules/${id}`, data).then((r) => r.data),
  remove: (id: number) => api.delete(`/test-modules/${id}`),
  reorder: (items: { id: number; sort_index: number }[]) =>
    api.put<TestModule[]>('/test-modules/reorder', { items }).then((r) => r.data),
}

export type ImportKind = 'pcs' | 'dongles' | 'categories' | 'test-modules'

export const importApi = {
  upload: (kind: ImportKind, file: File, previewOnly = false) => {
    const form = new FormData()
    form.append('file', file)
    form.append('preview_only', String(previewOnly))
    return api
      .post<ImportResult>(`/import/${kind}`, form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      .then((r) => r.data)
  },
  text: (kind: ImportKind, text: string, previewOnly = false) =>
    api
      .post<ImportResult>(`/import/${kind}/text`, { text, preview_only: previewOnly })
      .then((r) => r.data),
}
