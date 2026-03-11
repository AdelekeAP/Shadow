import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('../../../services/api', () => ({
  submitQuiz: vi.fn(),
}))

import QuizPlayer from '../QuizPlayer'

// Quiz with a single MCQ so shuffle order doesn't matter
const singleMCQ = {
  id: 'quiz-mcq',
  title: 'MCQ Quiz',
  topic: 'Data Structures',
  time_limit_minutes: null,
  questions: [
    {
      id: 'q1',
      question: 'What is a binary search tree?',
      type: 'multiple_choice',
      options: ['A linear structure', 'A tree with ordered nodes', 'A hash map', 'A linked list'],
      difficulty: 'intermediate',
      topic_tag: 'Trees',
    },
  ],
}

// Multi-question quiz for progress/navigation tests
const multiQuiz = {
  id: 'quiz-multi',
  title: 'Mixed Quiz',
  topic: 'Algorithms',
  time_limit_minutes: null,
  questions: [
    {
      id: 'q1',
      question: 'First question',
      type: 'short_answer',
      options: null,
      difficulty: 'beginner',
      topic_tag: null,
    },
    {
      id: 'q2',
      question: 'Second question',
      type: 'short_answer',
      options: null,
      difficulty: 'intermediate',
      topic_tag: null,
    },
    {
      id: 'q3',
      question: 'Third question',
      type: 'short_answer',
      options: null,
      difficulty: 'advanced',
      topic_tag: null,
    },
  ],
}

function renderQuiz(quiz, callbacks = {}) {
  return render(
    <QuizPlayer
      quiz={quiz}
      onComplete={callbacks.onComplete || vi.fn()}
      onCancel={callbacks.onCancel || vi.fn()}
    />
  )
}

async function clickStart() {
  const user = userEvent.setup()
  await user.click(screen.getByRole('button', { name: /start quiz/i }))
  return user
}

describe('QuizPlayer', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders the ready screen before quiz starts', () => {
    renderQuiz(singleMCQ)
    expect(screen.getByRole('button', { name: /start quiz/i })).toBeInTheDocument()
    expect(screen.getByText(/ready to begin/i)).toBeInTheDocument()
  })

  it('shows question count on the ready screen', () => {
    renderQuiz(multiQuiz)
    expect(screen.getByText(/3 questions/i)).toBeInTheDocument()
  })

  it('renders the MCQ question after starting', async () => {
    renderQuiz(singleMCQ)
    await clickStart()
    expect(screen.getByText('What is a binary search tree?')).toBeInTheDocument()
  })

  it('shows answer options for multiple choice question', async () => {
    renderQuiz(singleMCQ)
    await clickStart()
    expect(screen.getByText('A linear structure')).toBeInTheDocument()
    expect(screen.getByText('A tree with ordered nodes')).toBeInTheDocument()
    expect(screen.getByText('A hash map')).toBeInTheDocument()
    expect(screen.getByText('A linked list')).toBeInTheDocument()
  })

  it('shows progress indicator (question X of Y)', async () => {
    renderQuiz(multiQuiz)
    await clickStart()
    expect(screen.getByText(/question 1 of 3/i)).toBeInTheDocument()
  })

  it('allows selecting a multiple choice answer', async () => {
    renderQuiz(singleMCQ)
    const user = await clickStart()
    const option = screen.getByText('A tree with ordered nodes')
    await user.click(option)
    // The button wrapping this option should now have the selected (dark) style
    const btn = option.closest('button')
    expect(btn.className).toMatch(/bg-navy-800/)
  })
})
