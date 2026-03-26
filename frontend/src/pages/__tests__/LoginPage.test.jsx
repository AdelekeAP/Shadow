import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import LoginPage from '../LoginPage'

const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return { ...actual, useNavigate: () => mockNavigate }
})

const mockLogin = vi.fn()
vi.mock('../../contexts/AuthContext', () => ({
  useAuth: () => ({ login: mockLogin, isAuthenticated: false, loading: false }),
}))

function renderLogin() {
  return render(<MemoryRouter><LoginPage /></MemoryRouter>)
}

describe('LoginPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders login form with email and password fields', () => {
    renderLogin()
    expect(screen.getByPlaceholderText('your.email@pau.edu.ng')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('Enter your password')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument()
  })

  it('renders link to register page', () => {
    renderLogin()
    expect(screen.getByText('Register')).toBeInTheDocument()
  })

  it('calls login API on form submission', async () => {
    mockLogin.mockResolvedValue({ access_token: 'tok', user: { id: 1 } })
    const user = userEvent.setup()
    renderLogin()

    await user.type(screen.getByPlaceholderText('your.email@pau.edu.ng'), 'test@pau.edu.ng')
    await user.type(screen.getByPlaceholderText('Enter your password'), 'Password123!')
    await user.click(screen.getByRole('button', { name: /sign in/i }))

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith({
        email: 'test@pau.edu.ng',
        password: 'Password123!',
      })
    })
  })

  it('navigates to dashboard on successful login', async () => {
    mockLogin.mockResolvedValue({ access_token: 'tok', user: { id: 1, full_name: 'Test' } })
    const user = userEvent.setup()
    renderLogin()

    await user.type(screen.getByPlaceholderText('your.email@pau.edu.ng'), 'test@pau.edu.ng')
    await user.type(screen.getByPlaceholderText('Enter your password'), 'Password123!')
    await user.click(screen.getByRole('button', { name: /sign in/i }))

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/dashboard')
    })
  })

  it('displays error message on failed login', async () => {
    mockLogin.mockRejectedValue({ detail: 'Incorrect email or password' })
    const user = userEvent.setup()
    renderLogin()

    await user.type(screen.getByPlaceholderText('your.email@pau.edu.ng'), 'wrong@pau.edu.ng')
    await user.type(screen.getByPlaceholderText('Enter your password'), 'bad')
    await user.click(screen.getByRole('button', { name: /sign in/i }))

    await waitFor(() => {
      expect(screen.getByText(/incorrect|error|failed/i)).toBeInTheDocument()
    })
  })

  it('shows loading state during submission', async () => {
    let resolveLogin
    mockLogin.mockImplementation(() => new Promise((r) => { resolveLogin = r }))
    const user = userEvent.setup()
    renderLogin()

    await user.type(screen.getByPlaceholderText('your.email@pau.edu.ng'), 'test@pau.edu.ng')
    await user.type(screen.getByPlaceholderText('Enter your password'), 'Password123!')
    await user.click(screen.getByRole('button', { name: /sign in/i }))

    // Button should be disabled during loading
    expect(screen.getByRole('button').closest('button')).toBeDisabled()
    resolveLogin({ access_token: 'tok', user: {} })
  })
})
