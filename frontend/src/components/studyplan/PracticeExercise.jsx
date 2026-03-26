import { useState, lazy, Suspense } from 'react'
import { generatePracticeExercises, validateExerciseStep } from '../../services/api'

const CodeEditor = lazy(() => import('./CodeEditor'))

/* ─── Icons ─── */
const BoltIcon = ({ className }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8">
    <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z" />
  </svg>
)
const CheckCircleIcon = ({ className }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
    <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
)
const ClockIcon = ({ className }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8">
    <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
)

const EXERCISE_TYPE_LABELS = {
  code_challenge: 'Code Challenge',
  worked_example: 'Worked Example',
  diagram_drawing: 'Draw It Out',
  explain_aloud: 'Explain Aloud',
  build_project: 'Build Project',
  debug_exercise: 'Debug Exercise',
  compare_contrast: 'Compare & Contrast',
}

const EXERCISE_TYPE_COLORS = {
  code_challenge: 'bg-violet-50 text-violet-700 border-violet-200',
  worked_example: 'bg-amber-50 text-amber-700 border-amber-200',
  diagram_drawing: 'bg-teal-50 text-teal-700 border-teal-200',
  explain_aloud: 'bg-sky-50 text-sky-700 border-sky-200',
  build_project: 'bg-rose-50 text-rose-700 border-rose-200',
  debug_exercise: 'bg-orange-50 text-orange-700 border-orange-200',
  compare_contrast: 'bg-indigo-50 text-indigo-700 border-indigo-200',
}

const DIFFICULTY_COLORS = {
  easy: 'bg-emerald-50 text-emerald-600',
  medium: 'bg-amber-50 text-amber-600',
  hard: 'bg-red-50 text-red-600',
}

export default function PracticeExercise({ planId, resource, topic, activityDescription = '', pageRange = null }) {
  const [exercises, setExercises] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [isFallback, setIsFallback] = useState(false)
  const [completedSteps, setCompletedSteps] = useState({})
  const [expanded, setExpanded] = useState({})
  const [guidedMode, setGuidedMode] = useState(true)
  const [stepAnswers, setStepAnswers] = useState({})
  const [stepResults, setStepResults] = useState({})
  const [validating, setValidating] = useState(null)

  const handleGenerate = async () => {
    if (!resource?.id) return
    setLoading(true)
    setError(null)
    try {
      const result = await generatePracticeExercises(planId, resource.id, activityDescription, pageRange)
      setExercises(result.exercises || [])
      setIsFallback(result.is_fallback || false)
      // Reset progress state for fresh exercises
      setCompletedSteps({})
      setStepAnswers({})
      setStepResults({})
      // Auto-expand first exercise
      if (result.exercises?.length > 0) {
        setExpanded({ 0: true })
      }
    } catch (err) {
      console.error('Failed to generate exercises:', err)
      setError('Failed to generate exercises. Try again.')
    } finally {
      setLoading(false)
    }
  }

  const toggleStep = (exerciseIdx, stepIdx) => {
    const key = `${exerciseIdx}-${stepIdx}`
    setCompletedSteps(prev => ({
      ...prev,
      [key]: !prev[key]
    }))
  }

  const toggleExpand = (idx) => {
    setExpanded(prev => ({ ...prev, [idx]: !prev[idx] }))
  }

  const getExerciseProgress = (exerciseIdx, totalSteps) => {
    let completed = 0
    for (let i = 0; i < totalSteps; i++) {
      if (completedSteps[`${exerciseIdx}-${i}`]) completed++
    }
    return completed
  }

  const handleValidateStep = async (exerciseIdx, stepIdx, step, exerciseTitle) => {
    const key = `${exerciseIdx}-${stepIdx}`
    const answer = stepAnswers[key]
    if (!answer?.trim()) return

    setValidating(key)
    try {
      const result = await validateExerciseStep(planId, resource.id, {
        exercise_title: exerciseTitle,
        step_text: step,
        student_answer: answer,
        topic: topic,
      })

      setStepResults(prev => ({ ...prev, [key]: result }))

      // Auto-mark as completed if correct
      if (result.correct) {
        setCompletedSteps(prev => ({ ...prev, [key]: true }))
      }
    } catch (err) {
      console.error('Step validation failed:', err)
      setStepResults(prev => ({
        ...prev,
        [key]: { correct: null, feedback: 'Validation unavailable — mark this step yourself.', hint: null }
      }))
    } finally {
      setValidating(null)
    }
  }

  // Not yet generated — show the generate button with sandbox indicator
  if (!exercises) {
    return (
      <div className="bg-violet-50/40 border border-violet-200/60 rounded-xl p-3">
        <button
          onClick={handleGenerate}
          disabled={loading}
          className="flex items-center gap-2 w-full justify-center px-3 py-2.5 bg-violet-600 hover:bg-violet-700 disabled:bg-violet-300 text-white rounded-lg text-[12px] font-semibold transition-all"
        >
          {loading ? (
            <>
              <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              Generating exercises...
            </>
          ) : (
            <>
              <BoltIcon className="w-3.5 h-3.5" />
              Generate Practice Exercises
            </>
          )}
        </button>

        {/* Sandbox feature hints */}
        {!loading && !error && (
          <div className="flex items-center justify-center gap-3 mt-2.5 flex-wrap">
            <span className="inline-flex items-center gap-1.5 text-[10px] font-semibold text-violet-600/80">
              <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8">
                <path strokeLinecap="round" strokeLinejoin="round" d="M17.25 6.75L22.5 12l-5.25 5.25m-10.5 0L1.5 12l5.25-5.25m7.5-3l-4.5 16.5" />
              </svg>
              Code Sandbox
            </span>
            <span className="w-px h-3 bg-violet-200/60" />
            <span className="inline-flex items-center gap-1.5 text-[10px] font-semibold text-violet-600/80">
              <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8">
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              AI Code Review
            </span>
            <span className="w-px h-3 bg-violet-200/60" />
            <span className="inline-flex items-center gap-1.5 text-[10px] font-semibold text-violet-600/80">
              <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8">
                <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6A2.25 2.25 0 016 3.75h2.25A2.25 2.25 0 0110.5 6v2.25a2.25 2.25 0 01-2.25 2.25H6a2.25 2.25 0 01-2.25-2.25V6zM3.75 15.75A2.25 2.25 0 016 13.5h2.25a2.25 2.25 0 012.25 2.25V18a2.25 2.25 0 01-2.25 2.25H6A2.25 2.25 0 013.75 18v-2.25zM13.5 6a2.25 2.25 0 012.25-2.25H18A2.25 2.25 0 0120.25 6v2.25A2.25 2.25 0 0118 10.5h-2.25a2.25 2.25 0 01-2.25-2.25V6zM13.5 15.75a2.25 2.25 0 012.25-2.25H18a2.25 2.25 0 012.25 2.25V18A2.25 2.25 0 0118 20.25h-2.25A2.25 2.25 0 0113.5 18v-2.25z" />
              </svg>
              Guided Steps
            </span>
          </div>
        )}

        {error && (
          <p className="text-[11px] text-red-500 mt-2 text-center">{error}</p>
        )}
      </div>
    )
  }

  // Exercises generated — show them
  const totalAllSteps = exercises.reduce((sum, ex) => sum + (ex.steps?.length || 0), 0)
  const totalCompleted = Object.values(completedSteps).filter(Boolean).length
  const allDone = totalAllSteps > 0 && totalCompleted === totalAllSteps

  return (
    <div className="bg-violet-50/30 border border-violet-200/60 rounded-lg overflow-hidden">
      {/* Header */}
      <div className="px-3 py-2.5 bg-violet-50/60 border-b border-violet-200/40 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <BoltIcon className="w-4 h-4 text-violet-600" />
          <span className="text-[12px] font-bold text-violet-800">
            Practice Exercises
          </span>
          <span className="text-[10px] font-semibold text-violet-500">
            {exercises.length} exercises
          </span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setGuidedMode(prev => !prev)}
            className="flex items-center gap-1 px-2 py-1 rounded-md text-[10px] font-semibold transition-all border"
            style={{
              background: guidedMode ? 'rgb(139 92 246 / 0.1)' : 'transparent',
              borderColor: guidedMode ? 'rgb(139 92 246 / 0.3)' : 'rgb(203 213 225 / 0.6)',
              color: guidedMode ? 'rgb(109 40 217)' : 'rgb(100 116 139)',
            }}
          >
            {guidedMode ? '✏️ Guided' : '☑️ Checklist'}
          </button>
          {allDone && (
            <span className="flex items-center gap-1 text-[10px] font-semibold text-emerald-600">
              <CheckCircleIcon className="w-3.5 h-3.5" />
              All complete!
            </span>
          )}
          <span className="text-[10px] font-mono text-violet-500">
            {totalCompleted}/{totalAllSteps} steps
          </span>
        </div>
      </div>

      {/* Fallback warning */}
      {isFallback && (
        <div className="mx-3 mt-2.5 px-3.5 py-2.5 bg-gradient-to-r from-amber-50/70 to-orange-50/40 border border-amber-200/50 rounded-xl flex items-center gap-2.5 animate-fade-up-0">
          <div className="w-6 h-6 rounded-lg bg-amber-100 border border-amber-200/60 flex items-center justify-center flex-shrink-0">
            <svg className="w-3.5 h-3.5 text-amber-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8">
              <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z" />
            </svg>
          </div>
          <div>
            <span className="text-[11px] text-amber-800 font-semibold">General exercises</span>
            <span className="text-[11px] text-amber-600 ml-1">— upload slides for targeted, content-specific practice</span>
          </div>
        </div>
      )}

      {/* Exercise list */}
      <div className="divide-y divide-violet-100/60">
        {exercises.map((exercise, idx) => {
          const isExpanded = expanded[idx]
          const stepsCount = exercise.steps?.length || 0
          const completed = getExerciseProgress(idx, stepsCount)
          const isComplete = stepsCount > 0 && completed === stepsCount
          const typeColor = EXERCISE_TYPE_COLORS[exercise.exercise_type] || 'bg-slate-50 text-slate-600 border-slate-200'
          const diffColor = DIFFICULTY_COLORS[exercise.difficulty] || DIFFICULTY_COLORS.medium

          return (
            <div key={idx} className={`transition-colors ${isComplete ? 'bg-emerald-50/20' : ''}`}>
              {/* Exercise header (always visible) */}
              <button
                onClick={() => toggleExpand(idx)}
                className="w-full px-3 py-2.5 flex items-start gap-2.5 text-left hover:bg-violet-50/40 transition-colors"
              >
                <div className={`w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5 ${
                  isComplete ? 'bg-emerald-500 text-white' : 'bg-violet-100 text-violet-600'
                }`}>
                  {isComplete ? (
                    <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="3">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                    </svg>
                  ) : (
                    <span className="text-[10px] font-bold">{idx + 1}</span>
                  )}
                </div>

                <div className="flex-1 min-w-0">
                  <p className={`text-[12px] font-semibold ${isComplete ? 'text-emerald-800' : 'text-navy-900'}`}>
                    {exercise.title}
                  </p>
                  <div className="flex items-center gap-1.5 mt-1 flex-wrap">
                    <span className={`text-[9px] font-semibold px-1.5 py-0.5 rounded border ${typeColor}`}>
                      {EXERCISE_TYPE_LABELS[exercise.exercise_type] || exercise.exercise_type}
                    </span>
                    <span className={`text-[9px] font-semibold px-1.5 py-0.5 rounded ${diffColor}`}>
                      {exercise.difficulty}
                    </span>
                    <span className="flex items-center gap-0.5 text-[9px] text-surface-400">
                      <ClockIcon className="w-3 h-3" />
                      {exercise.estimated_minutes}m
                    </span>
                    {stepsCount > 0 && (
                      <span className="text-[9px] text-surface-400 font-mono">
                        {completed}/{stepsCount}
                      </span>
                    )}
                  </div>
                </div>

                <svg className={`w-4 h-4 text-surface-300 flex-shrink-0 mt-1 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
                  fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
                </svg>
              </button>

              {/* Expanded exercise details */}
              {isExpanded && (
                <div className="px-3 pb-3 pt-0">
                  {exercise.instructions && (
                    <p className="text-[11px] text-surface-500 mb-2.5 ml-7.5 leading-relaxed">
                      {exercise.instructions}
                    </p>
                  )}

                  {/* Code Editor for code_challenge / debug_exercise */}
                  {(exercise.exercise_type === 'code_challenge' || exercise.exercise_type === 'debug_exercise') && (
                    <div className="ml-7.5 mb-3">
                      <Suspense fallback={
                        <div className="flex items-center gap-2 p-4 bg-slate-900/80 rounded-lg">
                          <div className="w-3.5 h-3.5 border-2 border-violet-300/30 border-t-violet-400 rounded-full animate-spin" />
                          <span className="text-[11px] text-slate-400">Loading code editor...</span>
                        </div>
                      }>
                        <CodeEditor
                          topic={topic}
                          exerciseTitle={exercise.title}
                          language={exercise.language}
                          initialCode={exercise.starter_code}
                          onCheckCode={async (code) => {
                            const result = await validateExerciseStep(planId, resource.id, {
                              exercise_title: exercise.title,
                              step_text: exercise.instructions || exercise.title,
                              student_answer: code,
                              topic: topic,
                            })
                            return result
                          }}
                        />
                      </Suspense>
                    </div>
                  )}

                  {/* Steps */}
                  {exercise.steps && exercise.steps.length > 0 && (
                    <div className="ml-7.5 space-y-1.5">
                      {exercise.steps.map((step, stepIdx) => {
                        const stepKey = `${idx}-${stepIdx}`
                        const isDone = completedSteps[stepKey]
                        const result = stepResults[stepKey]
                        const isValidating = validating === stepKey

                        if (!guidedMode) {
                          // Checklist mode — existing checkbox behavior
                          return (
                            <button
                              key={stepIdx}
                              onClick={(e) => { e.stopPropagation(); toggleStep(idx, stepIdx) }}
                              className={`w-full text-left flex items-start gap-2 px-2.5 py-1.5 rounded-lg transition-all ${
                                isDone ? 'bg-emerald-50/50' : 'hover:bg-surface-50'
                              }`}
                            >
                              <div className={`w-4 h-4 rounded border-2 flex items-center justify-center flex-shrink-0 mt-0.5 transition-all ${
                                isDone ? 'bg-emerald-500 border-emerald-500' : 'border-surface-300 bg-white'
                              }`}>
                                {isDone && (
                                  <svg className="w-2.5 h-2.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="3">
                                    <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                                  </svg>
                                )}
                              </div>
                              <span className={`text-[11px] leading-relaxed ${
                                isDone ? 'text-emerald-700 line-through' : 'text-navy-800'
                              }`}>
                                {step}
                              </span>
                            </button>
                          )
                        }

                        // Guided mode — input + validation
                        return (
                          <div key={stepIdx} className={`rounded-lg border transition-all ${
                            isDone ? 'bg-emerald-50/30 border-emerald-200/60' :
                            result?.correct === false ? 'bg-amber-50/30 border-amber-200/60' :
                            'bg-white border-surface-200/60'
                          }`}>
                            <div className="px-2.5 py-2">
                              <div className="flex items-start gap-2">
                                <div className={`w-4 h-4 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5 text-[9px] font-bold ${
                                  isDone ? 'bg-emerald-500 text-white' : 'bg-violet-100 text-violet-600'
                                }`}>
                                  {isDone ? '✓' : stepIdx + 1}
                                </div>
                                <p className={`text-[11px] leading-relaxed flex-1 ${isDone ? 'text-emerald-700' : 'text-navy-800'}`}>
                                  {step}
                                </p>
                              </div>

                              {!isDone && (
                                <div className="mt-2 ml-6">
                                  <textarea
                                    value={stepAnswers[stepKey] || ''}
                                    onChange={(e) => setStepAnswers(prev => ({ ...prev, [stepKey]: e.target.value }))}
                                    placeholder="Type your answer..."
                                    rows={2}
                                    className="w-full text-[11px] px-2.5 py-1.5 rounded-md border border-surface-200 bg-white focus:border-violet-400 focus:ring-1 focus:ring-violet-200 outline-none resize-none transition-all"
                                  />
                                  <div className="flex items-center gap-2 mt-1.5">
                                    <button
                                      onClick={() => handleValidateStep(idx, stepIdx, step, exercise.title)}
                                      disabled={isValidating || !stepAnswers[stepKey]?.trim()}
                                      className="px-2.5 py-1 bg-violet-600 hover:bg-violet-700 disabled:bg-violet-300 text-white rounded-md text-[10px] font-semibold transition-all flex items-center gap-1"
                                    >
                                      {isValidating ? (
                                        <>
                                          <div className="w-2.5 h-2.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                                          Checking...
                                        </>
                                      ) : 'Check'}
                                    </button>
                                    <button
                                      onClick={() => {
                                        setCompletedSteps(prev => ({ ...prev, [stepKey]: true }))
                                      }}
                                      className="px-2.5 py-1 text-surface-400 hover:text-surface-600 text-[10px] font-medium transition-all"
                                    >
                                      Skip
                                    </button>
                                  </div>
                                </div>
                              )}

                              {/* Feedback */}
                              {result && !isDone && (
                                <div className={`mt-2 ml-6 px-2.5 py-2 rounded-md text-[11px] ${
                                  result.correct ? 'bg-emerald-50 text-emerald-700 border border-emerald-200/60' :
                                  result.correct === false ? 'bg-amber-50 text-amber-700 border border-amber-200/60' :
                                  'bg-slate-50 text-slate-600 border border-slate-200/60'
                                }`}>
                                  <p>{result.feedback}</p>
                                  {result.hint && (
                                    <p className="mt-1 text-[10px] opacity-80">💡 {result.hint}</p>
                                  )}
                                </div>
                              )}

                              {isDone && result && (
                                <div className="mt-1 ml-6">
                                  <p className="text-[10px] text-emerald-600">{result.feedback}</p>
                                </div>
                              )}
                            </div>
                          </div>
                        )
                      })}
                    </div>
                  )}

                  {/* Success criteria */}
                  {exercise.success_criteria && (
                    <div className="ml-7.5 mt-2.5 bg-emerald-50/50 border border-emerald-200/60 rounded-lg px-2.5 py-2">
                      <p className="text-[10px] font-semibold text-emerald-700 mb-0.5">Success Criteria</p>
                      <p className="text-[11px] text-emerald-600 leading-relaxed">{exercise.success_criteria}</p>
                    </div>
                  )}
                </div>
              )}
            </div>
          )
        })}
      </div>

      {/* Quiz prompt */}
      {allDone && (
        <div className="px-3 py-3 bg-emerald-50/40 border-t border-emerald-200/40">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <CheckCircleIcon className="w-4 h-4 text-emerald-500" />
              <span className="text-[12px] font-semibold text-emerald-700">
                All exercises complete! Ready to test yourself?
              </span>
            </div>
            <a
              href={`/smartstudy?quiz=${encodeURIComponent(topic)}`}
              className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-[11px] font-semibold transition-all"
            >
              Take Quiz
            </a>
          </div>
        </div>
      )}
    </div>
  )
}
