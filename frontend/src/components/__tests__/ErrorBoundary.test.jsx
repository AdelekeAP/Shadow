import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import ErrorBoundary from '../ErrorBoundary'

function ThrowingComponent() {
  throw new Error('Test error')
}

describe('ErrorBoundary', () => {
  it('renders children when no error', () => {
    render(
      <ErrorBoundary>
        <div>Normal Content</div>
      </ErrorBoundary>
    )
    expect(screen.getByText('Normal Content')).toBeInTheDocument()
  })

  it('renders error fallback when child throws', () => {
    const consoleError = vi.spyOn(console, 'error').mockImplementation(() => {})
    render(
      <ErrorBoundary>
        <ThrowingComponent />
      </ErrorBoundary>
    )
    expect(screen.getByText(/something went wrong/i)).toBeInTheDocument()
    expect(screen.getByText(/refresh page/i)).toBeInTheDocument()
    expect(screen.queryByText('Normal Content')).not.toBeInTheDocument()
    consoleError.mockRestore()
  })

  it('shows refresh button in error state', () => {
    const consoleError = vi.spyOn(console, 'error').mockImplementation(() => {})
    render(
      <ErrorBoundary>
        <ThrowingComponent />
      </ErrorBoundary>
    )
    expect(screen.getByRole('button', { name: /refresh/i })).toBeInTheDocument()
    consoleError.mockRestore()
  })
})
