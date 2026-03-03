import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import StudyPlanView from '../StudyPlanView'

vi.mock('../../services/api', () => ({
  generateStudyPlan: vi.fn(),
  getStudyPlans: vi.fn(),
  updateStudyPlanProgress: vi.fn(),
  markResourceComplete: vi.fn(),
  getEnrolledCourses: vi.fn(),
  browseLibrary: vi.fn(),
  createVideoNote: vi.fn(),
  getVideoNotes: vi.fn(),
  deleteVideoNote: vi.fn(),
}))

vi.mock('../YouTubePlayer', () => ({
  default: () => <div data-testid="youtube-player">Player</div>,
}))

import { getStudyPlans, getEnrolledCourses, browseLibrary } from '../../services/api'

const mockPlans = [
  {
    id: 'plan1',
    topic: 'Binary Search Trees',
    difficulty_level: 'intermediate',
    duration_days: 7,
    is_active: true,
    completion_percentage: 30,
    created_at: new Date().toISOString(),
    study_plan_content: {
      title: 'Binary Search Trees Study Plan',
      description: 'Master BST operations',
      learning_objectives: ['Understand BST structure', 'Implement insert/delete'],
      days: [
        {
          day: 1,
          title: 'Introduction to BSTs',
          focus: 'Understanding tree structures',
          activities: [],
          resources_needed: [],
          success_criteria: 'Can explain BST properties',
        }
      ],
    },
    resources: [
      {
        id: 'r1',
        title: 'BST Tutorial',
        resource_type: 'youtube_video',
        url: 'https://youtube.com/watch?v=test',
        is_completed: false,
        quality_score: 8.5,
      }
    ],
  },
]

describe('StudyPlanView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    getStudyPlans.mockResolvedValue(mockPlans)
    getEnrolledCourses.mockResolvedValue([])
    browseLibrary.mockResolvedValue({ documents: [] })
  })

  it('renders study plans title', async () => {
    render(<StudyPlanView onClose={vi.fn()} />)
    await waitFor(() => {
      expect(screen.getByText(/study plan/i)).toBeInTheDocument()
    })
  })

  it('loads study plans on mount', async () => {
    render(<StudyPlanView onClose={vi.fn()} />)
    await waitFor(() => {
      expect(getStudyPlans).toHaveBeenCalled()
    })
  })

  it('displays plan topic', async () => {
    render(<StudyPlanView onClose={vi.fn()} />)
    await waitFor(() => {
      // Topic appears in both sidebar and main view
      expect(screen.getAllByText(/Binary Search Trees/).length).toBeGreaterThan(0)
    }, { timeout: 3000 })
  })

  it('shows New Plan button', async () => {
    render(<StudyPlanView onClose={vi.fn()} />)
    // Wait for loading to finish
    await waitFor(() => {
      expect(screen.queryByText(/loading/i)).not.toBeInTheDocument()
    }, { timeout: 3000 })
    // The "New Plan" or "+ New" button should appear
    const newPlanBtn = screen.queryByText(/new plan/i) || screen.queryByText(/\+ new/i)
    expect(newPlanBtn).toBeInTheDocument()
  })

  it('shows empty state when no plans exist', async () => {
    getStudyPlans.mockResolvedValue([])
    render(<StudyPlanView onClose={vi.fn()} />)

    await waitFor(() => {
      const text = document.body.textContent.toLowerCase()
      expect(text).toMatch(/no.*plan|create.*first|get started|generate/i)
    }, { timeout: 3000 })
  })
})
