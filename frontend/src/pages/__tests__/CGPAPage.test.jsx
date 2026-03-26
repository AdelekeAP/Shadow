import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import CGPAPage from '../CGPAPage'

// Mock child components to isolate CGPAPage logic
vi.mock('../../components/CGPADashboard', () => ({
  default: () => <div data-testid="cgpa-dashboard">Dashboard</div>,
}))
vi.mock('../../components/WhatIfCalculator', () => ({
  default: ({ onClose }) => (
    <div data-testid="whatif-calculator">
      <button onClick={onClose}>Close</button>
    </div>
  ),
}))

vi.mock('../../contexts/AuthContext', () => ({
  useAuth: () => ({
    user: { full_name: 'Test Student', target_cgpa: 4.5, current_cgpa: 3.8 },
    isAuthenticated: true,
    loading: false,
  }),
}))

function renderCGPAPage() {
  return render(<MemoryRouter><CGPAPage /></MemoryRouter>)
}

describe('CGPAPage', () => {
  it('renders page title', () => {
    renderCGPAPage()
    expect(screen.getByText(/CGPA Analytics/i)).toBeInTheDocument()
  })

  it('renders CGPADashboard component', () => {
    renderCGPAPage()
    expect(screen.getByTestId('cgpa-dashboard')).toBeInTheDocument()
  })

  it('renders What-If Calculator button', () => {
    renderCGPAPage()
    expect(screen.getByText(/what-if calculator/i)).toBeInTheDocument()
  })

  it('opens What-If Calculator modal on button click', async () => {
    const user = userEvent.setup()
    renderCGPAPage()

    await user.click(screen.getByText(/what-if calculator/i))
    expect(screen.getByTestId('whatif-calculator')).toBeInTheDocument()
  })

  it('closes What-If Calculator modal', async () => {
    const user = userEvent.setup()
    renderCGPAPage()

    await user.click(screen.getByText(/what-if calculator/i))
    expect(screen.getByTestId('whatif-calculator')).toBeInTheDocument()

    await user.click(screen.getByText('Close'))
    expect(screen.queryByTestId('whatif-calculator')).not.toBeInTheDocument()
  })

  it('displays PAU grading scale information', () => {
    renderCGPAPage()
    // Should show grading scale reference
    expect(screen.getByText(/first class/i)).toBeInTheDocument()
  })
})
