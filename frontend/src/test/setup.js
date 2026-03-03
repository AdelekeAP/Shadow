import '@testing-library/jest-dom'

// Mock localStorage
const localStorageMock = (() => {
  let store = {}
  return {
    getItem: vi.fn((key) => store[key] ?? null),
    setItem: vi.fn((key, value) => { store[key] = String(value) }),
    removeItem: vi.fn((key) => { delete store[key] }),
    clear: vi.fn(() => { store = {} }),
  }
})()
Object.defineProperty(window, 'localStorage', { value: localStorageMock })

// Mock window.location
delete window.location
window.location = { href: '', assign: vi.fn(), replace: vi.fn() }

// Reset mocks between tests
afterEach(() => {
  vi.restoreAllMocks()
  localStorageMock.clear()
})
