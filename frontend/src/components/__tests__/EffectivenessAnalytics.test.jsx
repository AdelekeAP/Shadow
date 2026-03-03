import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import EffectivenessAnalytics from '../EffectivenessAnalytics'

vi.mock('../../services/api', () => ({
  getEffectivenessSummary: vi.fn(),
  getEffectivenessByLearningStyle: vi.fn(),
  getEffectivenessOverTime: vi.fn(),
  getMoodEffectivenessCorrelation: vi.fn(),
  getTopicEffectiveness: vi.fn(),
  getStatisticalAnalysis: vi.fn(),
}))

vi.mock('victory', () => ({
  VictoryPie: ({ data }) => <div data-testid="victory-pie">{JSON.stringify(data)}</div>,
  VictoryChart: ({ children }) => <div data-testid="victory-chart">{children}</div>,
  VictoryBar: () => <div data-testid="victory-bar" />,
  VictoryAxis: () => <div data-testid="victory-axis" />,
  VictoryTheme: { material: {} },
  VictoryLine: () => <div data-testid="victory-line" />,
  VictoryArea: () => <div data-testid="victory-area" />
}))

import {
  getEffectivenessSummary,
  getEffectivenessByLearningStyle,
  getEffectivenessOverTime,
  getMoodEffectivenessCorrelation,
  getTopicEffectiveness,
  getStatisticalAnalysis,
} from '../../services/api'

const mockSummary = {
  summary: {
    total_study_plans: 5,
    active_study_plans: 2,
    completed_study_plans: 3,
    plans_with_improvement_data: 2,
    average_improvement: 12.5,
    positive_improvements: 2,
    total_conversations: 10,
    total_messages: 45,
  },
  engagement: {
    total_resources: 20,
    resources_clicked: 15,
    resources_completed: 8,
    engagement_rate: 75.0,
    completion_rate: 40.0,
    average_helpful_rating: 4.2,
    rated_resources_count: 6,
  },
}

const mockLearningStyleData = {
  by_learning_style: {
    visual: { plan_count: 3, avg_completion: 80 },
    reading: { plan_count: 2, avg_completion: 65 },
  },
  by_resource_type: {
    youtube_video: { total: 10, clicked: 8, engagement_rate: 80 },
    article: { total: 5, clicked: 3, engagement_rate: 60 },
  },
}

const mockTimeData = {
  study_plans_over_time: [
    { date: '2026-02-01', plans_created: 2 },
    { date: '2026-02-08', plans_created: 3 },
  ],
  engagement_over_time: [
    { date: '2026-02-01', resources_engaged: 5 },
    { date: '2026-02-08', resources_engaged: 8 },
  ],
}

const mockMoodData = {
  mood_distribution: {
    focused: { count: 5, avg_energy: 4.2 },
    stressed: { count: 3, avg_energy: 2.5 },
  },
  effectiveness_by_mood: {
    focused: { avg_improvement: 15.0 },
    stressed: { avg_improvement: -3.0 },
  },
}

const mockTopicData = {
  topics: [
    { topic: 'Binary Trees', plan_count: 2, completed_count: 1, avg_completion: 75 },
    { topic: 'Sorting Algorithms', plan_count: 3, completed_count: 2, avg_completion: 90 },
  ],
}

const mockStatsData = {
  sample_size: 5,
  paired_scores: [
    { topic: 'Binary Trees', before_score: 45, after_score: 72, improvement: 27 },
    { topic: 'Sorting', before_score: 50, after_score: 78, improvement: 28 },
  ],
  descriptive_statistics: {
    mean_improvement: 15.5,
    median_improvement: 14.0,
    std_improvement: 8.2,
    min_improvement: 3.0,
    max_improvement: 28.0,
  },
  inferential_statistics: {
    t_statistic: 4.23,
    p_value: 0.013,
    degrees_of_freedom: 4,
    cohens_d: 1.89,
    effect_size_interpretation: 'large',
    significant: true,
    confidence_interval_95: { lower: 5.2, upper: 25.8 },
  },
  sample_adequacy: { is_adequate: false, power_note: 'Sample size below 30' },
  interpretation: 'Students showed significant improvement (p=0.013) with a large effect size.',
}

const mockStatsEmpty = {
  sample_size: 0,
  paired_scores: [],
  descriptive_statistics: null,
  inferential_statistics: null,
  sample_adequacy: null,
  interpretation: null,
}

function mockAllAPIs() {
  getEffectivenessSummary.mockResolvedValue(mockSummary)
  getEffectivenessByLearningStyle.mockResolvedValue(mockLearningStyleData)
  getEffectivenessOverTime.mockResolvedValue(mockTimeData)
  getMoodEffectivenessCorrelation.mockResolvedValue(mockMoodData)
  getTopicEffectiveness.mockResolvedValue(mockTopicData)
  getStatisticalAnalysis.mockResolvedValue(mockStatsData)
}

describe('EffectivenessAnalytics', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders loading state initially', () => {
    // Make APIs hang so loading state persists
    getEffectivenessSummary.mockReturnValue(new Promise(() => {}))
    getEffectivenessByLearningStyle.mockReturnValue(new Promise(() => {}))
    getEffectivenessOverTime.mockReturnValue(new Promise(() => {}))
    getMoodEffectivenessCorrelation.mockReturnValue(new Promise(() => {}))
    getTopicEffectiveness.mockReturnValue(new Promise(() => {}))

    render(<EffectivenessAnalytics onClose={vi.fn()} />)
    expect(screen.getByText('Loading analytics...')).toBeInTheDocument()
  })

  it('calls all five API functions on mount', async () => {
    mockAllAPIs()
    render(<EffectivenessAnalytics onClose={vi.fn()} />)

    await waitFor(() => {
      expect(getEffectivenessSummary).toHaveBeenCalledTimes(1)
      expect(getEffectivenessByLearningStyle).toHaveBeenCalledTimes(1)
      expect(getEffectivenessOverTime).toHaveBeenCalledTimes(1)
      expect(getMoodEffectivenessCorrelation).toHaveBeenCalledTimes(1)
      expect(getTopicEffectiveness).toHaveBeenCalledTimes(1)
    })
  })

  it('renders overview tab with summary data after loading', async () => {
    mockAllAPIs()
    render(<EffectivenessAnalytics onClose={vi.fn()} />)

    await waitFor(() => {
      expect(screen.queryByText('Loading analytics...')).not.toBeInTheDocument()
    })

    // Check stat cards are rendered with correct values
    expect(screen.getByText('Study Plans')).toBeInTheDocument()
    expect(screen.getByText('5')).toBeInTheDocument()
    expect(screen.getByText('2 active')).toBeInTheDocument()
    expect(screen.getByText('+12.5%')).toBeInTheDocument()
    expect(screen.getByText('Engagement Rate')).toBeInTheDocument()
    expect(screen.getByText('15/20 clicked')).toBeInTheDocument()
    expect(screen.getByText('4.2/5')).toBeInTheDocument()
  })

  it('renders the header and tab buttons', async () => {
    mockAllAPIs()
    render(<EffectivenessAnalytics onClose={vi.fn()} />)

    await waitFor(() => {
      expect(screen.queryByText('Loading analytics...')).not.toBeInTheDocument()
    })

    expect(screen.getByText('SmartStudy Effectiveness')).toBeInTheDocument()
    expect(screen.getByText('Overview')).toBeInTheDocument()
    expect(screen.getByText('Learning Styles')).toBeInTheDocument()
    expect(screen.getByText('Trends')).toBeInTheDocument()
    expect(screen.getByText('Mood Impact')).toBeInTheDocument()
  })

  it('switches to Learning Styles tab when clicked', async () => {
    mockAllAPIs()
    const user = userEvent.setup()
    render(<EffectivenessAnalytics onClose={vi.fn()} />)

    await waitFor(() => {
      expect(screen.queryByText('Loading analytics...')).not.toBeInTheDocument()
    })

    await user.click(screen.getByText('Learning Styles'))

    expect(screen.getByText('Performance by Learning Style')).toBeInTheDocument()
    expect(screen.getByText('visual')).toBeInTheDocument()
    expect(screen.getByText('reading')).toBeInTheDocument()
  })

  it('switches to Trends tab and shows chart content', async () => {
    mockAllAPIs()
    const user = userEvent.setup()
    render(<EffectivenessAnalytics onClose={vi.fn()} />)

    await waitFor(() => {
      expect(screen.queryByText('Loading analytics...')).not.toBeInTheDocument()
    })

    await user.click(screen.getByText('Trends'))

    expect(screen.getByText('Study Activity Over Time (Last 30 Days)')).toBeInTheDocument()
    expect(screen.getByText('Resource Engagement Over Time')).toBeInTheDocument()
  })

  it('switches to Mood Impact tab and shows mood data', async () => {
    mockAllAPIs()
    const user = userEvent.setup()
    render(<EffectivenessAnalytics onClose={vi.fn()} />)

    await waitFor(() => {
      expect(screen.queryByText('Loading analytics...')).not.toBeInTheDocument()
    })

    await user.click(screen.getByText('Mood Impact'))

    expect(screen.getByText('Your Mood Distribution')).toBeInTheDocument()
    expect(screen.getByText('Study Effectiveness by Mood')).toBeInTheDocument()
    expect(screen.getByText('Mood Insights')).toBeInTheDocument()
  })

  it('renders error state when API call fails', async () => {
    getEffectivenessSummary.mockRejectedValue(new Error('Network error'))
    getEffectivenessByLearningStyle.mockRejectedValue(new Error('Network error'))
    getEffectivenessOverTime.mockRejectedValue(new Error('Network error'))
    getMoodEffectivenessCorrelation.mockRejectedValue(new Error('Network error'))
    getTopicEffectiveness.mockRejectedValue(new Error('Network error'))

    render(<EffectivenessAnalytics onClose={vi.fn()} />)

    await waitFor(() => {
      expect(screen.queryByText('Loading analytics...')).not.toBeInTheDocument()
    })

    expect(screen.getByText('Failed to load analytics data')).toBeInTheDocument()
  })

  it('calls onClose when close button in footer is clicked', async () => {
    mockAllAPIs()
    const onClose = vi.fn()
    const user = userEvent.setup()
    render(<EffectivenessAnalytics onClose={onClose} />)

    await waitFor(() => {
      expect(screen.queryByText('Loading analytics...')).not.toBeInTheDocument()
    })

    // Click the "Close" button in the footer
    await user.click(screen.getByText('Close'))
    expect(onClose).toHaveBeenCalledTimes(1)
  })

  it('displays topic effectiveness data on overview tab', async () => {
    mockAllAPIs()
    render(<EffectivenessAnalytics onClose={vi.fn()} />)

    await waitFor(() => {
      expect(screen.queryByText('Loading analytics...')).not.toBeInTheDocument()
    })

    expect(screen.getByText('Top Study Topics')).toBeInTheDocument()
    expect(screen.getByText('Binary Trees')).toBeInTheDocument()
    expect(screen.getByText('Sorting Algorithms')).toBeInTheDocument()
  })

  it('renders Research tab button', async () => {
    mockAllAPIs()
    render(<EffectivenessAnalytics onClose={vi.fn()} />)

    await waitFor(() => {
      expect(screen.queryByText('Loading analytics...')).not.toBeInTheDocument()
    })

    expect(screen.getByText('Research')).toBeInTheDocument()
  })

  it('shows statistical data when Research tab clicked', async () => {
    mockAllAPIs()
    const user = userEvent.setup()
    render(<EffectivenessAnalytics onClose={vi.fn()} />)

    await waitFor(() => {
      expect(screen.queryByText('Loading analytics...')).not.toBeInTheDocument()
    })

    await user.click(screen.getByText('Research'))

    await waitFor(() => {
      expect(screen.getByText('Sample Information')).toBeInTheDocument()
    })

    expect(screen.getByText('Descriptive Statistics')).toBeInTheDocument()
    expect(screen.getByText('Inferential Statistics')).toBeInTheDocument()
    expect(screen.getByText('15.50')).toBeInTheDocument()
    expect(screen.getByText('14.00')).toBeInTheDocument()
    expect(screen.getByText('More data needed')).toBeInTheDocument()
    expect(screen.getByText('Sample size below 30')).toBeInTheDocument()
  })

  it('shows empty state when sample_size is 0', async () => {
    mockAllAPIs()
    getStatisticalAnalysis.mockResolvedValue(mockStatsEmpty)
    const user = userEvent.setup()
    render(<EffectivenessAnalytics onClose={vi.fn()} />)

    await waitFor(() => {
      expect(screen.queryByText('Loading analytics...')).not.toBeInTheDocument()
    })

    await user.click(screen.getByText('Research'))

    await waitFor(() => {
      expect(screen.getByText(/Complete study plans with before\/after scores/)).toBeInTheDocument()
    })

    expect(screen.getByText(/You need at least 2 completed plans with scores/)).toBeInTheDocument()
  })

  it('displays interpretation text', async () => {
    mockAllAPIs()
    const user = userEvent.setup()
    render(<EffectivenessAnalytics onClose={vi.fn()} />)

    await waitFor(() => {
      expect(screen.queryByText('Loading analytics...')).not.toBeInTheDocument()
    })

    await user.click(screen.getByText('Research'))

    await waitFor(() => {
      expect(screen.getByText('Students showed significant improvement (p=0.013) with a large effect size.')).toBeInTheDocument()
    })
  })
})
