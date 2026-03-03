import { render, screen, waitFor, act } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { AuthProvider, useAuth } from '../AuthContext'

vi.mock('../../services/api', () => ({
  login: vi.fn(),
  register: vi.fn(),
  logout: vi.fn(),
  getCurrentUser: vi.fn(),
  isAuthenticated: vi.fn(),
}))

import { login, register, logout, getCurrentUser } from '../../services/api'

// Test component that exposes auth state
function AuthDisplay() {
  const auth = useAuth()
  return (
    <div>
      <span data-testid="authenticated">{auth.isAuthenticated ? 'yes' : 'no'}</span>
      <span data-testid="user">{auth.user ? auth.user.full_name : 'none'}</span>
      <span data-testid="loading">{auth.loading ? 'loading' : 'ready'}</span>
      <button onClick={() => auth.login({ email: 'test@pau.edu.ng', password: 'pass' })}>
        Login
      </button>
      <button onClick={auth.logout}>Logout</button>
    </div>
  )
}

describe('AuthContext', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
    getCurrentUser.mockReturnValue(null)
  })

  it('provides initial unauthenticated state', async () => {
    render(
      <AuthProvider><AuthDisplay /></AuthProvider>
    )
    await waitFor(() => {
      expect(screen.getByTestId('loading')).toHaveTextContent('ready')
    })
    expect(screen.getByTestId('authenticated')).toHaveTextContent('no')
    expect(screen.getByTestId('user')).toHaveTextContent('none')
  })

  it('restores user from localStorage on mount', async () => {
    localStorage.setItem('access_token', 'saved-token')
    getCurrentUser.mockReturnValue({ full_name: 'Saved User' })

    render(
      <AuthProvider><AuthDisplay /></AuthProvider>
    )
    await waitFor(() => {
      expect(screen.getByTestId('loading')).toHaveTextContent('ready')
    })
    expect(screen.getByTestId('authenticated')).toHaveTextContent('yes')
    expect(screen.getByTestId('user')).toHaveTextContent('Saved User')
  })

  it('updates state on successful login', async () => {
    login.mockResolvedValue({
      access_token: 'new-token',
      user: { full_name: 'Test Student' }
    })
    const user = userEvent.setup()
    render(
      <AuthProvider><AuthDisplay /></AuthProvider>
    )
    await waitFor(() => {
      expect(screen.getByTestId('loading')).toHaveTextContent('ready')
    })

    await user.click(screen.getByText('Login'))

    await waitFor(() => {
      expect(screen.getByTestId('authenticated')).toHaveTextContent('yes')
      expect(screen.getByTestId('user')).toHaveTextContent('Test Student')
    })
  })

  it('clears state on logout', async () => {
    localStorage.setItem('access_token', 'saved-token')
    getCurrentUser.mockReturnValue({ full_name: 'Saved User' })
    const user = userEvent.setup()

    render(
      <AuthProvider><AuthDisplay /></AuthProvider>
    )
    await waitFor(() => {
      expect(screen.getByTestId('authenticated')).toHaveTextContent('yes')
    })

    await user.click(screen.getByText('Logout'))

    expect(screen.getByTestId('authenticated')).toHaveTextContent('no')
    expect(screen.getByTestId('user')).toHaveTextContent('none')
    expect(logout).toHaveBeenCalled()
  })

  it('throws error when useAuth is used outside AuthProvider', () => {
    const consoleError = vi.spyOn(console, 'error').mockImplementation(() => {})
    expect(() => render(<AuthDisplay />)).toThrow(/useAuth must be used within an AuthProvider/)
    consoleError.mockRestore()
  })
})
