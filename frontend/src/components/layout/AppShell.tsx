import type { ReactNode } from 'react'

import { Header } from './Header'

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen bg-paper">
      <Header />
      <main className="mx-auto max-w-6xl px-4 pt-8 pb-16 sm:px-8 sm:pt-12">{children}</main>
    </div>
  )
}
