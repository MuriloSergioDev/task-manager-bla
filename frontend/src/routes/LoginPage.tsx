import { useLocation } from 'react-router-dom'

import { AuthLayout } from '../components/layout/AuthLayout'
import { Alert } from '../components/ui'
import { LoginForm } from '../features/auth/components/LoginForm'

export function LoginPage() {
  const location = useLocation()
  const justRegistered = Boolean((location.state as { justRegistered?: boolean } | null)?.justRegistered)

  return (
    <AuthLayout title="Sign in" subtitle="See what's due and what's assigned to you.">
      {justRegistered && (
        <Alert tone="success" className="mb-5">
          Account created. Sign in with your new password.
        </Alert>
      )}
      <LoginForm />
    </AuthLayout>
  )
}
