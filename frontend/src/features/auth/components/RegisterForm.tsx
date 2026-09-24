import { useForm } from 'react-hook-form'
import { Link } from 'react-router-dom'

import { Button } from '../../../components/ui/Button'
import { Input } from '../../../components/ui/Input'
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
    watch,
    formState: { errors },
  } = useForm<RegisterFormValues>()
  const registerMutation = useRegister()

  const onSubmit = (values: RegisterFormValues) => {
    registerMutation.mutate({ email: values.email, password: values.password })
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
          validate: (value) => value === watch('password') || 'Passwords do not match',
        })}
      />

      {registerMutation.error && (
        <p className="text-sm text-red-600" role="alert">
          {registerMutation.error.message}
        </p>
      )}

      <Button type="submit" disabled={registerMutation.isPending} className="w-full">
        {registerMutation.isPending ? 'Creating account…' : 'Create account'}
      </Button>

      <p className="text-center text-sm text-gray-600">
        Already have an account?{' '}
        <Link to="/login" className="font-medium text-blue-600 hover:underline">
          Sign in
        </Link>
      </p>
    </form>
  )
}
