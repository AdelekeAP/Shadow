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

vi.mock('../../services/api', () => ({
  login: vi.fn(),
}))

import { login } from '../../services/api'

function renderLogin() {
  return render(<MemoryRouter><LoginPage /></MemoryRouter>)
}

describe('LoginPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders login form with email and password fields', () => {
    renderLogin()
    expect(screen.getByPlaceholderText(/email/i)).toBeInTheDocument()
    expect(screen.getByPlaceholderText(/••••••••/)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument()
  })

  it('renders link to register page', () => {
    renderLogin()
    expect(screen.getByText(/register here/i)).toBeInTheDocument()
  })

  it('calls login API on form submission', async () => {
    login.mockResolvedValue({ access_token: 'tok', user: { id: 1 } })
    const user = userEvent.setup()
    renderLogin()

    await user.type(screen.getByPlaceholderText(/email/i), 'test@pau.edu.ng')
    await user.type(screen.getByPlaceholderText(/••••••••/), 'Password123!')
    await user.click(screen.getByRole('button', { name: /sign in/i }))

    await waitFor(() => {
      expect(login).toHaveBeenCalledWith({
        email: 'test@pau.edu.ng',
        password: 'Password123!',
      })
    })
  })

  it('navigates to dashboard on successful login', async () => {
    login.mockResolvedValue({ access_token: 'tok', user: { id: 1, full_name: 'Test' } })
    const user = userEvent.setup()
    renderLogin()

    await user.type(screen.getByPlaceholderText(/email/i), 'test@pau.edu.ng')
    await user.type(screen.getByPlaceholderText(/••••••••/), 'Password123!')
    await user.click(screen.getByRole('button', { name: /sign in/i }))

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/dashboard')
    })
  })

  it('displays error message on failed login', async () => {
    login.mockRejectedValue({ detail: 'Incorrect email or password' })
    const user = userEvent.setup()
    renderLogin()

    await user.type(screen.getByPlaceholderText(/email/i), 'wrong@pau.edu.ng')
    await user.type(screen.getByPlaceholderText(/••••••••/), 'bad')
    await user.click(screen.getByRole('button', { name: /sign in/i }))

    await waitFor(() => {
      expect(screen.getByText(/incorrect|error|failed/i)).toBeInTheDocument()
    })
  })

  it('shows loading state during submission', async () => {
    let resolveLogin
    login.mockImplementation(() => new Promise((r) => { resolveLogin = r }))
    const user = userEvent.setup()
    renderLogin()

    await user.type(screen.getByPlaceholderText(/email/i), 'test@pau.edu.ng')
    await user.type(screen.getByPlaceholderText(/••••••••/), 'Password123!')
    await user.click(screen.getByRole('button', { name: /sign in/i }))

    expect(screen.getByText(/signing in/i)).toBeInTheDocument()
    resolveLogin({ access_token: 'tok', user: {} })
  })
})
