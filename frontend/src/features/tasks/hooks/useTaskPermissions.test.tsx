import { renderHook } from '@testing-library/react'
import type { ReactNode } from 'react'
import { describe, expect, it } from 'vitest'

import { makeTask, makeUser } from '../../../test/factories'
import type { Task } from '../../../types/task'
import type { User } from '../../../types/user'
import { AuthContext } from '../../auth/authContext'
import { useTaskPermissions } from './useTaskPermissions'

// Mirrors backend TaskAuthorizationService (tested there as the real
// enforcement point): owner and assignee may edit and complete; only the
// owner may delete or reassign.

function permissionsFor(user: User | null, task: Task) {
  const wrapper = ({ children }: { children: ReactNode }) => (
    <AuthContext.Provider
      value={{ user, isAuthenticated: user !== null, isLoading: false, login: () => {}, logout: () => {} }}
    >
      {children}
    </AuthContext.Provider>
  )
  return renderHook(() => useTaskPermissions(task), { wrapper }).result.current
}

const owner = makeUser({ id: 'owner-1' })
const assignee = makeUser({ id: 'assignee-1', email: 'bob@example.com' })
const stranger = makeUser({ id: 'stranger-1', email: 'carol@example.com' })
const task = makeTask({ owner_id: owner.id, assigned_to: assignee.id })

describe('useTaskPermissions', () => {
  it('lets the owner edit, complete, delete and reassign', () => {
    expect(permissionsFor(owner, task)).toMatchObject({
      isOwner: true,
      canEdit: true,
      canComplete: true,
      canDelete: true,
    })
  })

  it('lets the assignee edit and complete, but not delete or reassign', () => {
    expect(permissionsFor(assignee, task)).toMatchObject({
      isOwner: false,
      isAssignee: true,
      canEdit: true,
      canComplete: true,
      canDelete: false,
    })
  })

  it('gives anyone else no actions', () => {
    expect(permissionsFor(stranger, task)).toMatchObject({
      isInvolved: false,
      canEdit: false,
      canComplete: false,
      canDelete: false,
    })
  })

  it('does not offer "Complete" on a task that is already done', () => {
    expect(permissionsFor(owner, makeTask({ owner_id: owner.id, status: 'COMPLETED' })).canComplete).toBe(false)
  })

  // An unassigned task has assigned_to = null; that must never match a
  // signed-out (null) user as "the assignee".
  it('never treats an unassigned task as assigned to a signed-out user', () => {
    const unassigned = makeTask({ owner_id: owner.id, assigned_to: null })
    expect(permissionsFor(null, unassigned)).toMatchObject({ isAssignee: false, canEdit: false })
  })
})
