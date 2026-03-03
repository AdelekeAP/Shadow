import { useState, useEffect, useRef } from 'react'
import { createTask } from '../services/api'

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

export default function AddTaskModal({ isOpen, onClose, onTaskCreated, enrolledCourses }) {
  const [form, setForm] = useState({
    user_course_id: '', title: '', description: '', task_type: 'assignment',
    weight: '', category: 'CA', due_date: '', effort_estimate: '',
    is_completed: false, earned_marks: '',
  })
  const [errors, setErrors] = useState({})
  const [submitting, setSubmitting] = useState(false)
  const [entering, setEntering] = useState(false)
  const backdropRef = useRef(null)

  useEffect(() => {
    if (isOpen) requestAnimationFrame(() => setEntering(true))
    else { setEntering(false); resetForm() }
  }, [isOpen])

  const resetForm = () => {
    setForm({ user_course_id: '', title: '', description: '', task_type: 'assignment', weight: '', category: 'CA', due_date: '', effort_estimate: '', is_completed: false, earned_marks: '' })
    setErrors({})
  }

  const close = () => { setEntering(false); setTimeout(onClose, 200) }
  const set = (k, v) => { setForm(p => ({ ...p, [k]: v })); if (errors[k]) setErrors(p => ({ ...p, [k]: null })) }

  const validate = () => {
    const e = {}
    if (!form.user_course_id) e.user_course_id = 'Select a course'
    if (!form.title.trim()) e.title = 'Title is required'
    const w = parseFloat(form.weight)
    if (!form.weight || w <= 0) e.weight = 'Enter a valid weight'
    else if (form.category === 'CA' && w > 30) e.weight = 'CA max: 30 marks'
    else if (form.category === 'EXAM' && w > 65) e.weight = 'Exam max: 65 marks'
    if (form.is_completed && form.earned_marks) {
      const em = parseFloat(form.earned_marks)
      if (em > w) e.earned_marks = 'Cannot exceed weight'
      if (em < 0) e.earned_marks = 'Must be positive'
    }
    setErrors(e)
    return !Object.keys(e).length
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!validate()) return
    setSubmitting(true)
    try {
      await createTask({
        user_course_id: form.user_course_id,
        title: form.title.trim(),
        description: form.description.trim() || null,
        task_type: form.task_type,
        weight: parseFloat(form.weight),
        category: form.category,
        due_date: form.due_date || null,
        effort_estimate: form.effort_estimate ? parseInt(form.effort_estimate) : null,
        is_completed: form.is_completed,
        earned_marks: form.is_completed && form.earned_marks ? parseFloat(form.earned_marks) : null,
      })
      onTaskCreated()
      close()
    } catch (err) {
      let msg = 'Failed to create task. Try again.'
      if (err.detail) msg = Array.isArray(err.detail) ? err.detail.map(e => e.msg).join(', ') : err.detail
      setErrors({ submit: msg })
    } finally { setSubmitting(false) }
  }

  if (!isOpen) return null

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
            <h2 className="font-display text-[20px] font-bold text-navy-900 tracking-tight">Add Task</h2>
            <p className="text-[12px] text-surface-400 mt-0.5">Create a new academic task</p>
          </div>
          <button onClick={close} className="p-1.5 rounded-lg text-surface-300 hover:text-surface-400 hover:bg-surface-100 transition-all -mt-1 -mr-1">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto px-6 py-5 space-y-4">

          {/* Course */}
          <Field label="Course" required error={errors.user_course_id}>
            <select
              value={form.user_course_id}
              onChange={(e) => set('user_course_id', e.target.value)}
              className={inputCls(errors.user_course_id)}
            >
              <option value="">Select a course</option>
              {enrolledCourses.map(uc => (
                <option key={uc.id} value={uc.id}>{uc.course?.code} — {uc.course?.title}</option>
              ))}
            </select>
          </Field>

          {/* Title */}
          <Field label="Title" required error={errors.title}>
            <input
              type="text"
              value={form.title}
              onChange={(e) => set('title', e.target.value)}
              placeholder="e.g., Test 1, Project Submission"
              className={inputCls(errors.title)}
            />
          </Field>

          {/* Type + Category row */}
          <div className="grid grid-cols-2 gap-3">
            <Field label="Type">
              <select value={form.task_type} onChange={(e) => set('task_type', e.target.value)} className={inputCls()}>
                {taskTypes.map(t => (
                  <option key={t.value} value={t.value}>{t.label} ({t.hint})</option>
                ))}
              </select>
            </Field>
            <Field label="Category">
              <select value={form.category} onChange={(e) => set('category', e.target.value)} className={inputCls()}>
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
                value={form.weight}
                onChange={(e) => set('weight', e.target.value)}
                min="0" max={form.category === 'CA' ? '30' : '65'} step="0.5"
                placeholder={form.category === 'CA' ? 'max 30' : 'max 65'}
                className={inputCls(errors.weight)}
              />
            </Field>
            <Field label="Due date">
              <input
                type="datetime-local"
                value={form.due_date}
                onChange={(e) => set('due_date', e.target.value)}
                className={inputCls()}
              />
            </Field>
          </div>

          {/* Effort */}
          <Field label="Effort estimate" hint="minutes">
            <input
              type="number"
              value={form.effort_estimate}
              onChange={(e) => set('effort_estimate', e.target.value)}
              min="0" step="15" placeholder="e.g., 120"
              className={inputCls()}
            />
          </Field>

          {/* Description */}
          <Field label="Description" hint="optional">
            <textarea
              value={form.description}
              onChange={(e) => set('description', e.target.value)}
              rows={2}
              placeholder="Additional details..."
              className={`${inputCls()} resize-none`}
            />
          </Field>

          {/* Already completed toggle */}
          <div className="border-t border-surface-100 pt-4">
            <label className="flex items-center gap-3 cursor-pointer group">
              <div
                onClick={() => set('is_completed', !form.is_completed)}
                className={`w-5 h-5 rounded-md border-2 flex items-center justify-center transition-all ${
                  form.is_completed
                    ? 'bg-emerald-500 border-emerald-500'
                    : 'border-surface-300 group-hover:border-surface-400'
                }`}
              >
                {form.is_completed && (
                  <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="3">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                  </svg>
                )}
              </div>
              <div>
                <p className="text-[13px] font-semibold text-navy-900">Already completed</p>
                <p className="text-[11px] text-surface-400">Record marks for a finished task</p>
              </div>
            </label>

            {form.is_completed && (
              <div className="mt-3">
                <Field label="Marks earned" error={errors.earned_marks}>
                  <input
                    type="number"
                    value={form.earned_marks}
                    onChange={(e) => set('earned_marks', e.target.value)}
                    min="0" max={form.weight} step="0.5"
                    placeholder={form.weight ? `max ${form.weight}` : '0'}
                    className={inputCls(errors.earned_marks)}
                  />
                </Field>
              </div>
            )}
          </div>

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
          <button type="button" onClick={close} disabled={submitting} className="flex-1 px-5 py-2.5 border border-surface-200 text-navy-700 rounded-xl text-[13px] font-semibold hover:bg-surface-50 transition-all disabled:opacity-40">
            Cancel
          </button>
          <button onClick={handleSubmit} disabled={submitting} className="flex-1 px-5 py-2.5 bg-navy-800 hover:bg-navy-900 text-white rounded-xl text-[13px] font-semibold transition-all disabled:opacity-40 flex items-center justify-center gap-2">
            {submitting ? (
              <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            ) : (
              <>
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
                </svg>
                Create Task
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
