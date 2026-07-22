export interface Location {
  id: number
  name: string
  description?: string | null
  created_at: string
  updated_at: string
  pc_count?: number
  dongle_count?: number
}

export interface PC {
  id: number
  name: string
  location_id?: number | null
  description?: string | null
  created_at: string
  updated_at: string
  location?: { id: number; name: string } | null
  dongle_count: number
  dongles?: { id: number; dongle_id: string }[]
}

export interface TestModuleBrief {
  id: number
  name: string
  sort_index: number
  is_active: boolean
}

export interface DongleModuleLink {
  test_module_id: number
  enabled: boolean
  test_module?: TestModuleBrief | null
}

export interface Dongle {
  id: number
  dongle_id: string
  pc_id?: number | null
  description?: string | null
  created_at: string
  updated_at: string
  pc?: {
    id: number
    name: string
    location?: { id: number; name: string } | null
  } | null
  enabled_module_count: number
  modules?: DongleModuleLink[]
}

export interface Category {
  id: number
  name: string
  description?: string | null
  created_at: string
  updated_at: string
  module_count: number
  modules?: TestModuleBrief[]
}

export interface TestModule {
  id: number
  name: string
  description?: string | null
  sort_index: number
  is_active: boolean
  created_at: string
  updated_at: string
  categories: { id: number; name: string }[]
}

export interface CompletenessResult {
  dongle_id: string
  category_id: number
  category: string
  total_required_modules: number
  enabled_required_modules: number
  missing_modules: { id: number; name: string; sort_index: number }[]
  extra_enabled_modules: { id: number; name: string; sort_index: number }[]
  is_complete: boolean
}

export interface ImportResult {
  created: number
  updated: number
  skipped: number
  errors: { row: number; field?: string | null; message: string; value?: string | null }[]
  details: Record<string, unknown>[]
}

export interface DashboardStats {
  dongle_count: number
  pc_count: number
  location_count: number
  category_count: number
  test_module_count: number
  unassigned_dongles: Dongle[]
  recently_changed_dongles: Dongle[]
}
