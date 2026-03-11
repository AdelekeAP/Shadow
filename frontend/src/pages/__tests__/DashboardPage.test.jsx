import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, it, expect, vi, beforeEach } from 'vitest'

// ── API mocks ───────────────────────────────────────────────────────────────
vi.mock('../../services/api', () => ({
  getEnrolledCourses: vi.fn(() => Promise.resolve([])),
  getTasks: vi.fn(() => Promise.resolve([])),
  getTaskStats: vi.fn(() => Promise.resolve(null)),
  updateEnrollment: vi.fn(),
  resendVerification: vi.fn(),
}))

// ── AuthContext mock ────────────────────────────────────────────────────────
vi.mock('../../contexts/AuthContext', () => ({
  useAuth: () => ({
    user: { full_name: 'Test Student', current_cgpa: 3.8, target_cgpa: 4.5, total_credits_completed: 60, email_verified: true },
    logout: vi.fn(),
    isAuthenticated: true,
  }),
}))

// ── Heavy child component mocks ─────────────────────────────────────────────
vi.mock('../../components/TaskList', () => ({
  default: ({ tasks }) => <div data-testid="task-list">Tasks: {tasks.length}</div>,
}))
vi.mock('../../components/CourseCarousel', () => ({
  default: ({ enrolledCourses }) => <div data-testid="course-carousel">Courses: {enrolledCourses.length}</div>,
}))
vi.mock('../../components/PriorityRecommendationsCompact', () => ({
  default: () => <div data-testid="priority-recommendations">Priority</div>,
}))
vi.mock('../../components/MoodLogger', () => ({
  default: () => <div data-testid="mood-logger">MoodLogger</div>,
}))
vi.mock('../../components/SmartStudyChat', () => ({
  default: () => <div data-testid="smartstudy-chat">Chat</div>,
}))
vi.mock('../../components/SmartStudyTriggerBanner', () => ({
  default: () => <div data-testid="smartstudy-banner">Banner</div>,
}))
vi.mock('../../components/AddTaskModal', () => ({
  default: () => null,
}))
vi.mock('../../components/EditCourseScoresModal', () => ({
  default: () => null,
}))
vi.mock('../../components/NotificationBell', () => ({
  default: () => <div data-testid="notification-bell">Bell</div>,
}))

import DashboardPage from '../DashboardPage'

function renderDashboard() {
  return render(
    <MemoryRouter>
      <DashboardPage />
    </MemoryRouter>
  )
}

describe('DashboardPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders the Shadow brand logo in the navigation', async () => {
    renderDashboard()
    await waitFor(() => {
      expect(screen.getByText('Shadow')).toBeInTheDocument()
    })
  })

  it('renders the CGPA display area with current and target values', async () => {
    renderDashboard()
    await waitFor(() => {
      // The CGPA card shows Current and Target labels (may appear multiple times in the layout)
      const currentEls = screen.getAllByText('Current')
      expect(currentEls.length).toBeGreaterThan(0)
      const targetEls = screen.getAllByText('Target')
      expect(targetEls.length).toBeGreaterThan(0)
    })
  })

  it('renders the task section with Add Task button', async () => {
    renderDashboard()
    await waitFor(() => {
      expect(screen.getByText('My Tasks')).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /add task/i })).toBeInTheDocument()
    })
  })

  it('shows empty task state when no courses are enrolled', async () => {
    renderDashboard()
    await waitFor(() => {
      expect(screen.getByText(/enroll in courses to start adding tasks/i)).toBeInTheDocument()
    })
  })

  it('renders SmartStudy trigger banner', async () => {
    renderDashboard()
    await waitFor(() => {
      expect(screen.getByTestId('smartstudy-banner')).toBeInTheDocument()
    })
  })

  it('renders navigation links for major sections', async () => {
    renderDashboard()
    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Courses' })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: 'CGPA' })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: 'Library' })).toBeInTheDocument()
    })
  })
})
