import { describe, it, expect } from 'vitest'

describe('Vitest smoke test', () => {
  it('runs a basic assertion', () => {
    expect(1 + 1).toBe(2)
  })

  it('has jsdom environment', () => {
    expect(document).toBeDefined()
    expect(window).toBeDefined()
  })
})
