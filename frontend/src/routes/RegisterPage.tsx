import { RegisterForm } from '../features/auth/components/RegisterForm'

export function RegisterPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4">
      <div className="w-full max-w-sm space-y-6 rounded-lg bg-white p-8 shadow">
        <h1 className="text-center text-2xl font-semibold text-gray-900">Create an account</h1>
        <RegisterForm />
      </div>
    </div>
  )
}
