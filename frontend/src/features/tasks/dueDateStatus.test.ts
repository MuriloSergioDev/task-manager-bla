import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { makeTask } from '../../test/factories'
import {
  daysOverdue,
  dueDateParts,
  formatCompletedDate,
  formatDueDate,
  getDueState,
  isOverdue,
} from './dueDateStatus'

// vitest.config.ts pins TZ to America/Sao_Paulo (UTC-3), so "local" and
// "UTC" calendar days differ between 21:00 and midnight local time.

describe('dueDateStatus', () => {
  beforeEach(() => {
    vi.useFakeTimers({ toFake: ['Date'] })
    // Midday local time: the local and UTC dates are the same.
    vi.setSystemTime(new Date('2026-09-27T12:00:00-03:00'))
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  describe('getDueState', () => {
    it('is "none" without a due date', () => {
      expect(getDueState(makeTask({ due_date: null }))).toBe('none')
    })

    it('is "overdue" for a past due date', () => {
      expect(getDueState(makeTask({ due_date: '2026-09-26' }))).toBe('overdue')
    })

    it('is "today" on the due date', () => {
      expect(getDueState(makeTask({ due_date: '2026-09-27' }))).toBe('today')
    })

    it('is "upcoming" for a future due date', () => {
      expect(getDueState(makeTask({ due_date: '2026-09-28' }))).toBe('upcoming')
    })

    it('is "done" for a completed task, even one that was due in the past', () => {
      const task = makeTask({ status: 'COMPLETED', due_date: '2026-09-01' })
      expect(getDueState(task)).toBe('done')
      expect(isOverdue(task)).toBe(false)
    })
  })

  // Regression: "today" used to come from toISOString(), i.e. the UTC date.
  // At 23:30 in UTC-3 it's already the next day in UTC, so a task due today
  // was shown as overdue for the last three hours of every day.
  describe('uses the local calendar day, not UTC', () => {
    beforeEach(() => {
      vi.setSystemTime(new Date('2026-09-27T23:30:00-03:00')) // 2026-09-28T02:30Z
    })

    it('treats a task due today as due today late in the evening', () => {
      const task = makeTask({ due_date: '2026-09-27' })
      expect(getDueState(task)).toBe('today')
      expect(isOverdue(task)).toBe(false)
    })

    it("treats tomorrow's date as upcoming, not today", () => {
      expect(getDueState(makeTask({ due_date: '2026-09-28' }))).toBe('upcoming')
    })
  })

  describe('daysOverdue', () => {
    it('counts whole calendar days past the due date', () => {
      expect(daysOverdue(makeTask({ due_date: '2026-09-24' }))).toBe(3)
      expect(daysOverdue(makeTask({ due_date: '2026-09-26' }))).toBe(1)
    })

    it('is 0 when the task is not overdue', () => {
      expect(daysOverdue(makeTask({ due_date: '2026-09-27' }))).toBe(0)
      expect(daysOverdue(makeTask({ due_date: null }))).toBe(0)
      expect(daysOverdue(makeTask({ due_date: '2026-09-01', status: 'COMPLETED' }))).toBe(0)
    })
  })

  describe('dueDateParts', () => {
    it('omits the year when it is the current one', () => {
      expect(dueDateParts('2026-10-05')).toEqual({ month: 'Oct', day: '5', year: null })
    })

    it('includes the year when it is not', () => {
      expect(dueDateParts('2027-01-15')).toEqual({ month: 'Jan', day: '15', year: '2027' })
    })
  })

  describe('formatting', () => {
    // A date-only string parsed as UTC midnight would display as the
    // previous day west of UTC ("Sep 4" for 2026-09-05 in UTC-3).
    it('formats a due date as the same calendar day in any time zone', () => {
      expect(formatDueDate('2026-09-05')).toBe('Sep 5, 2026')
    })

    it('says so when there is no due date', () => {
      expect(formatDueDate(null)).toBe('No due date')
    })

    it('formats a completion timestamp in local time', () => {
      // 01:00 UTC on the 16th is still the 15th in UTC-3.
      expect(formatCompletedDate('2026-09-16T01:00:00Z')).toBe('Sep 15, 2026')
    })
  })
})
