import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import NotificationBell from '../NotificationBell'

vi.mock('../../services/api', () => ({
  getNotifications: vi.fn(),
  getNotificationCount: vi.fn(),
  markNotificationRead: vi.fn(),
  markAllNotificationsRead: vi.fn(),
  dismissNotification: vi.fn(),
}))

import {
  getNotifications,
  getNotificationCount,
  markNotificationRead,
  markAllNotificationsRead,
  dismissNotification,
} from '../../services/api'

describe('NotificationBell', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    getNotificationCount.mockResolvedValue({ unread_count: 3, total_count: 5 })
    getNotifications.mockResolvedValue({
      notifications: [
        {
          id: 'n1',
          title: 'Task Due',
          message: 'CSC401 assignment due tomorrow',
          type: 'task_reminder',
          priority: 'high',
          is_read: false,
          created_at: new Date().toISOString(),
        },
        {
          id: 'n2',
          title: 'Study Plan Ready',
          message: 'Your AI study plan is ready',
          type: 'study_plan',
          priority: 'medium',
          is_read: true,
          created_at: new Date().toISOString(),
        },
      ],
      unread_count: 3,
      total_count: 5,
    })
  })

  it('renders bell icon', () => {
    render(<NotificationBell />)
    // Should have a clickable bell area
    expect(screen.getByRole('button')).toBeInTheDocument()
  })

  it('displays unread badge count', async () => {
    render(<NotificationBell />)
    await waitFor(() => {
      expect(screen.getByText('3')).toBeInTheDocument()
    })
  })

  it('opens dropdown on click', async () => {
    const user = userEvent.setup()
    render(<NotificationBell />)

    await user.click(screen.getByRole('button'))
    await waitFor(() => {
      expect(screen.getByText(/notifications/i)).toBeInTheDocument()
    })
  })

  it('loads notifications when dropdown opens', async () => {
    const user = userEvent.setup()
    render(<NotificationBell />)

    await user.click(screen.getByRole('button'))
    await waitFor(() => {
      expect(getNotifications).toHaveBeenCalled()
    })
  })

  it('displays notification titles in dropdown', async () => {
    const user = userEvent.setup()
    render(<NotificationBell />)

    await user.click(screen.getByRole('button'))
    await waitFor(() => {
      expect(screen.getByText('Task Due')).toBeInTheDocument()
      expect(screen.getByText('Study Plan Ready')).toBeInTheDocument()
    })
  })

  it('shows mark all read button when notifications have unread items', async () => {
    const user = userEvent.setup()
    render(<NotificationBell />)

    // Wait for badge to load
    await waitFor(() => {
      expect(screen.getByText('3')).toBeInTheDocument()
    })

    await user.click(screen.getByRole('button', { name: /notifications/i }))

    // Wait for notifications to fully load and render
    await waitFor(() => {
      expect(screen.getByText('Task Due')).toBeInTheDocument()
    })

    // Now check for mark all read
    expect(screen.getByText(/mark all read/i)).toBeInTheDocument()
  })

  it('shows empty state when no notifications', async () => {
    getNotificationCount.mockResolvedValue({ unread_count: 0, total_count: 0 })
    getNotifications.mockResolvedValue({ notifications: [] })
    const user = userEvent.setup()
    render(<NotificationBell />)

    await user.click(screen.getByRole('button'))
    await waitFor(() => {
      expect(screen.getByText(/no notification/i)).toBeInTheDocument()
    })
  })
})
