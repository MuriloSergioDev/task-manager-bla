import { useAuth } from '../../features/auth/authContext'
import { Button } from '../ui/Button'

export function Header() {
  const { user, logout } = useAuth()

  return (
    <header className="border-b border-gray-200 bg-white">
      <div className="mx-auto flex max-w-5xl items-center justify-between gap-3 px-4 py-3">
        <span className="shrink-0 text-lg font-semibold text-gray-900">Task Manager</span>
        {user && (
          <div className="flex min-w-0 items-center gap-3">
            <span className="min-w-0 truncate text-sm text-gray-600">{user.email}</span>
            <Button variant="secondary" onClick={logout} className="shrink-0">
              Log out
            </Button>
          </div>
        )}
      </div>
    </header>
  )
}
