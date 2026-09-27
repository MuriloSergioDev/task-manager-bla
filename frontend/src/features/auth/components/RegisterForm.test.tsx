import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { renderWithProviders } from '../../../test/render'
import * as authApi from '../authApi'
import { RegisterForm } from './RegisterForm'

async function fillForm(email: string, password: string, confirmation: string) {
  await userEvent.type(screen.getByLabelText('Email'), email)
  await userEvent.type(screen.getByLabelText('Password'), password)
  await userEvent.type(screen.getByLabelText('Confirm password'), confirmation)
  await userEvent.click(screen.getByRole('button', { name: 'Create account' }))
}

describe('RegisterForm', () => {
  it('validates on the client and makes no request when invalid', async () => {
    const register = vi.spyOn(authApi, 'register')
    renderWithProviders(<RegisterForm />)

    await userEvent.click(screen.getByRole('button', { name: 'Create account' }))

    expect(await screen.findByText('Email is required')).toBeTruthy()
    expect(screen.getByText('Password is required')).toBeTruthy()
    expect(screen.getByText('Please confirm your password')).toBeTruthy()
    expect(register).not.toHaveBeenCalled()
  })

  it('rejects a short password and a mismatched confirmation', async () => {
    const register = vi.spyOn(authApi, 'register')
    renderWithProviders(<RegisterForm />)

    await fillForm('new@example.com', 'short', 'different')

    expect(await screen.findByText('Password must be at least 8 characters')).toBeTruthy()
    expect(screen.getByText('Passwords do not match')).toBeTruthy()
    expect(register).not.toHaveBeenCalled()
  })

  it('sends only email and password, not the confirmation', async () => {
    const register = vi.spyOn(authApi, 'register').mockResolvedValue({
      id: 'new-user',
      email: 'new@example.com',
      is_active: true,
    })
    renderWithProviders(<RegisterForm />)

    await fillForm('new@example.com', 'CorrectHorse9', 'CorrectHorse9')

    await vi.waitFor(() => expect(register).toHaveBeenCalledTimes(1))
    expect(register.mock.calls[0][0]).toEqual({ email: 'new@example.com', password: 'CorrectHorse9' })
  })

  it('shows the API error when registration fails', async () => {
    vi.spyOn(authApi, 'register').mockRejectedValue({ status: 400, message: 'Email is already registered' })
    renderWithProviders(<RegisterForm />)

    await fillForm('alice@example.com', 'CorrectHorse9', 'CorrectHorse9')

    expect((await screen.findByRole('alert')).textContent).toBe('Email is already registered')
  })
})
