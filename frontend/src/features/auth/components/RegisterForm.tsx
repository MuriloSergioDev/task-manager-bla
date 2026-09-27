import { useForm } from 'react-hook-form'
import { Link } from 'react-router-dom'

import { Alert, Button, Input } from '../../../components/ui'
import { useRegister } from '../hooks/useRegister'

interface RegisterFormValues {
  email: string
  password: string
  confirmPassword: string
}

export function RegisterForm() {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterFormValues>()
  const registerMutation = useRegister()

  const onSubmit = (values: RegisterFormValues) => {
    registerMutation.mutate({ email: values.email, password: values.password })
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-5" noValidate>
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
        autoComplete="new-password"
        error={errors.password?.message}
        {...register('password', {
          required: 'Password is required',
          minLength: { value: 8, message: 'Password must be at least 8 characters' },
        })}
      />
      <Input
        label="Confirm password"
        type="password"
        autoComplete="new-password"
        error={errors.confirmPassword?.message}
        {...register('confirmPassword', {
          required: 'Please confirm your password',
          validate: (value, formValues) => value === formValues.password || 'Passwords do not match',
        })}
      />

      {registerMutation.error && (
        <Alert tone="error">{registerMutation.error.message}</Alert>
      )}

      <Button type="submit" disabled={registerMutation.isPending} className="w-full">
        {registerMutation.isPending ? 'Creating account…' : 'Create account'}
      </Button>

      <p className="pt-1 text-sm text-muted">
        Already have an account?{' '}
        <Link to="/login" className="font-semibold text-ink underline decoration-line-strong underline-offset-4 hover:decoration-ink">
          Sign in
        </Link>
      </p>
    </form>
  )
}
