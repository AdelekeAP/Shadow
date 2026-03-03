import { useState, useEffect, useRef } from 'react'
import { updateTask } from '../services/api'

const taskTypes = [
  { value: 'test', label: 'Test / Quiz', hint: '10–15 mk' },
  { value: 'project', label: 'Project', hint: '15–20 mk' },
  { value: 'assignment', label: 'Assignment', hint: '5–15 mk' },
  { value: 'participation', label: 'Participation', hint: '~5 mk' },
  { value: 'presentation', label: 'Presentation', hint: 'varies' },
  { value: 'quiz', label: 'Quiz', hint: 'small' },
  { value: 'exam', label: 'Exam', hint: 'final' },
  { value: 'other', label: 'Other', hint: 'custom' },
]

const EditTaskModal = ({ isOpen, onClose, onTaskUpdated, task, enrolledCourses }) => {
  const [formData, setFormData] = useState({
    title: '', description: '', task_type: 'assignment',
    weight: '', category: 'CA', due_date: '', effort_estimate: ''
  })
  const [errors, setErrors] = useState({})
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [entering, setEntering] = useState(false)
  const backdropRef = useRef(null)

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

  useEffect(() => {
    if (isOpen) requestAnimationFrame(() => setEntering(true))
    else setEntering(false)
  }, [isOpen])

  const close = () => { setEntering(false); setTimeout(onClose, 200) }
  const set = (k, v) => { setFormData(p => ({ ...p, [k]: v })); if (errors[k]) setErrors(p => ({ ...p, [k]: null })) }

  const validate = () => {
    const e = {}
    if (!formData.title.trim()) e.title = 'Title is required'
    const w = parseFloat(formData.weight)
    if (!formData.weight || w <= 0) e.weight = 'Enter a valid weight'
    else if (formData.category === 'CA' && w > 30) e.weight = 'CA max: 30 marks'
    else if (formData.category === 'EXAM' && w > 65) e.weight = 'Exam max: 65 marks'
    setErrors(e)
    return !Object.keys(e).length
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!validate()) return
    setIsSubmitting(true)

    try {
      await updateTask(task.id, {
        title: formData.title.trim(),
        description: formData.description.trim() || null,
        task_type: formData.task_type,
        weight: parseFloat(formData.weight),
        category: formData.category,
        due_date: formData.due_date || null,
        effort_estimate: formData.effort_estimate ? parseInt(formData.effort_estimate) : null
      })
      onTaskUpdated()
      close()
    } catch (error) {
      console.error('Error updating task:', error)
      let msg = 'Failed to update task. Try again.'
      if (error.detail) msg = Array.isArray(error.detail) ? error.detail.map(e => e.msg).join(', ') : error.detail
      setErrors({ submit: msg })
    } finally { setIsSubmitting(false) }
  }

  if (!isOpen || !task) return null

  const currentCourse = enrolledCourses.find(uc => uc.id === task.user_course_id)

  return (
    <div
      ref={backdropRef}
      onClick={(e) => e.target === backdropRef.current && close()}
      className={`fixed inset-0 z-50 bg-navy-950/40 backdrop-blur-sm flex items-center justify-center p-4 transition-opacity duration-200 ${entering ? 'opacity-100' : 'opacity-0'}`}
    >
      <div className={`bg-white rounded-2xl shadow-2xl max-w-xl w-full max-h-[90vh] overflow-hidden flex flex-col transition-all duration-300 ${
        entering ? 'scale-100 translate-y-0 opacity-100' : 'scale-95 translate-y-4 opacity-0'
      }`}>

        {/* Header */}
        <div className="flex-shrink-0 px-6 pt-6 pb-0 flex items-start justify-between">
          <div>
            <h2 className="font-display text-[20px] font-bold text-navy-900 tracking-tight">Edit Task</h2>
            {currentCourse && (
              <p className="text-[12px] text-surface-400 mt-0.5">
                {currentCourse.course?.code} — {currentCourse.course?.title}
              </p>
            )}
          </div>
          <button onClick={close} className="p-1.5 rounded-lg text-surface-300 hover:text-surface-400 hover:bg-surface-100 transition-all -mt-1 -mr-1">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto px-6 py-5 space-y-4">

          {/* Title */}
          <Field label="Title" required error={errors.title}>
            <input
              type="text"
              value={formData.title}
              onChange={(e) => set('title', e.target.value)}
              placeholder="e.g., Test 1, Project Submission"
              className={inputCls(errors.title)}
            />
          </Field>

          {/* Type + Category row */}
          <div className="grid grid-cols-2 gap-3">
            <Field label="Type">
              <select value={formData.task_type} onChange={(e) => set('task_type', e.target.value)} className={inputCls()}>
                {taskTypes.map(t => (
                  <option key={t.value} value={t.value}>{t.label} ({t.hint})</option>
                ))}
              </select>
            </Field>
            <Field label="Category">
              <select value={formData.category} onChange={(e) => set('category', e.target.value)} className={inputCls()}>
                <option value="CA">CA (max 30)</option>
                <option value="EXAM">Exam (max 65)</option>
              </select>
            </Field>
          </div>

          {/* Weight + Due date row */}
          <div className="grid grid-cols-2 gap-3">
            <Field label="Weight (marks)" required error={errors.weight}>
              <input
                type="number"
                value={formData.weight}
                onChange={(e) => set('weight', e.target.value)}
                min="0" max={formData.category === 'CA' ? '30' : '65'} step="0.5"
                placeholder={formData.category === 'CA' ? 'max 30' : 'max 65'}
                className={inputCls(errors.weight)}
              />
            </Field>
            <Field label="Due date">
              <input
                type="datetime-local"
                value={formData.due_date}
                onChange={(e) => set('due_date', e.target.value)}
                className={inputCls()}
              />
            </Field>
          </div>

          {/* Effort */}
          <Field label="Effort estimate" hint="minutes">
            <input
              type="number"
              value={formData.effort_estimate}
              onChange={(e) => set('effort_estimate', e.target.value)}
              min="0" step="15" placeholder="e.g., 120"
              className={inputCls()}
            />
          </Field>

          {/* Description */}
          <Field label="Description" hint="optional">
            <textarea
              value={formData.description}
              onChange={(e) => set('description', e.target.value)}
              rows={2}
              placeholder="Additional details..."
              className={`${inputCls()} resize-none`}
            />
          </Field>

          {/* Completion info */}
          {task.is_completed && (
            <div className="px-4 py-3 rounded-xl bg-navy-800/[0.03] border border-navy-200/40 flex items-start gap-2.5">
              <svg className="w-4 h-4 text-navy-500 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8">
                <path strokeLinecap="round" strokeLinejoin="round" d="M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z" />
              </svg>
              <div className="text-[11px] text-navy-600 leading-relaxed">
                <p className="font-semibold mb-0.5">This task is marked as completed.</p>
                <p>To mark as incomplete, click the green checkmark in the task list. To edit marks, click the pencil icon next to your score.</p>
              </div>
            </div>
          )}

          {/* Submit error */}
          {errors.submit && (
            <div className="px-4 py-2.5 rounded-xl bg-red-50 border border-red-100 flex items-center gap-2">
              <svg className="w-4 h-4 text-red-400 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
              </svg>
              <span className="text-[12px] font-medium text-red-600">{errors.submit}</span>
            </div>
          )}
        </form>

        {/* Footer */}
        <div className="flex-shrink-0 flex gap-3 px-6 py-4 border-t border-surface-100">
          <button type="button" onClick={close} disabled={isSubmitting} className="flex-1 px-5 py-2.5 border border-surface-200 text-navy-700 rounded-xl text-[13px] font-semibold hover:bg-surface-50 transition-all disabled:opacity-40">
            Cancel
          </button>
          <button onClick={handleSubmit} disabled={isSubmitting} className="flex-1 px-5 py-2.5 bg-navy-800 hover:bg-navy-900 text-white rounded-xl text-[13px] font-semibold transition-all disabled:opacity-40 flex items-center justify-center gap-2">
            {isSubmitting ? (
              <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            ) : (
              <>
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931z" />
                </svg>
                Update Task
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  )
}

/* ─── Shared field wrapper ─── */
function Field({ label, required, hint, error, children }) {
  return (
    <div>
      <label className="flex items-baseline gap-1.5 mb-1.5">
        <span className="text-[12px] font-semibold text-navy-800 uppercase tracking-wider">{label}</span>
        {required && <span className="text-red-400 text-[10px]">*</span>}
        {hint && <span className="text-[10px] text-surface-300 normal-case tracking-normal font-normal">{hint}</span>}
      </label>
      {children}
      {error && <p className="text-[11px] text-red-500 font-medium mt-1">{error}</p>}
    </div>
  )
}

/* ─── Input class helper ─── */
function inputCls(error) {
  return `w-full bg-surface-50 border ${error ? 'border-red-300 focus:border-red-400 focus:ring-red-100' : 'border-surface-200/80 focus:border-navy-300 focus:ring-navy-100'} rounded-xl px-3.5 py-2.5 text-[13px] text-navy-900 placeholder:text-surface-300 focus:ring-2 focus:bg-white transition-all outline-none`
}

export default EditTaskModal
