import { createBrowserRouter, Navigate } from 'react-router-dom'

import { AppShell } from '../components/layout/AppShell'
import { ProtectedRoute } from '../components/layout/ProtectedRoute'
import { PublicOnlyRoute } from '../components/layout/PublicOnlyRoute'
import { DashboardPage } from '../routes/DashboardPage'
import { LoginPage } from '../routes/LoginPage'
import { RegisterPage } from '../routes/RegisterPage'

export const router = createBrowserRouter([
  {
    path: '/',
    element: <Navigate to="/dashboard" replace />,
  },
  {
    path: '/login',
    element: (
      <PublicOnlyRoute>
        <LoginPage />
      </PublicOnlyRoute>
    ),
  },
  {
    path: '/register',
    element: (
      <PublicOnlyRoute>
        <RegisterPage />
      </PublicOnlyRoute>
    ),
  },
  {
    path: '/dashboard',
    element: (
      <ProtectedRoute>
        <AppShell>
          <DashboardPage />
        </AppShell>
      </ProtectedRoute>
    ),
  },
])
