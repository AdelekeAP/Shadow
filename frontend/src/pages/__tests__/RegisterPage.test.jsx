import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import RegisterPage from '../RegisterPage'

const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return { ...actual, useNavigate: () => mockNavigate }
})

const mockRegister = vi.fn()
vi.mock('../../contexts/AuthContext', () => ({
  useAuth: () => ({ register: mockRegister, isAuthenticated: false, loading: false }),
}))

function renderRegister() {
  return render(<MemoryRouter><RegisterPage /></MemoryRouter>)
}

async function fillForm(user) {
  await user.type(screen.getByPlaceholderText('Paul Adeleke'), 'Test Student')
  await user.type(screen.getByPlaceholderText('your.email@pau.edu.ng'), 'test@pau.edu.ng')
  await user.type(screen.getByPlaceholderText('Min 8 characters'), 'SecurePass123!')
  await user.type(screen.getByPlaceholderText('Re-enter password'), 'SecurePass123!')
}

describe('RegisterPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders registration form fields', () => {
    renderRegister()
    expect(screen.getByPlaceholderText('Paul Adeleke')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('your.email@pau.edu.ng')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('Min 8 characters')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('Re-enter password')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /create account/i })).toBeInTheDocument()
  })

  it('renders PAU-specific fields (level, CGPA)', () => {
    renderRegister()
    // Level select and Target CGPA field
    expect(screen.getByDisplayValue('400 Level')).toBeInTheDocument()
    expect(screen.getByText(/target cgpa/i)).toBeInTheDocument()
    expect(screen.getByDisplayValue('4.50')).toBeInTheDocument()
  })

  it('validates passwords match', async () => {
    const user = userEvent.setup()
    renderRegister()

    await user.type(screen.getByPlaceholderText('Paul Adeleke'), 'Test User')
    await user.type(screen.getByPlaceholderText('your.email@pau.edu.ng'), 'test@pau.edu.ng')
    await user.type(screen.getByPlaceholderText('Min 8 characters'), 'Password123!')
    await user.type(screen.getByPlaceholderText('Re-enter password'), 'DifferentPass1!')
    await user.click(screen.getByRole('button', { name: /create account/i }))

    await waitFor(() => {
      expect(screen.getByText(/passwords do not match/i)).toBeInTheDocument()
    })
  })

  it('validates password minimum length', async () => {
    const user = userEvent.setup()
    renderRegister()

    await user.type(screen.getByPlaceholderText('Paul Adeleke'), 'Test User')
    await user.type(screen.getByPlaceholderText('your.email@pau.edu.ng'), 'test@pau.edu.ng')
    await user.type(screen.getByPlaceholderText('Min 8 characters'), 'short')
    await user.type(screen.getByPlaceholderText('Re-enter password'), 'short')
    await user.click(screen.getByRole('button', { name: /create account/i }))

    await waitFor(() => {
      expect(screen.getByText(/8 characters/i)).toBeInTheDocument()
    })
  })

  it('calls register API with correct data on submission', async () => {
    mockRegister.mockResolvedValue({ access_token: 'tok', user: { id: 1 } })
    const user = userEvent.setup()
    renderRegister()

    await fillForm(user)
    await user.click(screen.getByRole('button', { name: /create account/i }))

    await waitFor(() => {
      expect(mockRegister).toHaveBeenCalledTimes(1)
      const callArgs = mockRegister.mock.calls[0][0]
      expect(callArgs.full_name).toBe('Test Student')
      expect(callArgs.email).toBe('test@pau.edu.ng')
      expect(callArgs.entry_level).toBe('400L')
    })
  })

  it('navigates to dashboard on successful registration', async () => {
    mockRegister.mockResolvedValue({ access_token: 'tok', user: { id: 1 } })
    const user = userEvent.setup()
    renderRegister()

    await fillForm(user)
    await user.click(screen.getByRole('button', { name: /create account/i }))

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/dashboard')
    })
  })

  it('displays API error on failed registration', async () => {
    mockRegister.mockRejectedValue({ detail: 'Email already registered' })
    const user = userEvent.setup()
    renderRegister()

    await fillForm(user)
    await user.click(screen.getByRole('button', { name: /create account/i }))

    await waitFor(() => {
      expect(screen.getByText(/already registered/i)).toBeInTheDocument()
    })
  })

  it('has link to login page', () => {
    renderRegister()
    expect(screen.getByText('Sign in')).toBeInTheDocument()
  })
})
