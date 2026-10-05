import '@testing-library/jest-dom/vitest'
import { cleanup } from '@testing-library/react'
import { afterEach } from 'vitest'

/**
 * Provide a predictable localStorage implementation when jsdom does not expose one.
 */
const ensureTestLocalStorage = () => {
  if (typeof window === 'undefined') {
    return
  }

  let existingStorage: Storage | undefined
  try {
    existingStorage = window.localStorage ?? undefined
  } catch {
    existingStorage = undefined
  }

  if (existingStorage) {
    return
  }

  const storageMap = new Map<string, string>()
  const storage: Storage = {
    get length() {
      return storageMap.size
    },
    clear() {
      storageMap.clear()
    },
    getItem(key: string) {
      return storageMap.has(key) ? storageMap.get(key) ?? null : null
    },
    key(index: number) {
      return Array.from(storageMap.keys())[index] ?? null
    },
    removeItem(key: string) {
      storageMap.delete(key)
    },
    setItem(key: string, value: string) {
      storageMap.set(key, value)
    },
  }

  Object.defineProperty(window, 'localStorage', {
    configurable: true,
    value: storage,
    writable: true,
  })
}

/**
 * Reset the DOM between tests so component state never leaks across cases.
 */
const resetDomAfterEach = () => {
  cleanup()
}

ensureTestLocalStorage()

afterEach(resetDomAfterEach)