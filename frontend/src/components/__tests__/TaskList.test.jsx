import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { describe, it, expect, vi, beforeEach } from 'vitest'

// Mock API module
vi.mock('../../services/api', () => ({
  default: {},
  completeTask: vi.fn(),
  deleteTask: vi.fn(),
  updateTask: vi.fn(),
}))

// Mock EditTaskModal to avoid deep dependency chain
vi.mock('../EditTaskModal', () => ({
  default: ({ isOpen }) => isOpen ? <div data-testid="edit-task-modal">Edit Modal</div> : null,
}))

import TaskList from '../TaskList'

const makeTasks = (overrides = []) => overrides

const baseTask = (id, overrides = {}) => ({
  id,
  title: `Task ${id}`,
  task_type: 'assignment',
  category: 'CA',
  weight: 10,
  max_marks: 10,
  is_completed: false,
  is_urgent: false,
  due_date: null,
  priority_score: null,
  earned_marks: null,
  course_code: 'CSC101',
  description: null,
  ...overrides,
})

function renderTaskList(props = {}) {
  return render(
    <MemoryRouter>
      <TaskList tasks={[]} onUpdate={vi.fn()} {...props} />
    </MemoryRouter>
  )
}

describe('TaskList', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders empty state when no tasks provided', () => {
    renderTaskList({ tasks: [] })
    expect(screen.getByText(/no tasks yet/i)).toBeInTheDocument()
    expect(screen.getByText(/create a task to get started/i)).toBeInTheDocument()
  })

  it('renders task items with their titles', () => {
    const tasks = [
      baseTask(1, { title: 'Data Structures Assignment' }),
      baseTask(2, { title: 'Machine Learning Quiz' }),
    ]
    renderTaskList({ tasks })
    expect(screen.getByText('Data Structures Assignment')).toBeInTheDocument()
    expect(screen.getByText('Machine Learning Quiz')).toBeInTheDocument()
  })

  it('renders filter tabs when tasks are present', () => {
    const tasks = [baseTask(1)]
    renderTaskList({ tasks })
    expect(screen.getByRole('button', { name: /all/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /pending/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /urgent/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /done/i })).toBeInTheDocument()
  })

  it('shows completed tasks with strikethrough styling', () => {
    const tasks = [
      baseTask(1, { title: 'Completed Task', is_completed: true, earned_marks: 8, max_marks: 10 }),
    ]
    renderTaskList({ tasks })
    const titleEl = screen.getByText('Completed Task')
    expect(titleEl.className).toMatch(/line-through/)
  })

  it('shows footer summary with completion count when tasks present', () => {
    const tasks = [
      baseTask(1, { is_completed: true }),
      baseTask(2, { is_completed: false }),
    ]
    renderTaskList({ tasks })
    // Footer shows "X of Y done"
    expect(screen.getByText(/of 2 done/i)).toBeInTheDocument()
  })

  it('filters to show only pending tasks when Pending tab is clicked', async () => {
    const user = userEvent.setup()
    const tasks = [
      baseTask(1, { title: 'Pending Task', is_completed: false }),
      baseTask(2, { title: 'Done Task', is_completed: true }),
    ]
    renderTaskList({ tasks })

    await user.click(screen.getByRole('button', { name: /pending/i }))

    expect(screen.getByText('Pending Task')).toBeInTheDocument()
    // Completed task should not match the pending filter
    expect(screen.queryByText('Done Task')).not.toBeInTheDocument()
  })
})
