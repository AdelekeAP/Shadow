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

vi.mock('../../services/api', () => ({
  register: vi.fn(),
}))

import { register } from '../../services/api'

function renderRegister() {
  return render(<MemoryRouter><RegisterPage /></MemoryRouter>)
}

async function fillForm(user) {
  await user.type(screen.getByLabelText(/full name/i), 'Test Student')
  await user.type(screen.getByLabelText(/email address/i), 'test@pau.edu.ng')
  await user.type(screen.getByLabelText(/^password$/i), 'SecurePass123!')
  await user.type(screen.getByLabelText(/confirm password/i), 'SecurePass123!')
}

describe('RegisterPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders registration form fields', () => {
    renderRegister()
    expect(screen.getByLabelText(/full name/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/email address/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/^password$/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/confirm password/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /create account/i })).toBeInTheDocument()
  })

  it('renders PAU-specific fields (level, CGPA)', () => {
    renderRegister()
    expect(screen.getByLabelText(/current level/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/target cgpa/i)).toBeInTheDocument()
    expect(screen.getByDisplayValue('4.50')).toBeInTheDocument()
  })

  it('validates passwords match', async () => {
    const user = userEvent.setup()
    renderRegister()

    await user.type(screen.getByLabelText(/full name/i), 'Test User')
    await user.type(screen.getByLabelText(/email address/i), 'test@pau.edu.ng')
    await user.type(screen.getByLabelText(/^password$/i), 'Password123!')
    await user.type(screen.getByLabelText(/confirm password/i), 'DifferentPass!')
    await user.click(screen.getByRole('button', { name: /create account/i }))

    await waitFor(() => {
      expect(screen.getByText(/passwords do not match/i)).toBeInTheDocument()
    })
  })

  it('validates password minimum length', async () => {
    const user = userEvent.setup()
    renderRegister()

    await user.type(screen.getByLabelText(/full name/i), 'Test User')
    await user.type(screen.getByLabelText(/email address/i), 'test@pau.edu.ng')
    await user.type(screen.getByLabelText(/^password$/i), 'short')
    await user.type(screen.getByLabelText(/confirm password/i), 'short')
    await user.click(screen.getByRole('button', { name: /create account/i }))

    await waitFor(() => {
      expect(screen.getByText(/8 characters/i)).toBeInTheDocument()
    })
  })

  it('calls register API with correct data on submission', async () => {
    register.mockResolvedValue({ access_token: 'tok', user: { id: 1 } })
    const user = userEvent.setup()
    renderRegister()

    await fillForm(user)
    await user.click(screen.getByRole('button', { name: /create account/i }))

    await waitFor(() => {
      expect(register).toHaveBeenCalledTimes(1)
      const callArgs = register.mock.calls[0][0]
      expect(callArgs.full_name).toBe('Test Student')
      expect(callArgs.email).toBe('test@pau.edu.ng')
      expect(callArgs.entry_level).toBe('400L')
    })
  })

  it('navigates to dashboard on successful registration', async () => {
    register.mockResolvedValue({ access_token: 'tok', user: { id: 1 } })
    const user = userEvent.setup()
    renderRegister()

    await fillForm(user)
    await user.click(screen.getByRole('button', { name: /create account/i }))

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/dashboard')
    })
  })

  it('displays API error on failed registration', async () => {
    register.mockRejectedValue({ detail: 'Email already registered' })
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
    expect(screen.getByText(/login here/i)).toBeInTheDocument()
  })
})
