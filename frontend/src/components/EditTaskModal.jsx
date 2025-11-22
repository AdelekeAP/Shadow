import { useState, useEffect } from 'react'
import { updateTask } from '../services/api'

/**
 * EditTaskModal Component
 * Modal for editing existing tasks
 */
const EditTaskModal = ({ isOpen, onClose, onTaskUpdated, task, enrolledCourses }) => {
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    task_type: 'assignment',
    weight: '',
    category: 'CA',
    due_date: '',
    effort_estimate: ''
  })

  const [errors, setErrors] = useState({})
  const [isSubmitting, setIsSubmitting] = useState(false)

  // Populate form when task changes
  useEffect(() => {
    if (task && isOpen) {
      setFormData({
        title: task.title || '',
        description: task.description || '',
        task_type: task.task_type || 'assignment',
        weight: task.weight || '',
        category: task.category || 'CA',
        due_date: task.due_date ? new Date(task.due_date).toISOString().slice(0, 16) : '',
        effort_estimate: task.effort_estimate || ''
      })
      setErrors({})
    }
  }, [task, isOpen])

  const taskTypes = [
    { value: 'test', label: 'Test/Quiz', description: 'Typically 10-15 marks' },
    { value: 'project', label: 'Project', description: 'Usually 15-20 marks' },
    { value: 'assignment', label: 'Assignment', description: 'Varies 5-15 marks' },
    { value: 'participation', label: 'Participation', description: 'Usually 5 marks' },
    { value: 'presentation', label: 'Presentation', description: 'Varies' },
    { value: 'quiz', label: 'Quiz', description: 'Small assessments' },
    { value: 'exam', label: 'Exam', description: 'Final examination' },
    { value: 'other', label: 'Other', description: 'Custom task type' }
  ]

  const validateForm = () => {
    const newErrors = {}

    if (!formData.title.trim()) {
      newErrors.title = 'Task title is required'
    }
    if (!formData.weight || parseFloat(formData.weight) <= 0) {
      newErrors.weight = 'Weight must be greater than 0'
    }

    // Validate weight based on category
    const weight = parseFloat(formData.weight)
    if (formData.category === 'CA' && weight > 30) {
      newErrors.weight = 'CA tasks cannot exceed 30 marks (5 marks reserved for participation)'
    } else if (formData.category === 'EXAM' && weight > 65) {
      newErrors.weight = 'EXAM tasks cannot exceed 65 marks'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: value
    }))
    // Clear error for this field
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: null }))
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()

    if (!validateForm()) {
      return
    }

    setIsSubmitting(true)

    try {
      // Prepare data for API
      const taskData = {
        title: formData.title.trim(),
        description: formData.description.trim() || null,
        task_type: formData.task_type,
        weight: parseFloat(formData.weight),
        category: formData.category,
        due_date: formData.due_date || null,
        effort_estimate: formData.effort_estimate ? parseInt(formData.effort_estimate) : null
      }

      await updateTask(task.id, taskData)
      onTaskUpdated()
      onClose()
    } catch (error) {
      console.error('Error updating task:', error)

      // Handle validation errors
      let errorMessage = 'Failed to update task. Please try again.'
      if (error.detail) {
        if (Array.isArray(error.detail)) {
          errorMessage = error.detail.map(err => err.msg).join(', ')
        } else if (typeof error.detail === 'string') {
          errorMessage = error.detail
        }
      }

      setErrors({
        submit: errorMessage
      })
    } finally {
      setIsSubmitting(false)
    }
  }

  if (!isOpen || !task) return null

  // Get course info for display
  const currentCourse = enrolledCourses.find(uc => uc.id === task.user_course_id)

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-stone-900/40 backdrop-blur-sm transition-opacity"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="flex min-h-screen items-center justify-center p-4">
        <div className="relative bg-white rounded-2xl shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto animate-scale-in">
          {/* Header */}
          <div className="sticky top-0 bg-gradient-to-r from-navy-800 to-navy-900 px-6 py-5 flex items-center justify-between rounded-t-2xl">
            <div>
              <h2 className="text-xl font-bold text-white">Edit Task</h2>
              {currentCourse && (
                <p className="text-sm text-white/70 mt-0.5">
                  {currentCourse.course?.code} - {currentCourse.course?.title}
                </p>
              )}
            </div>
            <button
              onClick={onClose}
              className="text-white/70 hover:text-white transition-colors p-1 hover:bg-white/10 rounded-lg"
            >
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="p-6 space-y-5">
            {/* Task Title */}
            <div>
              <label htmlFor="title" className="block text-sm font-medium text-stone-700 mb-2">
                Task Title <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                id="title"
                name="title"
                value={formData.title}
                onChange={handleChange}
                placeholder="e.g., Test 1, Project Submission, Assignment 2"
                className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-navy-500 focus:border-navy-500 ${
                  errors.title ? 'border-red-500' : 'border-stone-300'
                }`}
              />
              {errors.title && (
                <p className="mt-1 text-sm text-red-600">{errors.title}</p>
              )}
            </div>

            {/* Task Type */}
            <div>
              <label htmlFor="task_type" className="block text-sm font-medium text-stone-700 mb-2">
                Task Type <span className="text-red-500">*</span>
              </label>
              <select
                id="task_type"
                name="task_type"
                value={formData.task_type}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-stone-300 rounded-lg focus:ring-2 focus:ring-navy-500 focus:border-navy-500"
              >
                {taskTypes.map(type => (
                  <option key={type.value} value={type.value}>
                    {type.label} - {type.description}
                  </option>
                ))}
              </select>
            </div>

            {/* Weight and Category */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label htmlFor="weight" className="block text-sm font-medium text-stone-700 mb-2">
                  Weight (Marks) <span className="text-red-500">*</span>
                </label>
                <input
                  type="number"
                  id="weight"
                  name="weight"
                  value={formData.weight}
                  onChange={handleChange}
                  min="0"
                  max={formData.category === 'CA' ? '30' : '65'}
                  step="0.5"
                  placeholder={formData.category === 'CA' ? 'e.g., 15 (max 30)' : 'e.g., 40 (max 65)'}
                  className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-navy-500 focus:border-navy-500 ${
                    errors.weight ? 'border-red-500' : 'border-stone-300'
                  }`}
                />
                {errors.weight && (
                  <p className="mt-1 text-sm text-red-600">{errors.weight}</p>
                )}
              </div>

              <div>
                <label htmlFor="category" className="block text-sm font-medium text-stone-700 mb-2">
                  Category
                </label>
                <select
                  id="category"
                  name="category"
                  value={formData.category}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-stone-300 rounded-lg focus:ring-2 focus:ring-navy-500 focus:border-navy-500"
                >
                  <option value="CA">CA (Continuous Assessment)</option>
                  <option value="EXAM">EXAM (Final Examination)</option>
                </select>
                <p className="mt-1 text-xs text-stone-500">
                  {formData.category === 'CA'
                    ? 'CA max: 30 marks (5 marks reserved for participation at lecturer discretion)'
                    : 'EXAM max: 65 marks (projects, major assessments, final exam)'}
                </p>
              </div>
            </div>

            {/* Due Date and Effort */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label htmlFor="due_date" className="block text-sm font-medium text-stone-700 mb-2">
                  Due Date
                </label>
                <input
                  type="datetime-local"
                  id="due_date"
                  name="due_date"
                  value={formData.due_date}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-stone-300 rounded-lg focus:ring-2 focus:ring-navy-500 focus:border-navy-500"
                />
              </div>

              <div>
                <label htmlFor="effort_estimate" className="block text-sm font-medium text-stone-700 mb-2">
                  Effort Estimate (minutes)
                </label>
                <input
                  type="number"
                  id="effort_estimate"
                  name="effort_estimate"
                  value={formData.effort_estimate}
                  onChange={handleChange}
                  min="0"
                  step="15"
                  placeholder="e.g., 120"
                  className="w-full px-3 py-2 border border-stone-300 rounded-lg focus:ring-2 focus:ring-navy-500 focus:border-navy-500"
                />
              </div>
            </div>

            {/* Description */}
            <div>
              <label htmlFor="description" className="block text-sm font-medium text-stone-700 mb-2">
                Description (Optional)
              </label>
              <textarea
                id="description"
                name="description"
                value={formData.description}
                onChange={handleChange}
                rows={3}
                placeholder="Add any additional details about this task..."
                className="w-full px-3 py-2 border border-stone-300 rounded-lg focus:ring-2 focus:ring-navy-500 focus:border-navy-500 resize-none"
              />
            </div>

            {/* Completion Status Info */}
            {task.is_completed && (
              <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
                <p className="text-sm text-blue-700 mb-2">
                  <strong>This task is marked as completed.</strong>
                </p>
                <p className="text-xs text-navy-800">
                  • To mark as incomplete: Click the green checkmark in the task list<br />
                  • To edit earned marks: Click the small pencil icon next to your score
                </p>
              </div>
            )}

            {/* Submit Error */}
            {errors.submit && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
                <p className="text-sm text-red-600">{errors.submit}</p>
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex justify-end gap-3 pt-4 border-t border-stone-200 bg-stone-50 -mx-6 -mb-5 px-6 py-4 mt-5 rounded-b-2xl">
              <button
                type="button"
                onClick={onClose}
                disabled={isSubmitting}
                className="px-5 py-2.5 border-2 border-stone-300 rounded-xl text-stone-700 font-medium hover:bg-stone-100 transition-all disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isSubmitting}
                className="px-5 py-2.5 bg-navy-800 text-white rounded-xl font-medium hover:bg-navy-900 hover:shadow-lg transition-all disabled:opacity-50 flex items-center"
              >
                {isSubmitting ? (
                  <>
                    <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    Updating...
                  </>
                ) : (
                  'Update Task'
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}

export default EditTaskModal
