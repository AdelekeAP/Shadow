import { useState } from 'react'
import { completeTask, deleteTask } from '../services/api'
import EditTaskModal from './EditTaskModal'

/**
 * TaskItem Component
 * Individual task card with completion and delete actions
 */
const TaskItem = ({ task, onUpdate, onDelete, onEdit }) => {
  const [isLoading, setIsLoading] = useState(false)
  const [showMarkInput, setShowMarkInput] = useState(false)
  const [earnedMarks, setEarnedMarks] = useState('')
  const [showEditMarks, setShowEditMarks] = useState(false)

  const handleComplete = async () => {
    if (!showMarkInput) {
      setShowMarkInput(true)
      return
    }

    setIsLoading(true)
    try {
      const completionData = {}
      if (earnedMarks) {
        completionData.earned_marks = parseFloat(earnedMarks)
      }

      await completeTask(task.id, completionData)
      onUpdate()
      setShowMarkInput(false)
      setEarnedMarks('')
    } catch (error) {
      console.error('Error completing task:', error)
      alert(error.detail || 'Failed to complete task')
    } finally {
      setIsLoading(false)
    }
  }

  const handleUncomplete = async () => {
    if (!confirm('Mark this task as incomplete? This will remove completion status and earned marks.')) return

    setIsLoading(true)
    try {
      const { updateTask } = await import('../services/api')
      await updateTask(task.id, {
        is_completed: false,
        completed_at: null,
        earned_marks: null,
        is_late: false
      })
      onUpdate()
    } catch (error) {
      console.error('Error uncompleting task:', error)
      alert(error.detail || 'Failed to uncomplete task')
    } finally {
      setIsLoading(false)
    }
  }

  const handleUpdateMarks = async () => {
    setIsLoading(true)
    try {
      const { updateTask } = await import('../services/api')
      const updateData = {}
      if (earnedMarks) {
        updateData.earned_marks = parseFloat(earnedMarks)
      }

      await updateTask(task.id, updateData)
      onUpdate()
      setShowEditMarks(false)
      setEarnedMarks('')
    } catch (error) {
      console.error('Error updating marks:', error)
      alert(error.detail || 'Failed to update marks')
    } finally {
      setIsLoading(false)
    }
  }

  const handleDelete = async () => {
    if (!confirm('Are you sure you want to delete this task?')) return

    setIsLoading(true)
    try {
      await deleteTask(task.id)
      onDelete(task.id)
    } catch (error) {
      console.error('Error deleting task:', error)
      alert(error.detail || 'Failed to delete task')
    } finally {
      setIsLoading(false)
    }
  }

  const getTaskTypeColor = () => {
    const colors = {
      test: 'bg-navy-100 text-navy-800',
      project: 'bg-blue-100 text-blue-800',
      assignment: 'bg-green-100 text-green-800',
      exam: 'bg-red-100 text-red-800',
      participation: 'bg-yellow-100 text-yellow-800',
      quiz: 'bg-pink-100 text-pink-800',
      presentation: 'bg-navy-100 text-navy-800',
      other: 'bg-stone-100 text-stone-800'
    }
    return colors[task.task_type] || colors.other
  }

  const formatDate = (dateString) => {
    if (!dateString) return null
    const date = new Date(dateString)
    const today = new Date()
    const tomorrow = new Date(today)
    tomorrow.setDate(tomorrow.getDate() + 1)

    if (date.toDateString() === today.toDateString()) return 'Today'
    if (date.toDateString() === tomorrow.toDateString()) return 'Tomorrow'

    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: date.getFullYear() !== today.getFullYear() ? 'numeric' : undefined
    })
  }

  const isOverdue = task.due_date && !task.is_completed && new Date(task.due_date) < new Date()
  const isDueSoon = task.due_date && !task.is_completed && new Date(task.due_date) <= new Date(Date.now() + 3 * 24 * 60 * 60 * 1000)

  return (
    <div
      data-task-id={task.id}
      className={`
      relative bg-white rounded-xl p-4 transition-all duration-200
      ${task.is_completed
        ? 'bg-stone-50 border border-stone-200'
        : 'border border-stone-200 shadow-sm hover:shadow-md hover:border-stone-300'
      }
      ${isOverdue ? 'border-l-4 border-l-red-500 bg-red-50/30' : ''}
      ${task.is_urgent && !task.is_completed && !isOverdue ? 'border-l-4 border-l-amber-500 bg-amber-50/30' : ''}
    `}>
      <div className="flex items-start justify-between">
        {/* Left side - Task info */}
        <div className="flex items-start space-x-3 flex-1">
          {/* Checkbox */}
          <button
            onClick={task.is_completed ? handleUncomplete : handleComplete}
            disabled={isLoading}
            className={`
              mt-0.5 w-6 h-6 rounded-full border-2 flex items-center justify-center transition-all duration-200
              ${task.is_completed
                ? 'bg-green-500 border-green-500 hover:bg-green-600 shadow-sm'
                : 'border-stone-300 hover:border-navy-500 hover:bg-navy-50'
              }
              ${isLoading ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
            `}
            title={task.is_completed ? 'Click to mark as incomplete' : 'Click to complete'}
          >
            {task.is_completed && (
              <svg className="w-3.5 h-3.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
              </svg>
            )}
          </button>

          {/* Task details */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1.5 flex-wrap">
              <h4 className={`font-semibold text-stone-900 ${task.is_completed ? 'line-through text-stone-500' : ''}`}>
                {task.title}
              </h4>
              {task.course_code && (
                <span
                  className="px-2 py-0.5 text-xs font-medium rounded-full bg-navy-100 text-navy-800 cursor-help"
                  title={task.course_title || task.course_code}
                >
                  {task.course_code}
                </span>
              )}
              <span className={`px-2 py-0.5 text-xs font-medium rounded-full ${getTaskTypeColor()}`}>
                {task.task_type}
              </span>
              {task.category === 'CA' && (
                <span className="px-2 py-0.5 text-xs font-medium rounded-full bg-blue-50 text-blue-700">
                  CA
                </span>
              )}
            </div>

            {task.description && (
              <p className="text-sm text-stone-600 mb-2">{task.description}</p>
            )}

            <div className="flex flex-wrap items-center gap-3 text-xs text-stone-500">
              {/* Weight */}
              <div className="flex items-center">
                <span className="font-medium text-stone-700">{task.weight} marks</span>
                {task.is_completed && task.earned_marks !== null && (
                  <>
                    <span className="ml-1 text-green-600 font-medium">
                      ({task.earned_marks}/{task.max_marks})
                    </span>
                    <button
                      onClick={() => {
                        setEarnedMarks(task.earned_marks.toString())
                        setShowEditMarks(true)
                      }}
                      className="ml-1 text-stone-400 hover:text-navy-800 transition-colors"
                      title="Edit earned marks"
                    >
                      <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                      </svg>
                    </button>
                  </>
                )}
              </div>

              {/* Due date */}
              {task.due_date && (
                <div className={`flex items-center ${isOverdue ? 'text-red-600 font-medium' : isDueSoon ? 'text-yellow-600 font-medium' : ''}`}>
                  <svg className="w-4 h-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                  {formatDate(task.due_date)}
                  {isOverdue && ' (Overdue)'}
                </div>
              )}

              {/* Priority score */}
              {task.priority_score && (
                <div className="flex items-center">
                  <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                    task.priority_score >= 70 ? 'bg-red-100 text-red-700' :
                    task.priority_score >= 50 ? 'bg-yellow-100 text-yellow-700' :
                    'bg-green-100 text-green-700'
                  }`}>
                    Priority: {Math.round(task.priority_score)}
                  </span>
                </div>
              )}
            </div>

            {/* Mark input (when completing) */}
            {showMarkInput && !task.is_completed && (
              <div className="mt-3 flex items-center space-x-2">
                <input
                  type="number"
                  min="0"
                  max={task.max_marks}
                  step="0.5"
                  value={earnedMarks}
                  onChange={(e) => setEarnedMarks(e.target.value)}
                  placeholder={`Marks earned (max ${task.max_marks})`}
                  className="px-3 py-1 border border-stone-300 rounded text-sm focus:ring-2 focus:ring-navy-500 focus:border-navy-500"
                  autoFocus
                />
                <button
                  onClick={handleComplete}
                  disabled={isLoading}
                  className="px-3 py-1 bg-green-600 text-white text-sm rounded hover:bg-green-700 disabled:opacity-50"
                >
                  {isLoading ? 'Saving...' : 'Save'}
                </button>
                <button
                  onClick={() => setShowMarkInput(false)}
                  className="px-3 py-1 bg-stone-200 text-stone-700 text-sm rounded hover:bg-stone-300"
                >
                  Cancel
                </button>
              </div>
            )}

            {/* Edit marks (when task is completed) */}
            {showEditMarks && task.is_completed && (
              <div className="mt-3 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                <p className="text-xs text-blue-700 mb-2">Edit earned marks for this completed task</p>
                <div className="flex items-center space-x-2">
                  <input
                    type="number"
                    min="0"
                    max={task.max_marks}
                    step="0.5"
                    value={earnedMarks}
                    onChange={(e) => setEarnedMarks(e.target.value)}
                    placeholder={`Marks earned (max ${task.max_marks})`}
                    className="px-3 py-1 border border-stone-300 rounded text-sm focus:ring-2 focus:ring-navy-500 focus:border-navy-500"
                    autoFocus
                  />
                  <button
                    onClick={handleUpdateMarks}
                    disabled={isLoading}
                    className="px-3 py-1 bg-navy-800 text-white text-sm rounded hover:bg-navy-900 disabled:opacity-50"
                  >
                    {isLoading ? 'Updating...' : 'Update'}
                  </button>
                  <button
                    onClick={() => {
                      setShowEditMarks(false)
                      setEarnedMarks('')
                    }}
                    className="px-3 py-1 bg-stone-200 text-stone-700 text-sm rounded hover:bg-stone-300"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Right side - Action buttons */}
        <div className="flex items-center space-x-1 ml-2">
          {/* Edit button */}
          <button
            onClick={() => onEdit(task)}
            disabled={isLoading}
            className="p-1 text-stone-400 hover:text-navy-800 transition-colors"
            title="Edit task"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
            </svg>
          </button>

          {/* Delete button */}
          <button
            onClick={handleDelete}
            disabled={isLoading}
            className="p-1 text-stone-400 hover:text-red-600 transition-colors"
            title="Delete task"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  )
}

/**
 * TaskList Component
 * Displays a list of tasks with filtering and grouping options
 */
const TaskList = ({ tasks, onUpdate, showCompleted = true, groupByCourse = false, enrolledCourses = [] }) => {
  const [filter, setFilter] = useState('all') // all, pending, completed, urgent
  const [editingTask, setEditingTask] = useState(null)

  const isTaskOverdue = (task) => task.due_date && !task.is_completed && new Date(task.due_date) < new Date()

  const filteredTasks = tasks.filter(task => {
    if (filter === 'pending') return !task.is_completed
    if (filter === 'completed') return task.is_completed
    if (filter === 'urgent') return (task.is_urgent || isTaskOverdue(task)) && !task.is_completed
    return showCompleted || !task.is_completed
  })

  const sortedTasks = [...filteredTasks].sort((a, b) => {
    // Completed tasks go to bottom
    if (a.is_completed !== b.is_completed) {
      return a.is_completed ? 1 : -1
    }
    // Then sort by priority (high to low)
    if (b.priority_score !== a.priority_score) {
      return (b.priority_score || 0) - (a.priority_score || 0)
    }
    // Then by due date (earliest first)
    if (a.due_date && b.due_date) {
      return new Date(a.due_date) - new Date(b.due_date)
    }
    return 0
  })

  const handleTaskDelete = (taskId) => {
    onUpdate() // Refresh the task list
  }

  const handleTaskEdit = (task) => {
    setEditingTask(task)
  }

  const handleCloseEditModal = () => {
    setEditingTask(null)
  }

  const handleTaskUpdated = () => {
    setEditingTask(null)
    onUpdate() // Refresh the task list
  }

  if (tasks.length === 0) {
    return (
      <div className="text-center py-12 bg-stone-50 rounded-lg">
        <svg className="mx-auto h-12 w-12 text-stone-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
        </svg>
        <h3 className="mt-2 text-sm font-medium text-stone-900">No tasks</h3>
        <p className="mt-1 text-sm text-stone-500">Get started by creating a new task</p>
      </div>
    )
  }

  return (
    <div>
      {/* Filter tabs */}
      <div className="flex gap-1 mb-5 p-1 bg-stone-100 rounded-lg w-fit">
        {[
          { key: 'all', label: 'All' },
          { key: 'pending', label: 'Pending' },
          { key: 'urgent', label: 'Urgent' },
          { key: 'completed', label: 'Done' }
        ].map(({ key, label }) => (
          <button
            key={key}
            onClick={() => setFilter(key)}
            className={`
              px-4 py-2 text-sm font-medium rounded-md transition-all duration-200
              ${filter === key
                ? 'bg-white text-navy-800 shadow-sm'
                : 'text-stone-600 hover:text-stone-900 hover:bg-stone-50'
              }
            `}
          >
            {label}
            {key === 'pending' && tasks.filter(t => !t.is_completed).length > 0 && (
              <span className="ml-1.5 px-1.5 py-0.5 text-xs rounded-full bg-navy-100 text-navy-700">
                {tasks.filter(t => !t.is_completed).length}
              </span>
            )}
            {key === 'urgent' && tasks.filter(t => (t.is_urgent || isTaskOverdue(t)) && !t.is_completed).length > 0 && (
              <span className="ml-1.5 px-1.5 py-0.5 text-xs rounded-full bg-red-100 text-red-700">
                {tasks.filter(t => (t.is_urgent || isTaskOverdue(t)) && !t.is_completed).length}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Task list */}
      <div className="space-y-3">
        {sortedTasks.length === 0 ? (
          <p className="text-center text-stone-500 py-8">No tasks match this filter</p>
        ) : (
          sortedTasks.map(task => (
            <TaskItem
              key={task.id}
              task={task}
              onUpdate={onUpdate}
              onDelete={handleTaskDelete}
              onEdit={handleTaskEdit}
            />
          ))
        )}
      </div>

      {/* Summary */}
      {sortedTasks.length > 0 && (
        <div className="mt-4 pt-4 border-t border-stone-200">
          <div className="flex justify-between text-sm text-stone-600">
            <span>
              {tasks.filter(t => t.is_completed).length} of {tasks.length} tasks completed
            </span>
            <span>
              {tasks.filter(t => !t.is_completed && t.category === 'CA').reduce((sum, t) => sum + (t.weight || 0), 0).toFixed(1)} CA marks remaining
            </span>
          </div>
        </div>
      )}

      {/* Edit Task Modal */}
      <EditTaskModal
        isOpen={editingTask !== null}
        onClose={handleCloseEditModal}
        onTaskUpdated={handleTaskUpdated}
        task={editingTask}
        enrolledCourses={enrolledCourses}
      />
    </div>
  )
}

export default TaskList
