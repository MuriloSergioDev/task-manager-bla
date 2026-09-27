import { LogOut } from 'lucide-react'

import { useAuth } from '../../features/auth/authContext'
import { Button } from '../ui/Button'
import { Wordmark } from './Wordmark'

export function Header() {
  const { user, logout } = useAuth()

  return (
    <header className="border-b border-line bg-paper">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-3 px-4 py-3.5 sm:px-8">
        <Wordmark />
        {user && (
          <div className="flex min-w-0 items-center gap-3">
            <span className="hidden min-w-0 truncate text-sm text-muted sm:inline">{user.email}</span>
            <Button variant="ghost" size="sm" onClick={logout} className="shrink-0">
              <LogOut className="h-4 w-4" aria-hidden="true" />
              Log out
            </Button>
          </div>
        )}
      </div>
    </header>
  )
}
