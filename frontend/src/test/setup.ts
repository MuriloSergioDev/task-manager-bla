import { cleanup } from '@testing-library/react'
import { afterEach } from 'vitest'

// Globals are off (tests import from 'vitest' explicitly), so Testing
// Library can't register its own automatic cleanup.
afterEach(() => {
  cleanup()
})
