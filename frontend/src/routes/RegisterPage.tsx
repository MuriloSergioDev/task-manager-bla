import { AuthLayout } from '../components/layout/AuthLayout'
import { RegisterForm } from '../features/auth/components/RegisterForm'

export function RegisterPage() {
  return (
    <AuthLayout title="Create an account" subtitle="Use your work email. You'll sign in right after.">
      <RegisterForm />
    </AuthLayout>
  )
}
