import '@testing-library/jest-dom/vitest'
import { cleanup } from '@testing-library/react'
import { afterEach } from 'vitest'

/**
 * Reset the DOM between tests so component state never leaks across cases.
 */
const resetDomAfterEach = () => {
  cleanup()
}

afterEach(resetDomAfterEach)