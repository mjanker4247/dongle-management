import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { AppLayout } from './components/AppLayout'
import { CategoriesPage } from './pages/CategoriesPage'
import { DashboardPage } from './pages/DashboardPage'
import { DongleDetailPage, DonglesPage } from './pages/DonglesPage'
import { ImportPage } from './pages/ImportPage'
import { LocationsPage } from './pages/LocationsPage'
import { PCsPage } from './pages/PCsPage'
import { QuickDongleEntryPage } from './pages/QuickDongleEntryPage'
import { TestModulesPage } from './pages/TestModulesPage'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppLayout />}>
          <Route index element={<DashboardPage />} />
          <Route path="dongles" element={<DonglesPage />} />
          <Route path="dongles/:id" element={<DongleDetailPage />} />
          <Route path="pcs" element={<PCsPage />} />
          <Route path="locations" element={<LocationsPage />} />
          <Route path="categories" element={<CategoriesPage />} />
          <Route path="test-modules" element={<TestModulesPage />} />
          <Route path="import" element={<ImportPage />} />
          <Route path="quick-entry" element={<QuickDongleEntryPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
