import type { ReactNode } from 'react'

import { Wordmark } from './Wordmark'

interface AuthLayoutProps {
  title: string
  subtitle: string
  children: ReactNode
}

/** Shared frame for the sign-in and registration screens. */
export function AuthLayout({ title, subtitle, children }: AuthLayoutProps) {
  return (
    <main className="flex min-h-screen flex-col bg-paper px-4 py-10 sm:justify-center">
      <div className="mx-auto w-full max-w-auth">
        <Wordmark size="lg" />
        <h1 className="mt-10 text-title font-extrabold text-ink">{title}</h1>
        <p className="mt-1.5 text-lead text-muted">{subtitle}</p>
        <div className="mt-7 rounded-sheet border border-line bg-sheet p-6 sm:p-7">{children}</div>
      </div>
    </main>
  )
}
