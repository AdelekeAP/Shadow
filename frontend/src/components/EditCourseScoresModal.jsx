import { useState, useEffect, useRef } from 'react'

export default function EditCourseScoresModal({ isOpen, onClose, enrollment, onUpdate }) {
  const [form, setForm] = useState({ ca_score: '', participation_score: '', exam_score: '', project_score: '' })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [entering, setEntering] = useState(false)
  const backdropRef = useRef(null)

  // FYP / project courses are graded as a single score out of 100 (no CA/Exam split)
  const isFYP = enrollment?.course?.grading_type === 'single_grade'

  useEffect(() => {
    if (enrollment) {
      const fyp = enrollment.course?.grading_type === 'single_grade'
      setForm({
        ca_score: enrollment.ca_score || '',
        participation_score: enrollment.participation_score || '',
        exam_score: enrollment.exam_score || '',
        // FYP stores its single grade in exam_score (0–100)
        project_score: fyp ? (enrollment.exam_score ?? enrollment.current_score ?? '') : '',
      })
    }
  }, [enrollment])

  useEffect(() => {
    if (isOpen) requestAnimationFrame(() => setEntering(true))
    else setEntering(false)
  }, [isOpen])

  const close = () => { setEntering(false); setTimeout(onClose, 200) }
  const set = (k, v) => { setForm(p => ({ ...p, [k]: v })); setError('') }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    // FYP / single-grade: one project score out of 100
    if (isFYP) {
      const grade = form.project_score === '' ? null : parseFloat(form.project_score)
      if (grade === null || isNaN(grade) || grade < 0 || grade > 100) {
        setError('Project grade: 0–100'); setLoading(false); return
      }
      try {
        await onUpdate(enrollment.id, { project_score: grade })
        close()
      } catch (err) {
        setError(err.message || err.detail || 'Failed to update grade')
      } finally { setLoading(false) }
      return
    }

    const ca = parseFloat(form.ca_score) || 0
    const part = form.participation_score ? parseFloat(form.participation_score) : null
    const exam = form.exam_score ? parseFloat(form.exam_score) : null

    if (ca < 0 || ca > 30) { setError('CA score: 0–30'); setLoading(false); return }
    if (part !== null && (part < 0 || part > 5)) { setError('Participation: 0–5'); setLoading(false); return }
    if (exam !== null && (exam < 0 || exam > 65)) { setError('Exam score: 0–65'); setLoading(false); return }

    try {
      const data = {}
      if (ca > 0) data.ca_score = ca
      if (part !== null) data.participation_score = part
      if (exam !== null) data.exam_score = exam
      await onUpdate(enrollment.id, data)
      close()
    } catch (err) {
      setError(err.message || err.detail || 'Failed to update scores')
    } finally { setLoading(false) }
  }

  if (!isOpen) return null

  /* ── Preview totals ── */
  const ca = parseFloat(form.ca_score) || 0
  const part = form.participation_score ? parseFloat(form.participation_score) : 0
  const exam = form.exam_score ? parseFloat(form.exam_score) : 0
  const total = ca + part + exam

  return (
    <div
      ref={backdropRef}
      onClick={(e) => e.target === backdropRef.current && close()}
      className={`fixed inset-0 z-50 bg-navy-950/40 backdrop-blur-sm flex items-center justify-center p-4 transition-opacity duration-200 ${entering ? 'opacity-100' : 'opacity-0'}`}
    >
      <div className={`bg-white rounded-2xl shadow-2xl max-w-md w-full overflow-hidden transition-all duration-300 ${
        entering ? 'scale-100 translate-y-0 opacity-100' : 'scale-95 translate-y-4 opacity-0'
      }`}>

        {/* Header */}
        <div className="px-6 pt-6 pb-0">
          <h2 className="font-display text-[20px] font-bold text-navy-900 tracking-tight">Update Scores</h2>
          <p className="text-[13px] text-surface-400 mt-0.5">{enrollment?.course?.code} — {enrollment?.course?.title}</p>
        </div>

        {/* Info banner */}
        <div className="mx-6 mt-4 px-4 py-2.5 rounded-xl bg-navy-800/[0.03] border border-navy-200/40 flex items-start gap-2.5">
          <svg className="w-4 h-4 text-navy-500 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8">
            <path strokeLinecap="round" strokeLinejoin="round" d="M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z" />
          </svg>
          <p className="text-[11px] text-navy-600 leading-relaxed">
            {isFYP
              ? <>This is a <span className="font-semibold">Final Year Project</span> — graded as a single score out of 100 (thesis, defence &amp; supervisor assessment). No CA/Exam split.</>
              : <>Participation defaults to <span className="font-semibold">3/5</span> for predictions until you update it.</>}
          </p>
        </div>

        {/* Error */}
        {error && (
          <div className="mx-6 mt-3 px-4 py-2.5 rounded-xl bg-red-50 border border-red-100 flex items-center gap-2">
            <svg className="w-4 h-4 text-red-400 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
            </svg>
            <span className="text-[12px] font-medium text-red-600">{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="px-6 py-5 space-y-4">
          {isFYP ? (
            <>
              {/* Single project grade out of 100 */}
              <ScoreField
                label="Project Grade" max="100" hint="Final thesis / defence score"
                value={form.project_score} onChange={(v) => set('project_score', v)}
                placeholder="—"
              />
            </>
          ) : (
            <>
              {/* CA Score */}
              <ScoreField
                label="CA Score" max="30" hint="Assignments, tests, etc."
                value={form.ca_score} onChange={(v) => set('ca_score', v)}
              />

              {/* Participation */}
              <ScoreField
                label="Participation" max="5" hint="Lecturer-awarded"
                value={form.participation_score} onChange={(v) => set('participation_score', v)}
              />

              {/* Exam */}
              <ScoreField
                label="Exam Score" max="65" hint="Leave blank if not taken"
                value={form.exam_score} onChange={(v) => set('exam_score', v)}
                placeholder="—"
              />
            </>
          )}

          {/* Live total preview */}
          <div className="flex items-center justify-between py-3 border-t border-surface-100">
            <span className="text-[12px] font-semibold text-surface-400 uppercase tracking-wider">{isFYP ? 'Project grade' : 'Total preview'}</span>
            <div className="flex items-baseline gap-1">
              <span className="font-mono text-[20px] font-bold text-navy-900">{isFYP ? (parseFloat(form.project_score) || 0).toFixed(1) : total.toFixed(1)}</span>
              <span className="text-[12px] text-surface-300">/100</span>
            </div>
          </div>
        </form>

        {/* Footer */}
        <div className="flex gap-3 px-6 py-4 border-t border-surface-100">
          <button type="button" onClick={close} disabled={loading} className="flex-1 px-5 py-2.5 border border-surface-200 text-navy-700 rounded-xl text-[13px] font-semibold hover:bg-surface-50 transition-all disabled:opacity-40">
            Cancel
          </button>
          <button onClick={handleSubmit} disabled={loading} className="flex-1 px-5 py-2.5 bg-navy-800 hover:bg-navy-900 text-white rounded-xl text-[13px] font-semibold transition-all disabled:opacity-40 flex items-center justify-center gap-2">
            {loading ? (
              <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            ) : 'Save Scores'}
          </button>
        </div>
      </div>
    </div>
  )
}

/* ─── Score input with visual max bar ─── */
function ScoreField({ label, max, hint, value, onChange, placeholder }) {
  const numMax = parseFloat(max)
  const numVal = parseFloat(value) || 0
  const pct = numMax > 0 ? Math.min((numVal / numMax) * 100, 100) : 0

  return (
    <div>
      <div className="flex items-baseline justify-between mb-1.5">
        <label className="text-[12px] font-semibold text-navy-800 uppercase tracking-wider">{label}</label>
        <span className="text-[10px] text-surface-300">out of {max}</span>
      </div>
      <div className="relative">
        <input
          type="number"
          step="0.01"
          min="0"
          max={max}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder || '0.00'}
          className="w-full bg-surface-50 border border-surface-200/80 rounded-xl px-3.5 py-2.5 text-[13px] text-navy-900 placeholder:text-surface-300 focus:border-navy-300 focus:ring-2 focus:ring-navy-100 focus:bg-white transition-all outline-none font-mono"
        />
        {/* Fill bar */}
        <div className="absolute bottom-0 left-0 right-0 h-[3px] rounded-b-xl overflow-hidden bg-surface-100">
          <div
            className="h-full rounded-b-xl transition-all duration-300 bg-navy-500/40"
            style={{ width: `${pct}%` }}
          />
        </div>
      </div>
      {hint && <p className="text-[10px] text-surface-300 mt-1">{hint}</p>}
    </div>
  )
}
