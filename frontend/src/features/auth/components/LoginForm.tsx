import { useForm } from 'react-hook-form'
import { Link } from 'react-router-dom'

import { Button } from '../../../components/ui/Button'
import { Input } from '../../../components/ui/Input'
import { useLogin } from '../hooks/useLogin'

interface LoginFormValues {
  email: string
  password: string
}

export function LoginForm() {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormValues>()
  const loginMutation = useLogin()

  const onSubmit = (values: LoginFormValues) => {
    loginMutation.mutate(values)
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
      <Input
        label="Email"
        type="email"
        autoComplete="email"
        error={errors.email?.message}
        {...register('email', {
          required: 'Email is required',
          pattern: { value: /^[^\s@]+@[^\s@]+\.[^\s@]+$/, message: 'Enter a valid email address' },
        })}
      />
      <Input
        label="Password"
        type="password"
        autoComplete="current-password"
        error={errors.password?.message}
        {...register('password', { required: 'Password is required' })}
      />

      {loginMutation.error && (
        <p className="text-sm text-red-600" role="alert">
          {loginMutation.error.message}
        </p>
      )}

      <Button type="submit" disabled={loginMutation.isPending} className="w-full">
        {loginMutation.isPending ? 'Signing in…' : 'Sign in'}
      </Button>

      <p className="text-center text-sm text-gray-600">
        Don&apos;t have an account?{' '}
        <Link to="/register" className="font-medium text-blue-600 hover:underline">
          Register
        </Link>
      </p>
    </form>
  )
}
