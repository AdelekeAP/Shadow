import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import WhatIfCalculator from '../WhatIfCalculator'

vi.mock('../../services/api', () => ({
  getEnrolledCourses: vi.fn(),
  getCurrentUser: vi.fn(),
}))

import { getEnrolledCourses, getCurrentUser } from '../../services/api'

const mockCourses = [
  {
    id: 'uc1',
    course: { id: 'c1', code: 'CSC401', title: 'Software Engineering', credits: 3 },
    ca_score: 25,
    exam_score: 55,
    final_grade_point: 4.0,
  },
  {
    id: 'uc2',
    course: { id: 'c2', code: 'CSC403', title: 'Artificial Intelligence', credits: 3 },
    ca_score: 20,
    exam_score: null,
    final_grade_point: null,
  },
]

const mockUser = {
  id: 'u1',
  target_cgpa: 4.5,
  current_cgpa: 3.8,
  total_credits_completed: 90,
}

function renderCalculator() {
  return render(<WhatIfCalculator onClose={vi.fn()} />)
}

describe('WhatIfCalculator', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    getEnrolledCourses.mockResolvedValue(mockCourses)
    getCurrentUser.mockReturnValue(mockUser)
  })

  it('renders calculator title', async () => {
    renderCalculator()
    await waitFor(() => {
      expect(screen.getByText(/what-if/i)).toBeInTheDocument()
    })
  })

  it('loads enrolled courses on mount', async () => {
    renderCalculator()
    await waitFor(() => {
      expect(getEnrolledCourses).toHaveBeenCalled()
    })
  })

  it('displays course list with grade selectors', async () => {
    renderCalculator()
    await waitFor(() => {
      expect(screen.getByText(/CSC401/)).toBeInTheDocument()
      expect(screen.getByText(/CSC403/)).toBeInTheDocument()
    })
  })

  it('shows grade buttons (A through F)', async () => {
    renderCalculator()
    await waitFor(() => {
      expect(screen.getAllByText('A').length).toBeGreaterThan(0)
      expect(screen.getAllByText('F').length).toBeGreaterThan(0)
    })
  })

  it('renders tab navigation', async () => {
    renderCalculator()
    await waitFor(() => {
      expect(screen.getByText(/simulator/i)).toBeInTheDocument()
      // "target" appears in multiple places; check at least one tab-like element exists
      expect(screen.getAllByText(/target/i).length).toBeGreaterThan(0)
      expect(screen.getByText(/scenarios/i)).toBeInTheDocument()
    })
  })

  it('shows CGPA classification', async () => {
    renderCalculator()
    await waitFor(() => {
      // Should display some classification text
      const text = document.body.textContent
      expect(text).toMatch(/class|cgpa/i)
    })
  })
})
