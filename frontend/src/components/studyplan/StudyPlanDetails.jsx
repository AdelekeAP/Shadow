import { useState } from 'react'
import { linkifyText, getActivityIcon, getDifficultyColor } from './studyPlanHelpers.jsx'
import ResourceCard from './ResourceCard'
import AudioPlayer from './AudioPlayer'

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

export default function StudyPlanDetails({ plan, onDayComplete, onPlayVideo, onSubmitBeforeScore, onSubmitAfterScore, onTakeQuiz }) {
  const planData = plan.plan_data || {}
  const days = planData.days || []
  const completedDays = plan.completed_days || []
  const resources = plan.resources || []

  const [beforeScore, setBeforeScore] = useState('')
  const [afterScore, setAfterScore] = useState('')
  const [savingDay, setSavingDay] = useState(null)
  const [justCompleted, setJustCompleted] = useState(null)
  const [confirmUnmark, setConfirmUnmark] = useState(null)

  const improvement = (plan.before_score != null && plan.after_score != null)
    ? plan.after_score - plan.before_score
    : null

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
            Before starting this plan, rate your current understanding of this topic (0–100)
          </p>
          <div className="flex items-center gap-3">
            <input
              type="number" min="0" max="100" step="1"
              value={beforeScore}
              onChange={(e) => setBeforeScore(e.target.value)}
              placeholder="0–100"
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
            How would you rate your understanding now? (0–100)
          </p>
          <div className="flex items-center gap-3">
            <input
              type="number" min="0" max="100" step="1"
              value={afterScore}
              onChange={(e) => setAfterScore(e.target.value)}
              placeholder="0–100"
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

      {/* ─── Plan Header ─── */}
      <div className="mb-8">
        <div className="flex items-start justify-between gap-4">
          <h1 className="font-display text-[1.5rem] font-bold text-navy-900 mb-2 leading-tight">{planData.title || plan.topic}</h1>
          <button
            onClick={() => window.print()}
            className="flex-shrink-0 flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[12px] font-semibold text-navy-600 hover:text-navy-800 hover:bg-surface-100 border border-surface-200/80 transition-colors print:hidden"
          >
            <PrinterIcon className="w-4 h-4" />
            Print Plan
          </button>
        </div>
        <p className="text-[13px] text-surface-400 leading-relaxed mb-4">{linkifyText(planData.description)}</p>

        <div className="flex items-center gap-2 flex-wrap">
          <span className="px-2.5 py-1 rounded-lg text-[11px] font-semibold bg-navy-800/[0.06] text-navy-700">{plan.duration_days} days</span>
          <span className="px-2.5 py-1 rounded-lg text-[11px] font-semibold bg-surface-100 text-surface-400 capitalize">{planData.difficulty_level || 'Intermediate'}</span>
          <span className="px-2.5 py-1 rounded-lg text-[11px] font-semibold bg-emerald-50 text-emerald-600">{planData.estimated_hours_total || '12-16 hours'}</span>
          <span className="px-2.5 py-1 rounded-lg text-[11px] font-semibold bg-amber-50 text-amber-600">{Math.round(plan.completion_percentage || 0)}% complete</span>
        </div>

        {/* Learning Objectives */}
        {planData.learning_objectives && planData.learning_objectives.length > 0 && (
          <div className="mt-5 bg-surface-50/50 border border-surface-200/60 rounded-xl p-4">
            <h3 className="text-[13px] font-bold text-navy-900 mb-2 flex items-center gap-2">
              <TargetIcon className="w-4 h-4 text-navy-600" />
              Learning Objectives
            </h3>
            <ul className="space-y-1.5">
              {planData.learning_objectives.map((obj, idx) => (
                <li key={idx} className="text-[13px] text-surface-400 flex items-start gap-2">
                  <svg className="w-3.5 h-3.5 text-emerald-500 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                  </svg>
                  <span>{obj}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* ─── Day-by-Day Breakdown ─── */}
      <div className="relative pl-10 sm:pl-12">
        {/* Timeline vertical line */}
        <div className="absolute left-[15px] sm:left-[19px] top-2 bottom-2 w-[2px] rounded-full bg-surface-200/80" />

        <div className="space-y-5">
        {days.map((day, idx) => {
          const isCompleted = completedDays.includes(day.day_number)
          const prevCompleted = idx > 0 && completedDays.includes(days[idx - 1].day_number)

          return (
            <div key={idx} className="relative">
              {/* Timeline node */}
              <div className={`absolute -left-10 sm:-left-12 top-5 w-[32px] sm:w-[40px] flex items-center justify-center`}>
                <div className={`w-[14px] h-[14px] rounded-full border-[2.5px] transition-all ${
                  justCompleted === day.day_number
                    ? 'border-emerald-400 bg-emerald-400 animate-check-pop scale-110'
                    : isCompleted
                      ? 'border-emerald-400 bg-emerald-400'
                      : 'border-surface-300 bg-white'
                }`}>
                  {isCompleted && (
                    <svg className="w-full h-full text-white p-[1px]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="4">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                    </svg>
                  )}
                </div>
              </div>
              {/* Emerald connector segment for completed days */}
              {isCompleted && idx > 0 && prevCompleted && (
                <div className="absolute -left-10 sm:-left-12 top-0 w-[32px] sm:w-[40px] flex justify-center" style={{ height: '20px', marginTop: '-20px' }}>
                  <div className="w-[2px] bg-emerald-300 rounded-full" style={{ height: '100%' }} />
                </div>
              )}

              <div
                className={`rounded-xl border overflow-hidden transition-all ${
                  justCompleted === day.day_number ? 'animate-glow-pulse' : ''
                } ${
                  isCompleted
                    ? 'border-emerald-200/60 bg-emerald-50/30'
                    : 'border-surface-200/80 bg-white hover:border-navy-300/40 hover:shadow-sm'
                }`}
              >
              {/* Day Header */}
              <div className={`px-5 py-4 ${isCompleted ? 'bg-emerald-50/50' : 'bg-surface-50/50'}`}>
                <div className="flex items-center justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2.5 mb-1">
                      <span className={`text-[11px] font-bold px-2.5 py-1 rounded-lg ${
                        isCompleted ? 'bg-emerald-500 text-white' : 'bg-navy-800 text-white'
                      }`}>Day {day.day_number}</span>
                      <h3 className="text-[14px] font-bold text-navy-900 truncate">{day.title}</h3>
                    </div>
                    <p className="text-[12px] text-surface-400">{day.focus}</p>
                  </div>

                  <button
                    onClick={async () => {
                      const wasCompleted = completedDays.includes(day.day_number)
                      if (wasCompleted) {
                        setConfirmUnmark(day.day_number)
                        return
                      }
                      setSavingDay(day.day_number)
                      try {
                        await onDayComplete(day.day_number)
                        setJustCompleted(day.day_number)
                        setTimeout(() => setJustCompleted(null), 1500)
                      } finally { setSavingDay(null) }
                    }}
                    disabled={savingDay !== null}
                    className={`ml-4 flex items-center gap-1.5 px-3.5 py-2 rounded-lg text-[12px] font-semibold transition-all ${
                      savingDay === day.day_number
                        ? 'bg-surface-200 text-surface-400 cursor-wait'
                        : isCompleted
                          ? 'bg-emerald-500 hover:bg-emerald-600 text-white'
                          : 'bg-white hover:bg-navy-800/[0.03] text-navy-700 border border-navy-200/60'
                    } disabled:opacity-60`}
                  >
                    {savingDay === day.day_number ? (
                      <div className="w-4 h-4 border-2 border-surface-300 border-t-navy-600 rounded-full animate-spin" />
                    ) : justCompleted === day.day_number ? (
                      <svg className="w-4 h-4 animate-check-pop" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                      </svg>
                    ) : isCompleted ? (
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                      </svg>
                    ) : (
                      <div className="w-4 h-4 rounded-full border-2 border-navy-300" />
                    )}
                    {savingDay === day.day_number ? 'Saving...' : isCompleted ? 'Completed' : 'Mark Done'}
                  </button>
                </div>
              </div>

              {/* Unmark confirmation */}
              {confirmUnmark === day.day_number && (
                <div className="mx-5 mt-3 bg-amber-50/50 border border-amber-200/60 rounded-lg px-4 py-2.5 flex items-center justify-between">
                  <span className="text-[12px] font-medium text-amber-700">Unmark this day as complete?</span>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={async () => {
                        setSavingDay(day.day_number)
                        try {
                          await onDayComplete(day.day_number)
                        } finally {
                          setSavingDay(null)
                          setConfirmUnmark(null)
                        }
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

              {/* Activities */}
              <div className="px-5 py-4 space-y-3">
                {day.activities && day.activities.map((activity, actIdx) => (
                  <div key={actIdx} className="bg-surface-50/50 border border-surface-200/60 rounded-lg p-4">
                    <div className="flex items-start gap-3">
                      <span className="text-[11px] font-bold text-navy-700 bg-navy-50 border border-navy-100 rounded-md px-2 py-1 mt-0.5 uppercase tracking-wide">{getActivityIcon(activity.activity_type)}</span>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-start justify-between gap-2 mb-1.5">
                          <h4 className="text-[13px] font-semibold text-navy-900">{activity.title}</h4>
                          <div className="flex items-center gap-2 flex-shrink-0">
                            <span className={`text-[10px] px-2 py-0.5 rounded-md font-semibold ${getDifficultyColor(activity.difficulty)}`}>
                              {activity.difficulty}
                            </span>
                            <span className="text-[11px] text-surface-400 font-mono">{activity.estimated_minutes}m</span>
                          </div>
                        </div>

                        <p className="text-[12px] text-surface-400 leading-relaxed mb-2">{linkifyText(activity.description)}</p>

                        {/* Inline Resource Card + Audio */}
                        {(() => {
                          const dayResources = resources.filter(
                            r => r.day_number === day.day_number && r.order_in_day === actIdx
                          )
                          // Pick the best resource for this activity type
                          const matchingResource = dayResources.length > 0
                            ? (dayResources.find(r => {
                                if (activity.activity_type === 'video') return r.resource_type === 'youtube_video'
                                if (activity.activity_type === 'reading' || activity.activity_type === 'review') return r.resource_type === 'article' || r.resource_type === 'documentation' || r.resource_type === 'uploaded_slides'
                                if (activity.activity_type === 'practice' || activity.activity_type === 'interactive') return r.resource_type === 'practice' || r.resource_type === 'interactive'
                                return r.resource_url // any resource with a URL
                              }) || dayResources.find(r => r.resource_url) || dayResources[0])
                            : null
                          if (!matchingResource) return null

                          const showAudio = ['reading', 'review'].includes(activity.activity_type)

                          return (
                            <div className="mt-2 space-y-2">
                              <ResourceCard resource={matchingResource} onPlayFullScreen={onPlayVideo} compact />
                              {showAudio && (
                                <AudioPlayer
                                  planId={plan.id}
                                  resource={matchingResource}
                                  topic={plan.topic}
                                  activityDescription={activity.description}
                                />
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
                ))}

                {/* Success Criteria */}
                {day.success_criteria && (
                  <div className="bg-navy-800/[0.03] border-l-3 border-navy-500 rounded-lg p-4">
                    <h5 className="text-[12px] font-bold text-navy-800 mb-1 flex items-center gap-1.5">
                      <TargetIcon className="w-3.5 h-3.5" />
                      Success Criteria
                    </h5>
                    <p className="text-[12px] text-navy-700/80">{day.success_criteria}</p>
                  </div>
                )}
              </div>
              </div>
            </div>
          )
        })}
        </div>
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
