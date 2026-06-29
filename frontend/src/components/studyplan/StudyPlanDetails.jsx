import { useState, useEffect, lazy, Suspense } from 'react'
import { linkifyText, getActivityIcon, getDifficultyColor } from './studyPlanHelpers.jsx'
import ResourceCard from './ResourceCard'
import AudioPlayer from './AudioPlayer'
import ConceptDiagram from './ConceptDiagram'
import PracticeExercise from './PracticeExercise'
import StudyCards from './StudyCards'
import ErrorBoundary from '../ErrorBoundary'
import { generateConceptDiagram, generateSectionQuiz } from '../../services/api'
import { friendlyError } from '../../utils/errors'

const SlideRangeViewer = lazy(() => import('./SlideRangeViewer'))

/* ─── SVG Icons ─── */
const TargetIcon = ({ className }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8">
    <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
)
const ClipboardIcon = ({ className }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8">
    <path strokeLinecap="round" strokeLinejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
  </svg>
)
const TrophyIcon = ({ className }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8">
    <path strokeLinecap="round" strokeLinejoin="round" d="M16.5 18.75h-9m9 0a3 3 0 013 3h-15a3 3 0 013-3m9 0v-3.375c0-.621-.503-1.125-1.125-1.125h-.871M7.5 18.75v-3.375c0-.621.504-1.125 1.125-1.125h.872m5.007 0H9.497m5.007 0a7.454 7.454 0 01-.982-3.172M9.497 14.25a7.454 7.454 0 00.981-3.172M5.25 4.236c-.982.143-1.954.317-2.916.52A6.003 6.003 0 007.73 9.728M5.25 4.236V4.5c0 2.108.966 3.99 2.48 5.228M5.25 4.236V2.721C7.456 2.41 9.71 2.25 12 2.25c2.291 0 4.545.16 6.75.47v1.516M18.75 4.236c.982.143 1.954.317 2.916.52A6.003 6.003 0 0016.27 9.728M18.75 4.236V4.5c0 2.108-.966 3.99-2.48 5.228m0 0a6.042 6.042 0 01-2.77.988m-5.96 0a6.042 6.042 0 002.77.988" />
  </svg>
)
const RocketIcon = ({ className }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8">
    <path strokeLinecap="round" strokeLinejoin="round" d="M15.59 14.37a6 6 0 01-5.84 7.38v-4.8m5.84-2.58a14.98 14.98 0 006.16-12.12A14.98 14.98 0 009.631 8.41m5.96 5.96a14.926 14.926 0 01-5.841 2.58m-.119-8.54a6 6 0 00-7.381 5.84h4.8m2.581-5.84a14.927 14.927 0 00-2.58 5.84m2.699 2.7c-.103.021-.207.041-.311.06a15.09 15.09 0 01-2.448-2.448 14.9 14.9 0 01.06-.312m-2.24 2.39a4.493 4.493 0 00-1.757 4.306 4.493 4.493 0 004.306-1.758M16.5 9a1.5 1.5 0 11-3 0 1.5 1.5 0 013 0z" />
  </svg>
)
const PrinterIcon = ({ className }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8">
    <path strokeLinecap="round" strokeLinejoin="round" d="M6.72 13.829c-.24.03-.48.062-.72.096m.72-.096a42.415 42.415 0 0110.56 0m-10.56 0L6.34 18m10.94-4.171c.24.03.48.062.72.096m-.72-.096L17.66 18m0 0l.229 2.523a1.125 1.125 0 01-1.12 1.227H7.231c-.662 0-1.18-.568-1.12-1.227L6.34 18m11.318 0h1.091A2.25 2.25 0 0021 15.75V9.456c0-1.081-.768-2.015-1.837-2.175a48.055 48.055 0 00-1.913-.247M6.34 18H5.25A2.25 2.25 0 013 15.75V9.456c0-1.081.768-2.015 1.837-2.175a48.041 48.041 0 011.913-.247m10.5 0a48.536 48.536 0 00-10.5 0m10.5 0V3.375c0-.621-.504-1.125-1.125-1.125h-8.25c-.621 0-1.125.504-1.125 1.125v3.659M18.75 12h.008v.008h-.008V12zm-2.25 0h.008v.008H16.5V12z" />
  </svg>
)
const ChevronIcon = ({ className, open }) => (
  <svg className={`${className} transition-transform duration-200 ${open ? 'rotate-180' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
    <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
  </svg>
)

/* ─── Activity type color accents ─── */
const activityAccent = {
  video:       { border: 'border-l-red-400',     bg: 'bg-red-50/40',    icon: 'bg-red-100 text-red-600' },
  reading:     { border: 'border-l-blue-400',    bg: 'bg-blue-50/40',   icon: 'bg-blue-100 text-blue-600' },
  review:      { border: 'border-l-indigo-400',  bg: 'bg-indigo-50/40', icon: 'bg-indigo-100 text-indigo-600' },
  practice:    { border: 'border-l-emerald-400', bg: 'bg-emerald-50/40',icon: 'bg-emerald-100 text-emerald-600' },
  interactive: { border: 'border-l-cyan-400',    bg: 'bg-cyan-50/40',   icon: 'bg-cyan-100 text-cyan-600' },
  project:     { border: 'border-l-violet-400',  bg: 'bg-violet-50/40', icon: 'bg-violet-100 text-violet-600' },
  writing:     { border: 'border-l-amber-400',   bg: 'bg-amber-50/40',  icon: 'bg-amber-100 text-amber-600' },
  audio:       { border: 'border-l-orange-400',  bg: 'bg-orange-50/40', icon: 'bg-orange-100 text-orange-600' },
}
const defaultAccent = { border: 'border-l-surface-300', bg: 'bg-surface-50/40', icon: 'bg-surface-100 text-surface-500' }

/* ─── Expandable text: shows 2 lines, click to reveal full ─── */
function ExpandableText({ text, className = '' }) {
  const [expanded, setExpanded] = useState(false)
  if (!text) return null
  const isLong = text.length > 140

  return (
    <div className={className}>
      <p className={`text-[12px] text-surface-500 leading-relaxed ${!expanded && isLong ? 'line-clamp-2' : ''}`}>
        {linkifyText(text)}
      </p>
      {isLong && (
        <button
          onClick={() => setExpanded(!expanded)}
          className="text-[11px] font-semibold text-navy-500 hover:text-navy-700 mt-1 transition-colors"
        >
          {expanded ? 'Show less' : 'Read more'}
        </button>
      )}
    </div>
  )
}

/* ─── Mini time bar ─── */
function TimeBadge({ minutes }) {
  if (!minutes) return null
  const width = Math.min(100, (minutes / 60) * 100)
  return (
    <div className="flex items-center gap-2">
      <div className="w-16 h-1.5 rounded-full bg-surface-200/60 overflow-hidden">
        <div className="h-full rounded-full bg-navy-300/60 transition-all" style={{ width: `${width}%` }} />
      </div>
      <span className="text-[10px] text-surface-400 font-mono tabular-nums">{minutes}m</span>
    </div>
  )
}

export default function StudyPlanDetails({ plan, onDayComplete, onPlayVideo, onSubmitBeforeScore, onSubmitAfterScore, onTakeQuiz, quizActive }) {
  const planData = plan.plan_data || {}
  const days = planData.days || []
  const completedDays = plan.completed_days || []
  const resources = plan.resources || []

  const [beforeScore, setBeforeScore] = useState('')
  const [afterScore, setAfterScore] = useState('')
  const [savingDay, setSavingDay] = useState(null)
  const [justCompleted, setJustCompleted] = useState(null)
  const [confirmUnmark, setConfirmUnmark] = useState(null)
  const [dayDiagrams, setDayDiagrams] = useState({})
  const [loadingDiagram, setLoadingDiagram] = useState(null)
  const [sectionQuizLoading, setSectionQuizLoading] = useState(null)
  const [activeSlideViewer, setActiveSlideViewer] = useState(null)
  const [slidesUnlocked, setSlidesUnlocked] = useState(false)
  const [sectionQuizError, setSectionQuizError] = useState(null)
  const [diagramError, setDiagramError] = useState(null)

  // Collapsible day state — open the first incomplete day by default
  const firstIncompleteIdx = days.findIndex(d => !completedDays.includes(d.day_number))
  const [openDays, setOpenDays] = useState(() => {
    const initial = new Set()
    if (firstIncompleteIdx >= 0) initial.add(firstIncompleteIdx)
    else if (days.length > 0) initial.add(days.length - 1) // all done → show last
    return initial
  })

  const toggleDay = (idx) => {
    setOpenDays(prev => {
      const next = new Set(prev)
      if (next.has(idx)) next.delete(idx)
      else next.add(idx)
      return next
    })
  }

  useEffect(() => {
    if (quizActive) setSlidesUnlocked(false)
  }, [quizActive])

  const isVisualPlan = (plan.learning_style_used || planData.learning_style_used) === 'visual'
  const isAudioPlan = (plan.learning_style_used || planData.learning_style_used) === 'audio'
  const isKinestheticPlan = (plan.learning_style_used || planData.learning_style_used) === 'kinesthetic'
  const isReadingPlan = (plan.learning_style_used || planData.learning_style_used) === 'reading'
  const hasSlideContent = !!(planData._slide_content)

  const handleLoadDiagram = async (dayNumber, topic) => {
    if (dayDiagrams[dayNumber]) {
      setDayDiagrams(prev => { const next = { ...prev }; delete next[dayNumber]; return next })
      return
    }
    setLoadingDiagram(dayNumber)
    try {
      const result = await generateConceptDiagram({ topic })
      setDayDiagrams(prev => ({ ...prev, [dayNumber]: result }))
    } catch (err) {
      console.error('Failed to generate diagram for day', dayNumber, err)
      setDiagramError(friendlyError(err))
      setTimeout(() => setDiagramError(null), 6000)
    } finally {
      setLoadingDiagram(null)
    }
  }

  const improvement = (plan.before_score != null && plan.after_score != null)
    ? plan.after_score - plan.before_score
    : null

  const completionPct = Math.round(plan.completion_percentage || 0)
  const totalActivities = days.reduce((sum, d) => sum + (d.activities?.length || 0), 0)
  const totalMinutes = days.reduce((sum, d) => sum + (d.activities || []).reduce((s, a) => s + (a.estimated_minutes || 0), 0), 0)

  return (
    <div className="max-w-4xl mx-auto">

      {/* ─── Before-score prompt ─── */}
      {plan.before_score == null && plan.is_active && (
        <div className="bg-amber-50/50 border border-amber-200/60 rounded-xl p-5 mb-6" data-testid="before-score-prompt">
          <div className="flex items-center gap-2 mb-2">
            <ClipboardIcon className="w-5 h-5 text-amber-600" />
            <h3 className="text-[15px] font-bold text-amber-800">Rate Your Current Knowledge</h3>
          </div>
          <p className="text-[13px] text-amber-700/80 mb-4">
            Before starting this plan, rate your current understanding of this topic (0-100)
          </p>
          <div className="flex items-center gap-3">
            <input
              type="number" min="0" max="100" step="1"
              value={beforeScore}
              onChange={(e) => setBeforeScore(e.target.value)}
              placeholder="0-100"
              className="w-24 bg-white border border-amber-300/80 rounded-lg px-3 py-2 text-center font-mono text-[14px] font-semibold text-navy-900 focus:outline-none focus:border-amber-500 focus:ring-2 focus:ring-amber-100"
            />
            <button
              onClick={() => { const v = parseFloat(beforeScore); if (!isNaN(v) && v >= 0 && v <= 100) { onSubmitBeforeScore(v); setBeforeScore('') } }}
              disabled={beforeScore === '' || isNaN(parseFloat(beforeScore)) || parseFloat(beforeScore) < 0 || parseFloat(beforeScore) > 100}
              className="px-4 py-2 bg-amber-500 hover:bg-amber-600 disabled:bg-amber-300 text-white text-[13px] font-semibold rounded-lg transition-all"
            >Save Baseline</button>
          </div>
        </div>
      )}

      {/* ─── After-score prompt ─── */}
      {(plan.completion_percentage >= 100 && plan.after_score == null) && (
        <div className="bg-emerald-50/50 border border-emerald-200/60 rounded-xl p-5 mb-6" data-testid="after-score-prompt">
          <div className="flex items-center gap-2 mb-2">
            <TrophyIcon className="w-5 h-5 text-emerald-600" />
            <h3 className="text-[15px] font-bold text-emerald-800">Plan Complete! Rate Your Progress</h3>
          </div>
          <p className="text-[13px] text-emerald-700/80 mb-4">
            How would you rate your understanding now? (0-100)
          </p>
          <div className="flex items-center gap-3">
            <input
              type="number" min="0" max="100" step="1"
              value={afterScore}
              onChange={(e) => setAfterScore(e.target.value)}
              placeholder="0-100"
              className="w-24 bg-white border border-emerald-300/80 rounded-lg px-3 py-2 text-center font-mono text-[14px] font-semibold text-navy-900 focus:outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-100"
            />
            <button
              onClick={() => { const v = parseFloat(afterScore); if (!isNaN(v) && v >= 0 && v <= 100) { onSubmitAfterScore(v); setAfterScore('') } }}
              disabled={afterScore === '' || isNaN(parseFloat(afterScore)) || parseFloat(afterScore) < 0 || parseFloat(afterScore) > 100}
              className="px-4 py-2 bg-emerald-500 hover:bg-emerald-600 disabled:bg-emerald-300 text-white text-[13px] font-semibold rounded-lg transition-all"
            >Submit Final Score</button>
          </div>
          {onTakeQuiz && (
            <div className="mt-4 pt-4 border-t border-emerald-200/60">
              <p className="text-[12px] text-emerald-700/70 mb-3">Or test your knowledge objectively with an AI-generated quiz</p>
              <button
                onClick={() => onTakeQuiz(plan)}
                className="flex items-center gap-2 px-4 py-2 bg-violet-600 hover:bg-violet-700 text-white text-[13px] font-semibold rounded-lg transition-all"
              >
                <ClipboardIcon className="w-4 h-4" />
                Take Knowledge Quiz
              </button>
            </div>
          )}
        </div>
      )}

      {/* ─── Results badge ─── */}
      {(plan.before_score != null && plan.after_score != null) && (
        <div className="bg-navy-800/[0.03] border border-navy-200/60 rounded-xl p-5 mb-6" data-testid="score-results-badge">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-[15px] font-bold text-navy-900 mb-1">Knowledge Improvement</h3>
              <p className="text-[13px] text-surface-400">
                Before: <span className="font-semibold text-navy-800">{plan.before_score}</span>
                {' '}&rarr;{' '}
                After: <span className="font-semibold text-navy-800">{plan.after_score}</span>
              </p>
            </div>
            <div className={`font-mono text-xl font-bold px-4 py-2 rounded-xl ${
              improvement > 0
                ? 'bg-emerald-50 text-emerald-600 border border-emerald-200/60'
                : improvement < 0
                  ? 'bg-red-50 text-red-600 border border-red-200/60'
                  : 'bg-surface-100 text-surface-400 border border-surface-200'
            }`}>
              {improvement > 0 ? '+' : ''}{improvement.toFixed(1)}%
            </div>
          </div>
        </div>
      )}

      {/* ═══════════════════════════════════════════════════
          PLAN HEADER — visual, scannable, with progress bar
         ═══════════════════════════════════════════════════ */}
      <div className="mb-8">
        <div className="flex items-start justify-between gap-4 mb-3">
          <h1 className="font-display text-[1.5rem] font-bold text-navy-900 leading-tight">{planData.title || plan.topic}</h1>
          <button
            onClick={() => window.print()}
            className="flex-shrink-0 flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[12px] font-semibold text-navy-600 hover:text-navy-800 hover:bg-surface-100 border border-surface-200/80 transition-colors print:hidden"
          >
            <PrinterIcon className="w-4 h-4" />
            Print
          </button>
        </div>

        {/* Plan description — truncated */}
        {planData.description && (
          <ExpandableText text={planData.description} className="mb-4" />
        )}

        {/* ─── Visual stat strip ─── */}
        <div className="grid grid-cols-4 gap-3 mb-4">
          <div className="bg-surface-50 border border-surface-200/60 rounded-xl px-3 py-2.5 text-center">
            <p className="text-[18px] font-bold text-navy-900 font-display">{days.length}</p>
            <p className="text-[10px] text-surface-400 font-semibold uppercase tracking-wider">Days</p>
          </div>
          <div className="bg-surface-50 border border-surface-200/60 rounded-xl px-3 py-2.5 text-center">
            <p className="text-[18px] font-bold text-navy-900 font-display">{totalActivities}</p>
            <p className="text-[10px] text-surface-400 font-semibold uppercase tracking-wider">Activities</p>
          </div>
          <div className="bg-surface-50 border border-surface-200/60 rounded-xl px-3 py-2.5 text-center">
            <p className="text-[18px] font-bold text-navy-900 font-display">{totalMinutes > 60 ? `${(totalMinutes / 60).toFixed(1)}h` : `${totalMinutes}m`}</p>
            <p className="text-[10px] text-surface-400 font-semibold uppercase tracking-wider">Est. Time</p>
          </div>
          <div className="bg-surface-50 border border-surface-200/60 rounded-xl px-3 py-2.5 text-center">
            <p className={`text-[18px] font-bold font-display ${completionPct >= 100 ? 'text-emerald-600' : completionPct > 0 ? 'text-navy-900' : 'text-surface-400'}`}>{completionPct}%</p>
            <p className="text-[10px] text-surface-400 font-semibold uppercase tracking-wider">Complete</p>
          </div>
        </div>

        {/* Progress bar */}
        <div className="h-2 bg-surface-200/60 rounded-full overflow-hidden mb-4">
          <div
            className={`h-full rounded-full transition-all duration-700 ease-out ${completionPct >= 100 ? 'bg-emerald-500' : 'bg-navy-600'}`}
            style={{ width: `${completionPct}%` }}
          />
        </div>

        {/* Metadata pills */}
        <div className="flex items-center gap-2 flex-wrap">
          <span className={`px-2.5 py-1 rounded-lg text-[11px] font-semibold ${getDifficultyColor(planData.difficulty_level || 'intermediate')} capitalize`}>{planData.difficulty_level || 'Intermediate'}</span>
          {plan.learning_style_used && plan.learning_style_used !== 'auto' && (
            <span className={`inline-flex items-center px-2.5 py-1 rounded-lg text-[11px] font-semibold ${
              plan.learning_style_used === 'visual' ? 'bg-indigo-100 text-indigo-700' :
              plan.learning_style_used === 'audio' ? 'bg-amber-100 text-amber-700' :
              plan.learning_style_used === 'reading' ? 'bg-emerald-100 text-emerald-700' :
              plan.learning_style_used === 'kinesthetic' ? 'bg-violet-100 text-violet-700' :
              'bg-slate-100 text-slate-700'
            }`}>
              {plan.learning_style_used === 'kinesthetic' ? 'Hands-on' : plan.learning_style_used} learner
            </span>
          )}
        </div>

        {/* Learning Objectives — compact horizontal chips */}
        {planData.learning_objectives && planData.learning_objectives.length > 0 && (
          <div className="mt-5">
            <h3 className="text-[11px] font-bold text-surface-400 uppercase tracking-wider mb-2.5 flex items-center gap-1.5">
              <TargetIcon className="w-3.5 h-3.5" />
              Learning Objectives
            </h3>
            <div className="flex flex-wrap gap-2">
              {planData.learning_objectives.map((obj, idx) => (
                <span key={idx} className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-[12px] text-navy-700 bg-navy-800/[0.04] border border-navy-200/40">
                  <svg className="w-3 h-3 text-emerald-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                  </svg>
                  <span className="line-clamp-1">{obj}</span>
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* ─── Slide Grounding Warning ─── */}
      {planData._slide_grounding && !planData._slide_grounding.grounded && (
        <div className="relative bg-gradient-to-r from-amber-50/80 to-orange-50/40 border border-amber-200/60 rounded-2xl p-5 mb-6 overflow-hidden animate-fade-up-0">
          <div className="absolute top-0 right-0 w-32 h-32 pointer-events-none opacity-30" style={{ background: 'radial-gradient(ellipse at 100% 0%, rgba(245, 158, 11, 0.15), transparent 70%)' }} />
          <div className="relative flex items-start gap-3.5">
            <div className="w-9 h-9 rounded-xl bg-amber-100 border border-amber-200/60 flex items-center justify-center flex-shrink-0 shadow-sm">
              <svg className="w-5 h-5 text-amber-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8">
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
              </svg>
            </div>
            <div className="flex-1">
              <div className="flex items-center gap-2.5 mb-1.5">
                <p className="text-[13px] font-bold text-amber-900">Low Slide Grounding</p>
                <span className="text-[11px] font-mono font-bold px-2 py-0.5 rounded-lg bg-amber-200/60 text-amber-700">
                  {Math.round((planData._slide_grounding.score || 0) * 100)}%
                </span>
              </div>
              <p className="text-[12px] text-amber-700/80 leading-relaxed">
                {planData._slide_grounding.grounding_warning || 'Some activities may use general knowledge instead of your specific uploaded material.'}
              </p>
              <div className="mt-3 flex items-center gap-2">
                <div className="flex-1 h-1.5 bg-amber-200/50 rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all duration-500 bg-gradient-to-r from-amber-400 to-amber-500"
                    style={{ width: `${Math.round((planData._slide_grounding.score || 0) * 100)}%` }}
                  />
                </div>
                <span className="text-[10px] text-amber-600 font-semibold">
                  {planData._slide_grounding.grounded_count || 0}/{planData._slide_grounding.total_count || 0} grounded
                </span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ═══════════════════════════════════════════════════
          DAY-BY-DAY — collapsible accordion cards
         ═══════════════════════════════════════════════════ */}
      <div className="space-y-3">
        {days.map((day, idx) => {
          const isCompleted = completedDays.includes(day.day_number)
          const isOpen = openDays.has(idx)
          let audioCountForDay = 0
          const dayMinutes = (day.activities || []).reduce((s, a) => s + (a.estimated_minutes || 0), 0)
          const activityCount = day.activities?.length || 0

          return (
            <div key={idx} className={`rounded-2xl border overflow-hidden transition-all ${
              justCompleted === day.day_number ? 'animate-glow-pulse' : ''
            } ${
              isCompleted
                ? 'border-emerald-200/60 bg-emerald-50/20'
                : 'border-surface-200/80 bg-white'
            }`}>

              {/* ─── Day Header (always visible, clickable to expand) ─── */}
              <button
                type="button"
                onClick={() => toggleDay(idx)}
                className={`w-full px-5 py-4 flex items-center gap-4 text-left transition-colors ${
                  isCompleted ? 'hover:bg-emerald-50/40' : 'hover:bg-surface-50/50'
                }`}
              >
                {/* Day number badge */}
                <div className={`w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 font-display text-[13px] font-bold transition-all ${
                  isCompleted
                    ? 'bg-emerald-500 text-white shadow-sm shadow-emerald-500/20'
                    : 'bg-navy-800 text-white'
                }`}>
                  {isCompleted ? (
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                    </svg>
                  ) : (
                    day.day_number
                  )}
                </div>

                {/* Title + meta */}
                <div className="flex-1 min-w-0">
                  <h3 className={`text-[14px] font-bold truncate ${isCompleted ? 'text-emerald-800' : 'text-navy-900'}`}>
                    {day.title}
                  </h3>
                  <div className="flex items-center gap-3 mt-0.5">
                    <span className="text-[11px] text-surface-400">{activityCount} {activityCount === 1 ? 'activity' : 'activities'}</span>
                    <span className="text-[11px] text-surface-300">&middot;</span>
                    <span className="text-[11px] text-surface-400 font-mono">{dayMinutes}m</span>
                    {day.focus && day.focus !== day.title && (
                      <>
                        <span className="text-[11px] text-surface-300">&middot;</span>
                        <span className="text-[11px] text-surface-400 truncate max-w-[200px]">{day.focus}</span>
                      </>
                    )}
                  </div>
                </div>

                {/* Action buttons */}
                <div className="flex items-center gap-2 flex-shrink-0" onClick={e => e.stopPropagation()}>
                  {/* Mark Done / Completed */}
                  <button
                    onClick={async (e) => {
                      e.stopPropagation()
                      if (isCompleted) { setConfirmUnmark(day.day_number); return }
                      setSavingDay(day.day_number)
                      try {
                        await onDayComplete(day.day_number)
                        setJustCompleted(day.day_number)
                        setTimeout(() => setJustCompleted(null), 1500)
                      } finally { setSavingDay(null) }
                    }}
                    disabled={savingDay !== null}
                    className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[11px] font-semibold transition-all ${
                      savingDay === day.day_number
                        ? 'bg-surface-200 text-surface-400 cursor-wait'
                        : isCompleted
                          ? 'bg-emerald-100 text-emerald-700 hover:bg-emerald-200'
                          : 'bg-surface-100 text-navy-600 hover:bg-navy-800/[0.06] border border-surface-200/80'
                    } disabled:opacity-60`}
                  >
                    {savingDay === day.day_number ? (
                      <div className="w-3.5 h-3.5 border-2 border-surface-300 border-t-navy-600 rounded-full animate-spin" />
                    ) : (
                      <svg className={`w-3.5 h-3.5 ${isCompleted ? 'text-emerald-600' : 'text-surface-400'}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                      </svg>
                    )}
                    {savingDay === day.day_number ? '...' : isCompleted ? 'Done' : 'Mark Done'}
                  </button>

                  {/* Diagram button (visual plans) */}
                  {isVisualPlan && (
                    <button
                      onClick={(e) => { e.stopPropagation(); handleLoadDiagram(day.day_number, day.focus || day.title) }}
                      disabled={loadingDiagram === day.day_number}
                      className={`flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-[11px] font-semibold transition-all border ${
                        dayDiagrams[day.day_number]
                          ? 'bg-teal-50 text-teal-700 border-teal-200'
                          : 'bg-white text-teal-600 border-teal-200/60 hover:bg-teal-50'
                      } disabled:opacity-60`}
                    >
                      {loadingDiagram === day.day_number ? (
                        <div className="w-3 h-3 border-2 border-teal-300 border-t-teal-600 rounded-full animate-spin" />
                      ) : (
                        <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                          <path strokeLinecap="round" strokeLinejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z" />
                          <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                        </svg>
                      )}
                    </button>
                  )}
                </div>

                {/* Chevron */}
                <ChevronIcon className="w-5 h-5 text-surface-300 flex-shrink-0" open={isOpen} />
              </button>

              {diagramError && loadingDiagram === null && (
                <div className="px-5 pb-2">
                  <span className="text-[11px] text-red-500 font-medium animate-fade-up-0">{diagramError}</span>
                </div>
              )}

              {/* Unmark confirmation */}
              {confirmUnmark === day.day_number && (
                <div className="mx-5 mb-3 bg-amber-50/50 border border-amber-200/60 rounded-lg px-4 py-2.5 flex items-center justify-between">
                  <span className="text-[12px] font-medium text-amber-700">Unmark this day as complete?</span>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={async () => {
                        setSavingDay(day.day_number)
                        try { await onDayComplete(day.day_number) }
                        finally { setSavingDay(null); setConfirmUnmark(null) }
                      }}
                      className="text-[11px] font-semibold text-amber-600 hover:text-amber-700 transition-colors"
                    >Yes, unmark</button>
                    <button
                      onClick={() => setConfirmUnmark(null)}
                      className="text-[11px] font-semibold text-surface-400 hover:text-surface-500 transition-colors"
                    >Cancel</button>
                  </div>
                </div>
              )}

              {/* Inline Concept Diagram (shows even when collapsed) */}
              {dayDiagrams[day.day_number] && (
                <div className="mx-5 mb-3">
                  <ConceptDiagram diagram={dayDiagrams[day.day_number]} compact />
                </div>
              )}

              {/* ─── Collapsible Body ─── */}
              {isOpen && (
                <div className="px-5 pb-5 space-y-2.5 border-t border-surface-100">
                  <div className="h-3" /> {/* spacer */}
                  {day.activities && day.activities.map((activity, actIdx) => {
                    const accent = activityAccent[activity.activity_type] || defaultAccent

                    return (
                      <div key={actIdx} className={`rounded-xl border-l-[3px] ${accent.border} ${accent.bg} border border-surface-200/40 p-4`}>
                        {/* Activity header row */}
                        <div className="flex items-start gap-3">
                          {/* Type icon badge */}
                          <div className={`w-8 h-8 rounded-lg ${accent.icon} flex items-center justify-center flex-shrink-0`}>
                            <span className="text-[10px] font-bold uppercase tracking-wide">{getActivityIcon(activity.activity_type)}</span>
                          </div>

                          <div className="flex-1 min-w-0">
                            <div className="flex items-start justify-between gap-2 mb-1">
                              <h4 className="text-[13px] font-semibold text-navy-900 leading-snug">{activity.title}</h4>
                              <div className="flex items-center gap-2 flex-shrink-0">
                                <span className={`text-[10px] px-2 py-0.5 rounded-md font-semibold ${getDifficultyColor(activity.difficulty)}`}>
                                  {activity.difficulty}
                                </span>
                              </div>
                            </div>

                            {/* Time bar */}
                            <TimeBadge minutes={activity.estimated_minutes} />

                            {/* Description — truncated with expand */}
                            <ExpandableText text={activity.description} className="mt-2" />

                            {/* Page Range Badge + Slide Viewer */}
                            {activity.page_range && hasSlideContent && (() => {
                              const viewerKey = `${day.day_number}-${actIdx}`
                              const isViewerOpen = activeSlideViewer === viewerKey
                              const slideResource = resources.find(r => r.resource_type === 'uploaded_slides' && r.resource_url)
                              const API_BASE = import.meta.env.VITE_API_URL || ''
                              const docUrl = slideResource?.resource_url
                                ? (slideResource.resource_url.startsWith('http') ? slideResource.resource_url : `${API_BASE}${slideResource.resource_url}`)
                                : null

                              return (
                                <div className="mt-2">
                                  <button
                                    onClick={() => setActiveSlideViewer(isViewerOpen ? null : viewerKey)}
                                    className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-[11px] font-bold transition-all border shadow-sm active:scale-[0.97] ${
                                      isViewerOpen
                                        ? 'bg-navy-800 text-white border-navy-800 shadow-navy-900/20'
                                        : 'bg-gradient-to-r from-navy-50 to-surface-50 text-navy-700 border-navy-200/50 hover:border-navy-300/60 hover:shadow-md hover:shadow-navy-900/5'
                                    }`}
                                  >
                                    <svg className={`w-3.5 h-3.5 ${isViewerOpen ? 'text-white/80' : 'text-navy-500'}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8">
                                      <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
                                    </svg>
                                    <span>Pages {activity.page_range}</span>
                                    {isViewerOpen && (
                                      <svg className="w-3 h-3 ml-0.5 text-white/70" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5">
                                        <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                                      </svg>
                                    )}
                                  </button>
                                  {isViewerOpen && docUrl && (
                                    <div className="mt-2 relative">
                                      {quizActive && !slidesUnlocked && (
                                        <div className="absolute inset-0 z-20 rounded-2xl overflow-hidden animate-fade-up-0">
                                          <div className="absolute inset-0 bg-navy-950/60 backdrop-blur-xl" />
                                          <div className="relative z-10 flex flex-col items-center justify-center h-full min-h-[280px] p-8 text-center">
                                            <div className="relative mb-5">
                                              <div className="absolute inset-0 w-16 h-16 rounded-2xl bg-amber-400/20 blur-xl" />
                                              <div className="relative w-16 h-16 rounded-2xl bg-gradient-to-br from-navy-800 to-navy-900 border border-white/10 flex items-center justify-center shadow-lg">
                                                <svg className="w-7 h-7 text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8">
                                                  <path strokeLinecap="round" strokeLinejoin="round" d="M16.5 10.5V6.75a4.5 4.5 0 10-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H6.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z" />
                                                </svg>
                                              </div>
                                            </div>
                                            <h4 className="text-[15px] font-bold text-white mb-1.5">Slides Paused</h4>
                                            <p className="text-[12px] text-white/50 max-w-[240px] leading-relaxed mb-5">
                                              Quiz in progress — slides are hidden to keep your assessment fair
                                            </p>
                                            <button
                                              onClick={() => setSlidesUnlocked(true)}
                                              className="group flex items-center gap-2 px-4 py-2 rounded-xl bg-white/[0.08] hover:bg-white/[0.14] border border-white/[0.08] hover:border-white/[0.15] text-white/70 hover:text-white transition-all text-[12px] font-semibold"
                                            >
                                              <svg className="w-3.5 h-3.5 text-white/40 group-hover:text-amber-400 transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                                                <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 10.5V6.75a4.5 4.5 0 119 0v3.75M3.75 21.75h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H3.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z" />
                                              </svg>
                                              View Anyway
                                            </button>
                                          </div>
                                        </div>
                                      )}
                                      <ErrorBoundary inline label="slide viewer">
                                        <Suspense fallback={
                                          <div className="flex items-center gap-2 p-4 bg-surface-50 border border-surface-200/60 rounded-lg">
                                            <div className="w-4 h-4 border-2 border-navy-300 border-t-navy-600 rounded-full animate-spin" />
                                            <span className="text-[12px] text-navy-500 font-medium">Loading slide viewer...</span>
                                          </div>
                                        }>
                                          <SlideRangeViewer
                                            documentUrl={docUrl}
                                            pageRange={activity.page_range}
                                            onClose={() => setActiveSlideViewer(null)}
                                          />
                                        </Suspense>
                                      </ErrorBoundary>
                                    </div>
                                  )}
                                  {isViewerOpen && !docUrl && (
                                    <p className="mt-1 text-[11px] text-surface-400">Document not available for inline viewing.</p>
                                  )}
                                </div>
                              )
                            })()}

                            {/* Inline Resource Card + Audio/Exercises/Cards */}
                            {(() => {
                              const dayResources = resources.filter(
                                r => r.day_number === day.day_number && r.order_in_day === actIdx
                              )
                              let matchingResource = dayResources.length > 0
                                ? (dayResources.find(r => {
                                    if (activity.activity_type === 'video') return r.resource_type === 'youtube_video'
                                    if (activity.activity_type === 'audio') return r.resource_type === 'youtube_video' || r.resource_type === 'article' || r.resource_type === 'documentation'
                                    if (['reading', 'review', 'written'].includes(activity.activity_type)) return r.resource_type === 'article' || r.resource_type === 'documentation' || r.resource_type === 'uploaded_slides'
                                    if (activity.activity_type === 'practice' || activity.activity_type === 'interactive') return r.resource_type === 'practice' || r.resource_type === 'interactive' || r.resource_type === 'youtube_video'
                                    return r.resource_url
                                  }) || dayResources.find(r => r.resource_url) || dayResources[0])
                                : null

                              // Fallback: use any resource from this day, or any plan resource
                              if (!matchingResource) {
                                matchingResource = resources.find(r => r.day_number === day.day_number)
                                  || resources.find(r => r.id) || null
                              }

                              const showAudio = true
                              const showExercises = isKinestheticPlan || ['practice', 'interactive', 'project'].includes(activity.activity_type)
                              const showStudyCards = isReadingPlan || ['reading', 'review', 'written'].includes(activity.activity_type)

                              // Skip entirely only if nothing to show
                              if (!matchingResource && !showAudio && !showExercises && !showStudyCards) return null

                              const isFirstAudioOfDay = isAudioPlan && audioCountForDay === 0
                              if (isAudioPlan) audioCountForDay++

                              return (
                                <div className="mt-3 space-y-2">
                                  {matchingResource && (
                                    <ResourceCard resource={matchingResource} onPlayFullScreen={onPlayVideo} compact />
                                  )}
                                  {showAudio && (
                                    <AudioPlayer
                                      planId={plan.id}
                                      resource={matchingResource}
                                      topic={plan.topic}
                                      activityDescription={activity.description}
                                      pageRange={activity.page_range}
                                      isPrimary={isFirstAudioOfDay}
                                    />
                                  )}
                                  {showExercises && (
                                    <PracticeExercise
                                      planId={plan.id}
                                      resource={matchingResource}
                                      topic={plan.topic}
                                      activityDescription={activity.description}
                                      pageRange={activity.page_range}
                                    />
                                  )}
                                  {showStudyCards && (
                                    <StudyCards
                                      planId={plan.id}
                                      resource={matchingResource}
                                      topic={plan.topic}
                                      activityDescription={activity.description}
                                      pageRange={activity.page_range}
                                    />
                                  )}
                                  {/* Per-section quiz */}
                                  {hasSlideContent && (activity.page_range || /(?:slide|page)s?\s*\d/i.test(activity.description || '')) && onTakeQuiz && (
                                    <button
                                      onClick={async () => {
                                        const key = `${day.day_number}-${actIdx}`
                                        setSectionQuizLoading(key)
                                        try {
                                          const quizResult = await generateSectionQuiz(plan.id, activity.page_range || null, activity.description || '', 5)
                                          // API returns the quiz object with `id` (older callers expected `quiz_id`).
                                          const sectionQuizId = quizResult?.id || quizResult?.quiz_id
                                          if (sectionQuizId) {
                                            onTakeQuiz({ ...plan, _sectionQuizId: sectionQuizId, _sectionLabel: activity.page_range ? `Pages ${activity.page_range}` : 'Section' })
                                          }
                                        } catch (err) {
                                          console.error('Section quiz generation failed:', err)
                                          setSectionQuizError(`${day.day_number}-${actIdx}:${friendlyError(err)}`)
                                          setTimeout(() => setSectionQuizError(null), 6000)
                                        } finally { setSectionQuizLoading(null) }
                                      }}
                                      disabled={sectionQuizLoading === `${day.day_number}-${actIdx}`}
                                      className="flex items-center gap-1.5 w-full justify-center px-3 py-2 bg-violet-50 hover:bg-violet-100 disabled:bg-violet-50/60 border border-violet-200/60 text-violet-700 rounded-lg text-[11px] font-semibold transition-all"
                                    >
                                      {sectionQuizLoading === `${day.day_number}-${actIdx}` ? (
                                        <>
                                          <div className="w-3 h-3 border-2 border-violet-300 border-t-violet-600 rounded-full animate-spin" />
                                          Generating section quiz...
                                        </>
                                      ) : (
                                        <>
                                          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8">
                                            <path strokeLinecap="round" strokeLinejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                                          </svg>
                                          Quiz this section{activity.page_range ? ` (Pages ${activity.page_range})` : ''}
                                        </>
                                      )}
                                    </button>
                                  )}
                                  {sectionQuizError?.startsWith(`${day.day_number}-${actIdx}:`) && (
                                    <p className="flex items-center gap-1.5 text-[11px] text-red-500 font-medium mt-1.5 animate-fade-up-0">
                                      <svg className="w-3.5 h-3.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                                        <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
                                      </svg>
                                      {sectionQuizError.split(':').slice(1).join(':')}
                                    </p>
                                  )}
                                </div>
                              )
                            })()}

                            {/* Resources Needed */}
                            {activity.resources_needed && activity.resources_needed.length > 0 && (
                              <div className="mt-2 flex items-center gap-1.5 flex-wrap">
                                <span className="text-[11px] text-surface-400">Resources:</span>
                                {activity.resources_needed.map((res, rIdx) => (
                                  <span key={rIdx} className="text-[10px] px-2 py-0.5 bg-surface-100 text-surface-400 rounded-md font-medium">{res}</span>
                                ))}
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    )
                  })}

                  {/* Success Criteria */}
                  {day.success_criteria && (
                    <div className="bg-navy-800/[0.03] border-l-3 border-navy-500 rounded-lg p-4 mt-1">
                      <h5 className="text-[12px] font-bold text-navy-800 mb-1 flex items-center gap-1.5">
                        <TargetIcon className="w-3.5 h-3.5" />
                        Success Criteria
                      </h5>
                      <p className="text-[12px] text-navy-700/80">{day.success_criteria}</p>
                    </div>
                  )}
                </div>
              )}
            </div>
          )
        })}
      </div>

      {/* ─── Final Assessment + Quiz ─── */}
      {planData.final_assessment && (
        <div className="mt-8 bg-emerald-50/40 border border-emerald-200/60 rounded-xl p-5">
          <h3 className="text-[15px] font-bold text-emerald-800 mb-2 flex items-center gap-2">
            <TrophyIcon className="w-5 h-5" />
            Final Assessment
          </h3>
          <p className="text-[13px] text-emerald-700/80 leading-relaxed">{planData.final_assessment}</p>

          {onTakeQuiz && (
            <button
              onClick={() => onTakeQuiz(plan)}
              className="mt-4 inline-flex items-center gap-2 px-4 py-2.5 bg-violet-600 hover:bg-violet-700 text-white rounded-xl text-[13px] font-semibold transition-all"
            >
              <ClipboardIcon className="w-4 h-4" />
              Take Knowledge Quiz
            </button>
          )}
        </div>
      )}

      {/* ─── Next Steps ─── */}
      {planData.next_steps && (
        <div className="mt-4 bg-navy-800/[0.03] border border-navy-200/60 rounded-xl p-5">
          <h3 className="text-[15px] font-bold text-navy-900 mb-2 flex items-center gap-2">
            <RocketIcon className="w-5 h-5 text-navy-600" />
            What's Next?
          </h3>
          <p className="text-[13px] text-navy-700/80 leading-relaxed">{planData.next_steps}</p>
        </div>
      )}
    </div>
  )
}
