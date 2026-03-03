import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import StudyPlanDetails from '../studyplan/StudyPlanDetails'

// Mock the helper module to avoid issues with linkifyText returning arrays
vi.mock('../studyplan/studyPlanHelpers.jsx', () => ({
  linkifyText: (text) => text,
  getActivityIcon: () => '',
  getDifficultyColor: () => 'text-stone-600 bg-stone-50',
  getNotebookLMLink: () => '#',
}))

vi.mock('../studyplan/ResourceCard', () => ({
  default: () => <div data-testid="resource-card">Resource</div>,
}))

const basePlan = {
  id: 'plan-1',
  topic: 'Binary Search Trees',
  duration_days: 7,
  completion_percentage: 30,
  is_active: true,
  before_score: null,
  after_score: null,
  effectiveness_score: null,
  completed_days: [],
  resources: [],
  plan_data: {
    title: 'BST Study Plan',
    description: 'Learn BST operations',
    difficulty_level: 'intermediate',
    estimated_hours_total: '14 hours',
    learning_objectives: ['Understand BST structure'],
    days: [
      {
        day_number: 1,
        title: 'Introduction',
        focus: 'Basics',
        activities: [],
        success_criteria: 'Can explain BST',
      },
    ],
  },
}

const mockOnDayComplete = vi.fn()
const mockOnPlayVideo = vi.fn()
const mockOnSubmitBeforeScore = vi.fn()
const mockOnSubmitAfterScore = vi.fn()

function renderDetails(planOverrides = {}) {
  const plan = { ...basePlan, ...planOverrides }
  return render(
    <StudyPlanDetails
      plan={plan}
      onDayComplete={mockOnDayComplete}
      onPlayVideo={mockOnPlayVideo}
      onSubmitBeforeScore={mockOnSubmitBeforeScore}
      onSubmitAfterScore={mockOnSubmitAfterScore}
    />
  )
}

describe('StudyPlanDetails — Before/After Score UI', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  // ---------------------------------------------------------------
  // Before-score prompt
  // ---------------------------------------------------------------

  it('renders before-score prompt when before_score is null and plan is active', () => {
    renderDetails({ before_score: null, is_active: true })
    expect(screen.getByTestId('before-score-prompt')).toBeInTheDocument()
    expect(screen.getByText('Rate Your Current Knowledge')).toBeInTheDocument()
    expect(screen.getByText('Save Baseline Score')).toBeInTheDocument()
  })

  it('does NOT render before-score prompt when before_score is already set', () => {
    renderDetails({ before_score: 50, is_active: true })
    expect(screen.queryByTestId('before-score-prompt')).not.toBeInTheDocument()
  })

  it('does NOT render before-score prompt when plan is inactive', () => {
    renderDetails({ before_score: null, is_active: false })
    expect(screen.queryByTestId('before-score-prompt')).not.toBeInTheDocument()
  })

  it('calls onSubmitBeforeScore when Save Baseline Score is clicked', async () => {
    const user = userEvent.setup()
    renderDetails({ before_score: null, is_active: true })

    const input = screen.getByPlaceholderText('0-100')
    await user.type(input, '45')
    await user.click(screen.getByText('Save Baseline Score'))

    expect(mockOnSubmitBeforeScore).toHaveBeenCalledWith(45)
  })

  // ---------------------------------------------------------------
  // After-score prompt
  // ---------------------------------------------------------------

  it('renders after-score prompt when completion is 100% and after_score is null', () => {
    renderDetails({ completion_percentage: 100, after_score: null })
    expect(screen.getByTestId('after-score-prompt')).toBeInTheDocument()
    expect(screen.getByText('Plan Complete! Rate Your Progress')).toBeInTheDocument()
    expect(screen.getByText('Submit Final Score')).toBeInTheDocument()
  })

  it('does NOT render after-score prompt when completion is below 100%', () => {
    renderDetails({ completion_percentage: 50, after_score: null })
    expect(screen.queryByTestId('after-score-prompt')).not.toBeInTheDocument()
  })

  it('does NOT render after-score prompt when after_score is already set', () => {
    renderDetails({ completion_percentage: 100, after_score: 85 })
    expect(screen.queryByTestId('after-score-prompt')).not.toBeInTheDocument()
  })

  it('calls onSubmitAfterScore when Submit Final Score is clicked', async () => {
    const user = userEvent.setup()
    renderDetails({ completion_percentage: 100, after_score: null })

    // There may be two inputs on the page (before + after), get the right one
    const inputs = screen.getAllByPlaceholderText('0-100')
    const afterInput = inputs[inputs.length - 1]
    await user.type(afterInput, '82')
    await user.click(screen.getByText('Submit Final Score'))

    expect(mockOnSubmitAfterScore).toHaveBeenCalledWith(82)
  })

  // ---------------------------------------------------------------
  // Results badge (improvement)
  // ---------------------------------------------------------------

  it('shows improvement badge when both scores exist', () => {
    renderDetails({ before_score: 40, after_score: 75 })
    expect(screen.getByTestId('score-results-badge')).toBeInTheDocument()
    expect(screen.getByText('Knowledge Improvement')).toBeInTheDocument()
    // Improvement = 75 - 40 = 35.0
    expect(screen.getByText('+35.0%')).toBeInTheDocument()
  })

  it('shows negative improvement in red when after_score < before_score', () => {
    renderDetails({ before_score: 70, after_score: 50 })
    expect(screen.getByTestId('score-results-badge')).toBeInTheDocument()
    // Improvement = 50 - 70 = -20.0
    expect(screen.getByText('-20.0%')).toBeInTheDocument()
  })

  it('does NOT show results badge when only before_score is set', () => {
    renderDetails({ before_score: 50, after_score: null })
    expect(screen.queryByTestId('score-results-badge')).not.toBeInTheDocument()
  })
})
