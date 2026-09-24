import { useLocation } from 'react-router-dom'

import { LoginForm } from '../features/auth/components/LoginForm'

export function LoginPage() {
  const location = useLocation()
  const justRegistered = Boolean((location.state as { justRegistered?: boolean } | null)?.justRegistered)

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4">
      <div className="w-full max-w-sm space-y-6 rounded-lg bg-white p-8 shadow">
        <h1 className="text-center text-2xl font-semibold text-gray-900">Sign in</h1>
        {justRegistered && (
          <p className="rounded-md bg-green-50 px-3 py-2 text-sm text-green-700">
            Account created. Sign in below.
          </p>
        )}
        <LoginForm />
      </div>
    </div>
  )
}
