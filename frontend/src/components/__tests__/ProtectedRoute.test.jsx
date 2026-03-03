import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, it, expect, vi } from 'vitest'
import ProtectedRoute from '../ProtectedRoute'

// Mock useAuth hook
const mockAuth = {
  isAuthenticated: false,
  loading: false,
}

vi.mock('../../contexts/AuthContext', () => ({
  useAuth: () => mockAuth,
}))

function renderProtected(children = <div>Protected Content</div>) {
  return render(
    <MemoryRouter>
      <ProtectedRoute>{children}</ProtectedRoute>
    </MemoryRouter>
  )
}

describe('ProtectedRoute', () => {
  it('shows loading spinner when auth is loading', () => {
    mockAuth.loading = true
    mockAuth.isAuthenticated = false
    renderProtected()
    // Should show spinner, not content
    expect(screen.queryByText('Protected Content')).not.toBeInTheDocument()
  })

  it('redirects to login when not authenticated', () => {
    mockAuth.loading = false
    mockAuth.isAuthenticated = false
    renderProtected()
    expect(screen.queryByText('Protected Content')).not.toBeInTheDocument()
  })

  it('renders children when authenticated', () => {
    mockAuth.loading = false
    mockAuth.isAuthenticated = true
    renderProtected()
    expect(screen.getByText('Protected Content')).toBeInTheDocument()
  })
})
