import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import MoodLogger from '../MoodLogger'

vi.mock('../../services/api', () => {
  const api = {
    post: vi.fn(),
    get: vi.fn(),
    patch: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  }
  return { default: api }
})

import api from '../../services/api'

const mockOnMoodLogged = vi.fn()
const mockOnClose = vi.fn()

function renderMoodLogger() {
  return render(<MoodLogger onMoodLogged={mockOnMoodLogged} onClose={mockOnClose} />)
}

describe('MoodLogger', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    // Suppress alert calls in tests
    vi.spyOn(window, 'alert').mockImplementation(() => {})
  })

  it('renders heading', () => {
    renderMoodLogger()
    expect(screen.getByText('How are you feeling?')).toBeInTheDocument()
  })

  it('renders all 8 mood buttons with emojis', () => {
    renderMoodLogger()
    // Mood labels include emojis like "🎯 Focused"
    expect(screen.getByText(/Focused/)).toBeInTheDocument()
    expect(screen.getByText(/Tired/)).toBeInTheDocument()
    expect(screen.getByText(/Stressed/)).toBeInTheDocument()
    expect(screen.getByText(/Motivated/)).toBeInTheDocument()
    expect(screen.getByText(/Calm/)).toBeInTheDocument()
    expect(screen.getByText(/Confident/)).toBeInTheDocument()
    expect(screen.getByText(/Anxious/)).toBeInTheDocument()
    expect(screen.getByText(/Overwhelmed/)).toBeInTheDocument()
  })

  it('renders energy level indicators', () => {
    renderMoodLogger()
    expect(screen.getByText('Very Low')).toBeInTheDocument()
    expect(screen.getByText('Very High')).toBeInTheDocument()
  })

  it('renders note textarea', () => {
    renderMoodLogger()
    expect(screen.getByPlaceholderText(/what's on your mind/i)).toBeInTheDocument()
  })

  it('has disabled submit when no mood selected', () => {
    renderMoodLogger()
    const submitBtn = screen.getByRole('button', { name: /log mood/i })
    expect(submitBtn).toBeDisabled()
  })

  it('enables submit after mood selection', async () => {
    const user = userEvent.setup()
    renderMoodLogger()

    await user.click(screen.getByText(/Focused/))
    const submitBtn = screen.getByRole('button', { name: /log mood/i })
    expect(submitBtn).not.toBeDisabled()
  })

  it('submits mood data via API', async () => {
    api.post.mockResolvedValue({
      data: { success: true, mood_log: { mood_type: 'focused', energy_level: 3 } }
    })
    const user = userEvent.setup()
    renderMoodLogger()

    await user.click(screen.getByText(/Focused/))
    await user.click(screen.getByRole('button', { name: /log mood/i }))

    await waitFor(() => {
      expect(api.post).toHaveBeenCalledWith(
        '/api/v1/mood/log-mood',
        expect.objectContaining({ mood_type: 'focused' })
      )
    })
  })

  it('calls onMoodLogged callback on success', async () => {
    api.post.mockResolvedValue({
      data: { success: true, mood_log: { mood_type: 'focused', energy_level: 3 } }
    })
    const user = userEvent.setup()
    renderMoodLogger()

    await user.click(screen.getByText(/Focused/))
    await user.click(screen.getByRole('button', { name: /log mood/i }))

    await waitFor(() => {
      expect(mockOnMoodLogged).toHaveBeenCalled()
    })
  })

  it('calls onClose when Cancel is clicked', async () => {
    const user = userEvent.setup()
    renderMoodLogger()

    await user.click(screen.getByText('Cancel'))
    expect(mockOnClose).toHaveBeenCalled()
  })

  it('calls onClose when X button is clicked', async () => {
    const user = userEvent.setup()
    renderMoodLogger()

    await user.click(screen.getByText('×'))
    expect(mockOnClose).toHaveBeenCalled()
  })

  it('shows character count for note', async () => {
    const user = userEvent.setup()
    renderMoodLogger()

    await user.type(screen.getByPlaceholderText(/what's on your mind/i), 'Hello')
    expect(screen.getByText('5/500')).toBeInTheDocument()
  })
})
