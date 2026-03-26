import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { completeTask, deleteTask } from '../services/api'
import EditTaskModal from './EditTaskModal'

/* ═══════════════════════════════════════
   TaskItem — single row
   ═══════════════════════════════════════ */
const TaskItem = ({ task, onUpdate, onDelete, onEdit }) => {
  const navigate = useNavigate()
  const [isLoading, setIsLoading] = useState(false)
  const [showMarkInput, setShowMarkInput] = useState(false)
  const [earnedMarks, setEarnedMarks] = useState('')
  const [showEditMarks, setShowEditMarks] = useState(false)
  const [intervention, setIntervention] = useState(null)
  const [toast, setToast] = useState(null)
  const [confirmAction, setConfirmAction] = useState(null)

  useEffect(() => {
    if (!toast) return
    const t = setTimeout(() => setToast(null), 5000)
    return () => clearTimeout(t)
  }, [toast])

  const handleComplete = async () => {
    if (!showMarkInput) { setShowMarkInput(true); return }
    setIsLoading(true)
    try {
      const completionData = {}
      if (earnedMarks) completionData.earned_marks = parseFloat(earnedMarks)
      const result = await completeTask(task.id, completionData)
      onUpdate(); setShowMarkInput(false); setEarnedMarks('')
      if (result?.intervention?.suggested) setIntervention(result.intervention)
    } catch (e) { console.error(e); setToast({ message: e.detail || 'Failed to complete task', type: 'error' }) }
    finally { setIsLoading(false) }
  }

  const handleUncomplete = async () => {
    setConfirmAction(null)
    setIsLoading(true)
    try {
      const { updateTask } = await import('../services/api')
      await updateTask(task.id, { is_completed: false, completed_at: null, earned_marks: null, is_late: false })
      onUpdate()
    } catch (e) { console.error(e); setToast({ message: e.detail || 'Failed to update task', type: 'error' }) }
    finally { setIsLoading(false) }
  }

  const handleUpdateMarks = async () => {
    setIsLoading(true)
    try {
      const { updateTask } = await import('../services/api')
      if (earnedMarks) await updateTask(task.id, { earned_marks: parseFloat(earnedMarks) })
      onUpdate(); setShowEditMarks(false); setEarnedMarks('')
    } catch (e) { console.error(e); setToast({ message: e.detail || 'Failed to update marks', type: 'error' }) }
    finally { setIsLoading(false) }
  }

  const handleDelete = async () => {
    setConfirmAction(null)
    setIsLoading(true)
    try { await deleteTask(task.id); onDelete(task.id) }
    catch (e) { console.error(e); setToast({ message: e.detail || 'Failed to delete task', type: 'error' }) }
    finally { setIsLoading(false) }
  }

  /* helpers */
  const typeColors = {
    test: 'bg-navy-800/[0.06] text-navy-700',
    project: 'bg-blue-500/[0.08] text-blue-600',
    assignment: 'bg-emerald-500/[0.08] text-emerald-600',
    exam: 'bg-red-500/[0.08] text-red-600',
    participation: 'bg-amber-500/[0.08] text-amber-600',
    quiz: 'bg-pink-500/[0.08] text-pink-600',
    presentation: 'bg-violet-500/[0.08] text-violet-600',
    other: 'bg-surface-100 text-surface-400',
  }

  const fmtDate = (d) => {
    if (!d) return null
    const date = new Date(d), now = new Date()
    const tmrw = new Date(now); tmrw.setDate(tmrw.getDate() + 1)
    if (date.toDateString() === now.toDateString()) return 'Today'
    if (date.toDateString() === tmrw.toDateString()) return 'Tomorrow'
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', ...(date.getFullYear() !== now.getFullYear() && { year: 'numeric' }) })
  }

  const isOverdue = task.due_date && !task.is_completed && new Date(task.due_date) < new Date()
  const isDueSoon = task.due_date && !task.is_completed && new Date(task.due_date) <= new Date(Date.now() + 3 * 864e5)

  return (
    <div
      data-task-id={task.id}
      className={`group relative transition-all duration-200 rounded-xl ${
        task.is_completed
          ? 'opacity-60 hover:opacity-80'
          : 'hover:bg-surface-50'
      } ${isOverdue ? 'bg-red-500/[0.03]' : ''}`}
    >
      <div className="flex items-start gap-3 px-3 py-3">
        {/* Checkbox */}
        <button
          onClick={task.is_completed ? () => setConfirmAction('uncomplete') : handleComplete}
          disabled={isLoading}
          className={`mt-0.5 flex-shrink-0 w-[18px] h-[18px] rounded-md border-[1.5px] flex items-center justify-center transition-all duration-200 ${
            task.is_completed
              ? 'bg-emerald-500 border-emerald-500 shadow-sm shadow-emerald-200'
              : `border-surface-300 hover:border-navy-400 hover:bg-navy-50 ${isOverdue ? 'border-red-300' : ''}`
          } ${isLoading ? 'opacity-40' : 'cursor-pointer'}`}
        >
          {task.is_completed && (
            <svg className="w-2.5 h-2.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="4">
              <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
            </svg>
          )}
        </button>

        {/* Content */}
        <div className="flex-1 min-w-0">
          {/* Title + actions row */}
          <div className="flex items-start justify-between gap-2">
            <h4 className={`text-[13px] font-semibold leading-snug transition-all ${
              task.is_completed ? 'line-through text-surface-300' : 'text-navy-900'
            }`}>
              {task.title}
            </h4>

            {/* Hover actions */}
            <div className="flex items-center gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity duration-150 flex-shrink-0">
              <button
                onClick={() => onEdit(task)}
                disabled={isLoading}
                className="p-1 rounded-md text-surface-300 hover:text-navy-700 hover:bg-surface-100 transition-colors"
                title="Edit"
              >
                <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931z" />
                </svg>
              </button>
              <button
                onClick={() => setConfirmAction('delete')}
                disabled={isLoading}
                className="p-1 rounded-md text-surface-300 hover:text-red-500 hover:bg-red-50 transition-colors"
                title="Delete"
              >
                <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
                </svg>
              </button>
            </div>
          </div>

          {/* Meta line */}
          <div className="flex items-center gap-1.5 mt-1 flex-wrap">
            {task.course_code && (
              <span className="px-1.5 py-0.5 text-[10px] font-semibold rounded bg-navy-800/[0.06] text-navy-700">
                {task.course_code}
              </span>
            )}
            <span className={`px-1.5 py-0.5 text-[10px] font-semibold rounded ${typeColors[task.task_type] || typeColors.other}`}>
              {task.task_type}
            </span>
            {task.category === 'CA' && (
              <span className="px-1.5 py-0.5 text-[10px] font-semibold rounded bg-blue-500/[0.08] text-blue-600">CA</span>
            )}
            <span className="text-surface-300 text-[10px]">·</span>
            <span className="text-[11px] text-surface-400 font-medium">{task.weight}mk</span>

            {task.is_completed && task.earned_marks !== null && (
              <>
                <span className="text-surface-300 text-[10px]">·</span>
                <span className="text-[11px] text-emerald-600 font-semibold">
                  {task.earned_marks}/{task.max_marks}
                </span>
                <button
                  onClick={() => { setEarnedMarks(task.earned_marks.toString()); setShowEditMarks(true) }}
                  className="text-surface-300 hover:text-navy-600 transition-colors"
                  title="Edit marks"
                >
                  <svg className="w-2.5 h-2.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931z" />
                  </svg>
                </button>
              </>
            )}

            {task.due_date && (
              <>
                <span className="text-surface-300 text-[10px]">·</span>
                <span className={`text-[11px] flex items-center gap-1 ${
                  isOverdue ? 'text-red-500 font-semibold' : isDueSoon ? 'text-amber-500 font-medium' : 'text-surface-400'
                }`}>
                  <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 012.25-2.25h13.5A2.25 2.25 0 0121 7.5v11.25m-18 0A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75m-18 0v-7.5A2.25 2.25 0 015.25 9h13.5A2.25 2.25 0 0121 11.25v7.5" />
                  </svg>
                  {fmtDate(task.due_date)}{isOverdue && ' (overdue)'}
                </span>
              </>
            )}

            {task.priority_score && !task.is_completed && (
              <>
                <span className="text-surface-300 text-[10px]">·</span>
                <span className={`font-mono text-[10px] font-semibold px-1 py-0.5 rounded ${
                  task.priority_score >= 70 ? 'bg-red-500/[0.08] text-red-500' :
                  task.priority_score >= 50 ? 'bg-amber-500/[0.08] text-amber-500' :
                  'bg-surface-100 text-surface-400'
                }`}>
                  P{Math.round(task.priority_score)}
                </span>
              </>
            )}
          </div>

          {task.description && (
            <p className="text-[12px] text-surface-400 mt-1 line-clamp-1">{task.description}</p>
          )}

          {/* Mark input (completing) */}
          {showMarkInput && !task.is_completed && (
            <div className="mt-2.5 flex items-center gap-2 p-2 rounded-lg bg-surface-50 border border-surface-200">
              <input
                type="number" min="0" max={task.max_marks} step="0.5"
                value={earnedMarks}
                onChange={(e) => setEarnedMarks(e.target.value)}
                placeholder={`Marks (max ${task.max_marks})`}
                className="w-32 px-2.5 py-1 text-[12px] border border-surface-200 rounded-lg bg-white focus:ring-2 focus:ring-navy-500/20 focus:border-navy-400 outline-none transition-all"
                autoFocus
              />
              <button
                onClick={handleComplete}
                disabled={isLoading}
                className="px-2.5 py-1 bg-emerald-500 text-white text-[11px] font-semibold rounded-lg hover:bg-emerald-600 disabled:opacity-40 transition-colors"
              >
                {isLoading ? 'Saving...' : 'Done'}
              </button>
              <button
                onClick={() => setShowMarkInput(false)}
                className="px-2.5 py-1 text-[11px] font-medium text-surface-400 hover:text-navy-800 transition-colors"
              >
                Cancel
              </button>
            </div>
          )}

          {/* Edit marks (completed task) */}
          {showEditMarks && task.is_completed && (
            <div className="mt-2.5 flex items-center gap-2 p-2 rounded-lg bg-blue-50/50 border border-blue-100">
              <span className="text-[11px] text-blue-600 font-medium">Edit marks:</span>
              <input
                type="number" min="0" max={task.max_marks} step="0.5"
                value={earnedMarks}
                onChange={(e) => setEarnedMarks(e.target.value)}
                className="w-24 px-2.5 py-1 text-[12px] border border-blue-200 rounded-lg bg-white focus:ring-2 focus:ring-navy-500/20 focus:border-navy-400 outline-none transition-all"
                autoFocus
              />
              <button
                onClick={handleUpdateMarks}
                disabled={isLoading}
                className="px-2.5 py-1 bg-navy-800 text-white text-[11px] font-semibold rounded-lg hover:bg-navy-900 disabled:opacity-40 transition-colors"
              >
                {isLoading ? '...' : 'Save'}
              </button>
              <button
                onClick={() => { setShowEditMarks(false); setEarnedMarks('') }}
                className="px-2.5 py-1 text-[11px] font-medium text-surface-400 hover:text-navy-800 transition-colors"
              >
                Cancel
              </button>
            </div>
          )}

          {/* Inline confirmation bar */}
          {confirmAction && (
            <div className="mt-2.5 flex items-center gap-2 p-2.5 rounded-lg bg-amber-50 border border-amber-200/80">
              <svg className="w-4 h-4 text-amber-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
              </svg>
              <span className="text-[12px] font-medium text-amber-800 flex-1">
                {confirmAction === 'delete' ? 'Delete this task?' : 'Mark as incomplete? Earned marks will be removed.'}
              </span>
              <button
                onClick={confirmAction === 'delete' ? handleDelete : handleUncomplete}
                disabled={isLoading}
                className={`px-2.5 py-1 text-white text-[11px] font-semibold rounded-lg disabled:opacity-40 transition-colors ${
                  confirmAction === 'delete' ? 'bg-red-500 hover:bg-red-600' : 'bg-amber-500 hover:bg-amber-600'
                }`}
              >
                {isLoading ? '...' : 'Yes'}
              </button>
              <button
                onClick={() => setConfirmAction(null)}
                className="px-2.5 py-1 text-[11px] font-medium text-surface-400 hover:text-navy-800 transition-colors"
              >
                Cancel
              </button>
            </div>
          )}

          {/* Toast notification */}
          {toast && (
            <div className="mt-2 flex items-center gap-2 px-2.5 py-2 rounded-lg border text-[11px] font-medium bg-red-50 border-red-200 text-red-700">
              <svg className="w-3.5 h-3.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
              </svg>
              <span className="flex-1">{toast.message}</span>
              <button onClick={() => setToast(null)} className="p-0.5 hover:bg-red-100 rounded transition-colors">
                <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Urgency accent line */}
      {isOverdue && !task.is_completed && (
        <div className="absolute left-0 top-2 bottom-2 w-[3px] rounded-full bg-red-400" />
      )}
      {task.is_urgent && !task.is_completed && !isOverdue && (
        <div className="absolute left-0 top-2 bottom-2 w-[3px] rounded-full bg-amber-400" />
      )}

      {/* SmartStudy Intervention Modal */}
      {intervention && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm" onClick={() => setIntervention(null)}>
          <div className="bg-white rounded-2xl shadow-2xl max-w-sm w-full mx-4 overflow-hidden" onClick={e => e.stopPropagation()}>
            {/* Header */}
            <div className="bg-gradient-to-br from-navy-800 to-navy-900 px-6 py-5 text-center">
              <div className="w-12 h-12 rounded-full bg-white/10 flex items-center justify-center mx-auto mb-3">
                <svg className="w-6 h-6 text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9 3.75h.008v.008H12v-.008Z" />
                </svg>
              </div>
              <p className="text-white/90 text-[14px] font-semibold">
                You scored <span className="text-amber-400">{intervention.score_percentage}%</span> on
              </p>
              <p className="text-white text-[16px] font-bold mt-0.5">{intervention.task_title}</p>
              {intervention.course_code && (
                <p className="text-white/50 text-[12px] mt-1">{intervention.course_code} — {intervention.course_title}</p>
              )}
            </div>

            {/* Body */}
            <div className="px-6 py-5">
              <p className="text-[13px] text-surface-500 text-center mb-5">
                SmartStudy can create a personalized study plan to help you improve in this area.
              </p>

              <div className="space-y-2.5">
                <button
                  onClick={() => {
                    setIntervention(null)
                    navigate('/smartstudy', {
                      state: {
                        courseCode: intervention.course_code,
                        courseName: intervention.course_title,
                        topic: intervention.task_title,
                        reason: 'low_score',
                      }
                    })
                  }}
                  className="w-full py-2.5 px-4 bg-gradient-to-r from-navy-800 to-navy-700 text-white text-[13px] font-semibold rounded-xl hover:from-navy-900 hover:to-navy-800 transition-all shadow-sm"
                >
                  Get Study Plan
                </button>
                <button
                  onClick={() => setIntervention(null)}
                  className="w-full py-2.5 px-4 text-surface-400 text-[13px] font-medium rounded-xl hover:bg-surface-50 transition-colors"
                >
                  Maybe Later
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

/* ═══════════════════════════════════════
   TaskList — main list with filters
   ═══════════════════════════════════════ */
const TaskList = ({ tasks, onUpdate, showCompleted = true, groupByCourse = false, enrolledCourses = [] }) => {
  const [filter, setFilter] = useState('all')
  const [editingTask, setEditingTask] = useState(null)

  const isOverdue = (t) => t.due_date && !t.is_completed && new Date(t.due_date) < new Date()

  const filtered = tasks.filter(t => {
    if (filter === 'pending') return !t.is_completed
    if (filter === 'completed') return t.is_completed
    if (filter === 'urgent') return (t.is_urgent || isOverdue(t)) && !t.is_completed
    return showCompleted || !t.is_completed
  })

  const sorted = [...filtered].sort((a, b) => {
    if (a.is_completed !== b.is_completed) return a.is_completed ? 1 : -1
    if (b.priority_score !== a.priority_score) return (b.priority_score || 0) - (a.priority_score || 0)
    if (a.due_date && b.due_date) return new Date(a.due_date) - new Date(b.due_date)
    return 0
  })

  const counts = {
    all: tasks.length,
    pending: tasks.filter(t => !t.is_completed).length,
    urgent: tasks.filter(t => (t.is_urgent || isOverdue(t)) && !t.is_completed).length,
    completed: tasks.filter(t => t.is_completed).length,
  }

  /* empty state */
  if (!tasks.length) return (
    <div className="py-12 text-center">
      <div className="w-12 h-12 rounded-2xl bg-surface-100 flex items-center justify-center mx-auto mb-3">
        <svg className="w-6 h-6 text-surface-300" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
          <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h3.75M9 15h3.75M9 18h3.75m3 .75H18a2.25 2.25 0 002.25-2.25V6.108c0-1.135-.845-2.098-1.976-2.192a48.424 48.424 0 00-1.123-.08m-5.801 0c-.065.21-.1.433-.1.664 0 .414.336.75.75.75h4.5a.75.75 0 00.75-.75 2.25 2.25 0 00-.1-.664m-5.8 0A2.251 2.251 0 0113.5 2.25H15c1.012 0 1.867.668 2.15 1.586m-5.8 0c-.376.023-.75.05-1.124.08C9.095 4.01 8.25 4.973 8.25 6.108V8.25m0 0H4.875c-.621 0-1.125.504-1.125 1.125v11.25c0 .621.504 1.125 1.125 1.125h9.75c.621 0 1.125-.504 1.125-1.125V9.375c0-.621-.504-1.125-1.125-1.125H8.25z" />
        </svg>
      </div>
      <p className="text-[14px] font-semibold text-navy-900">No tasks yet</p>
      <p className="text-[12px] text-surface-400 mt-0.5">Create a task to get started</p>
    </div>
  )

  const filters = [
    { key: 'all', label: 'All' },
    { key: 'pending', label: 'Pending' },
    { key: 'urgent', label: 'Urgent' },
    { key: 'completed', label: 'Done' },
  ]

  return (
    <div>
      {/* Filter tabs */}
      <div className="flex items-center gap-0.5 mb-4 p-0.5 bg-surface-100/80 rounded-lg w-fit">
        {filters.map(({ key, label }) => (
          <button
            key={key}
            onClick={() => setFilter(key)}
            className={`relative px-3 py-1.5 text-[12px] font-semibold rounded-md transition-all duration-200 ${
              filter === key
                ? 'bg-white text-navy-800 shadow-sm'
                : 'text-surface-400 hover:text-navy-700'
            }`}
          >
            {label}
            {counts[key] > 0 && key !== 'all' && (
              <span className={`ml-1 inline-flex items-center justify-center min-w-[16px] h-4 px-1 text-[10px] font-bold rounded-full ${
                filter === key
                  ? key === 'urgent' ? 'bg-red-100 text-red-600' : 'bg-navy-100 text-navy-700'
                  : key === 'urgent' ? 'bg-red-100 text-red-500' : 'bg-surface-200/80 text-surface-400'
              }`}>
                {counts[key]}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Task rows */}
      <div className="space-y-0.5">
        {sorted.length === 0 ? (
          <p className="text-center text-[13px] text-surface-400 py-8">No tasks match this filter</p>
        ) : (
          sorted.map(task => (
            <TaskItem
              key={task.id}
              task={task}
              onUpdate={onUpdate}
              onDelete={() => onUpdate()}
              onEdit={(t) => setEditingTask(t)}
            />
          ))
        )}
      </div>

      {/* Footer summary */}
      {sorted.length > 0 && (
        <div className="mt-4 pt-3 border-t border-surface-100 flex items-center justify-between">
          <div className="flex items-center gap-4 text-[11px] text-surface-400">
            <span>
              <span className="font-semibold text-navy-800">{counts.completed}</span> of {counts.all} done
            </span>
            <span className="text-surface-200">|</span>
            <span>
              <span className="font-semibold text-navy-800">
                {tasks.filter(t => !t.is_completed && t.category === 'CA').reduce((s, t) => s + (t.weight || 0), 0).toFixed(1)}
              </span> CA marks remaining
            </span>
          </div>
          {/* Mini completion bar */}
          <div className="flex items-center gap-2">
            <div className="w-20 h-1.5 bg-surface-100 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-navy-700 to-navy-500 rounded-full transition-all duration-500"
                style={{ width: `${counts.all > 0 ? (counts.completed / counts.all) * 100 : 0}%` }}
              />
            </div>
            <span className="font-mono text-[10px] font-semibold text-surface-400">
              {counts.all > 0 ? Math.round((counts.completed / counts.all) * 100) : 0}%
            </span>
          </div>
        </div>
      )}

      {/* Edit Modal */}
      <EditTaskModal
        isOpen={editingTask !== null}
        onClose={() => setEditingTask(null)}
        onTaskUpdated={() => { setEditingTask(null); onUpdate() }}
        task={editingTask}
        enrolledCourses={enrolledCourses}
      />
    </div>
  )
}

export default TaskList
