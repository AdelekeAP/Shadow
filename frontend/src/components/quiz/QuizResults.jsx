import { useState, useEffect } from 'react'

/* ─── Inline SVG Icons ─── */
const CheckCircleIcon = ({ className }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
    <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
)

const XCircleIcon = ({ className }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
    <path strokeLinecap="round" strokeLinejoin="round" d="M9.75 9.75l4.5 4.5m0-4.5l-4.5 4.5M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
)

const ChevronDownIcon = ({ className }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
    <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
  </svg>
)

const RefreshIcon = ({ className }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8">
    <path strokeLinecap="round" strokeLinejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182" />
  </svg>
)

const BookOpenIcon = ({ className }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8">
    <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 016-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0018 18a8.967 8.967 0 00-6 2.292m0-14.25v14.25" />
  </svg>
)

const ClockIcon = ({ className }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8">
    <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
)

const ExclamationTriangleIcon = ({ className }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8">
    <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
  </svg>
)

const BulletIcon = ({ className }) => (
  <svg className={className} fill="currentColor" viewBox="0 0 8 8">
    <circle cx="4" cy="4" r="3" />
  </svg>
)

/* ─── Helper: format seconds as M:SS ─── */
function formatTimeTaken(seconds) {
  if (!seconds && seconds !== 0) return null
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${m}:${String(s).padStart(2, '0')}`
}

/* ─── Score ring color ─── */
function getScoreColor(pct) {
  if (pct >= 80) return { ring: '#059669', bg: 'emerald' }   // emerald-500
  if (pct >= 60) return { ring: '#d97706', bg: 'amber' }     // amber-500
  return { ring: '#ef4444', bg: 'red' }                       // red-500
}

/* ─── Score Ring SVG ─── */
function ScoreRing({ percentage, size = 120 }) {
  const strokeWidth = 8
  const viewBox = 120
  const radius = 50
  const circumference = 2 * Math.PI * radius
  const offset = circumference - (percentage * circumference / 100)
  const color = getScoreColor(percentage)

  return (
    <div className="relative inline-flex items-center justify-center" style={{ width: size, height: size }}>
      <svg
        viewBox={`0 0 ${viewBox} ${viewBox}`}
        className="transform -rotate-90"
        style={{ width: size, height: size }}
      >
        {/* Background circle */}
        <circle
          cx={viewBox / 2}
          cy={viewBox / 2}
          r={radius}
          fill="none"
          stroke="#e5e7ee"
          strokeWidth={strokeWidth}
        />
        {/* Score circle */}
        <circle
          cx={viewBox / 2}
          cy={viewBox / 2}
          r={radius}
          fill="none"
          stroke={color.ring}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          style={{ transition: 'stroke-dashoffset 1.2s ease-out' }}
        />
      </svg>
      {/* Center text */}
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="font-display text-3xl font-bold" style={{ color: color.ring }}>
          {Math.round(percentage)}%
        </span>
      </div>
    </div>
  )
}

export default function QuizResults({ attempt, quiz, onRetake, onCreateStudyPlan, onClose }) {
  const [expandedQuestion, setExpandedQuestion] = useState(null)
  const [showAllExplanations, setShowAllExplanations] = useState(false)

  // Auto-expand first incorrect answer
  const [autoExpanded, setAutoExpanded] = useState(false)
  useEffect(() => {
    if (!autoExpanded && answersData.length > 0) {
      const firstIncorrect = answersData.find(a => !a.is_correct)
      if (firstIncorrect) setExpandedQuestion(firstIncorrect.question_id)
      setAutoExpanded(true)
    }
  }, [answersData, autoExpanded])

  if (!attempt) return null

  const scorePercentage = attempt.total_questions > 0
    ? (attempt.correct_count / attempt.total_questions) * 100
    : 0
  const scoreColor = getScoreColor(scorePercentage)
  const knowledgeGaps = attempt.knowledge_gaps || {}
  const weakTopics = knowledgeGaps.weak_topics || []
  const strongTopics = knowledgeGaps.strong_topics || []
  const answersData = attempt.answers || []

  const toggleQuestion = (questionId) => {
    setExpandedQuestion((prev) => (prev === questionId ? null : questionId))
  }

  // Find the weakest topic for the study plan CTA
  const weakestTopic = weakTopics.length > 0 ? weakTopics[0] : null
  const weakestTopicName = typeof weakestTopic === 'string'
    ? weakestTopic
    : weakestTopic?.topic || weakestTopic?.name || null

  return (
    <div className="max-w-2xl mx-auto px-4 sm:px-6 py-8 space-y-8">

      {/* ─── Score hero section ─── */}
      <div className="rounded-2xl border border-surface-200/80 bg-white p-8 text-center">
        <div className="flex justify-center mb-4">
          <ScoreRing percentage={scorePercentage} size={120} />
        </div>

        <p className="text-[14px] text-surface-400">
          {attempt.correct_count} of {attempt.total_questions} correct
        </p>

        {/* Time taken */}
        {attempt.was_timed && attempt.time_taken_seconds != null && (
          <div className="flex items-center justify-center gap-1.5 mt-2">
            <ClockIcon className="w-4 h-4 text-surface-300" />
            <span className="text-[13px] font-mono text-surface-400">
              Completed in {formatTimeTaken(attempt.time_taken_seconds)}
            </span>
          </div>
        )}

        {/* Timed out badge */}
        {attempt.timed_out && (
          <div className="inline-flex items-center gap-1.5 mt-3 px-3 py-1.5 bg-amber-50 border border-amber-200/60 rounded-lg">
            <ExclamationTriangleIcon className="w-3.5 h-3.5 text-amber-500" />
            <span className="text-[11px] font-semibold uppercase tracking-wide text-amber-700">Time expired</span>
          </div>
        )}
      </div>

      {/* ─── Knowledge Gap Analysis ─── */}
      {(weakTopics.length > 0 || strongTopics.length > 0 || knowledgeGaps.overall_assessment || knowledgeGaps.study_recommendations) && (
        <div className="rounded-2xl border border-surface-200/80 bg-white p-6">
          <h2 className="text-[15px] font-display font-bold text-navy-900 mb-5">Knowledge Analysis</h2>

          {/* Strong topics */}
          {strongTopics.length > 0 && (
            <div className="mb-4">
              <h3 className="text-[11px] font-semibold text-navy-800 uppercase tracking-wider mb-2">Strong Topics</h3>
              <div className="flex flex-wrap gap-2">
                {strongTopics.map((topic, idx) => {
                  const topicName = typeof topic === 'string' ? topic : (topic.topic || topic.name || '')
                  const topicScore = typeof topic === 'object' ? topic.score : null
                  return (
                    <div
                      key={idx}
                      className="flex items-center gap-2 bg-emerald-50 border border-emerald-200/60 rounded-lg px-3 py-1.5"
                    >
                      <span className="text-[12px] font-semibold text-emerald-700">{topicName}</span>
                      {topicScore != null && (
                        <span className="text-[10px] font-mono font-bold text-emerald-600">{Math.round(topicScore)}%</span>
                      )}
                    </div>
                  )
                })}
              </div>
            </div>
          )}

          {/* Weak topics */}
          {weakTopics.length > 0 && (
            <div className="mb-4">
              <h3 className="text-[11px] font-semibold text-navy-800 uppercase tracking-wider mb-2">Weak Topics</h3>
              <div className="flex flex-wrap gap-2">
                {weakTopics.map((topic, idx) => {
                  const topicName = typeof topic === 'string' ? topic : (topic.topic || topic.name || '')
                  const topicScore = typeof topic === 'object' ? topic.score : null
                  return (
                    <div
                      key={idx}
                      className="flex items-center gap-2 bg-red-50 border border-red-200/60 rounded-lg px-3 py-1.5"
                    >
                      <span className="text-[12px] font-semibold text-red-700">{topicName}</span>
                      {topicScore != null && (
                        <span className="text-[10px] font-mono font-bold text-red-600">{Math.round(topicScore)}%</span>
                      )}
                    </div>
                  )
                })}
              </div>
            </div>
          )}

          {/* Overall assessment */}
          {knowledgeGaps.overall_assessment && (
            <div className="mb-4">
              <h3 className="text-[11px] font-semibold text-navy-800 uppercase tracking-wider mb-2">Overall Assessment</h3>
              <p className="text-[13px] text-navy-900 leading-relaxed">{knowledgeGaps.overall_assessment}</p>
            </div>
          )}

          {/* Recommendations */}
          {knowledgeGaps.study_recommendations && knowledgeGaps.study_recommendations.length > 0 && (
            <div>
              <h3 className="text-[11px] font-semibold text-navy-800 uppercase tracking-wider mb-2">Recommendations</h3>
              <ul className="space-y-1.5">
                {knowledgeGaps.study_recommendations.map((rec, idx) => (
                  <li key={idx} className="flex items-start gap-2">
                    <BulletIcon className="w-1.5 h-1.5 text-navy-300 mt-1.5 flex-shrink-0" />
                    <span className="text-[13px] text-navy-900 leading-relaxed">{rec}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* ─── Question Review ─── */}
      {answersData.length > 0 && (
        <div className="rounded-2xl border border-surface-200/80 bg-white p-6">
          <div className="flex items-center justify-between mb-5">
            <h2 className="text-[15px] font-display font-bold text-navy-900">Question Review</h2>
            <button
              onClick={() => setShowAllExplanations(prev => !prev)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[12px] font-semibold text-navy-600 hover:text-navy-800 hover:bg-surface-100 transition-colors"
            >
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                <path strokeLinecap="round" strokeLinejoin="round" d={showAllExplanations ? "M19.5 8.25l-7.5 7.5-7.5-7.5" : "M8.25 4.5l7.5 7.5-7.5 7.5"} />
              </svg>
              {showAllExplanations ? 'Collapse All' : 'Show All'}
            </button>
          </div>

          <div className="space-y-2">
            {answersData.map((answer, idx) => {
              const isCorrect = answer.is_correct
              const isExpanded = showAllExplanations || expandedQuestion === answer.question_id
              const matchingQuestion = quiz?.questions?.find((q) => q.id === answer.question_id)
              const questionText = matchingQuestion?.question || `Question ${idx + 1}`

              return (
                <div
                  key={answer.question_id}
                  className={`rounded-xl border transition-all overflow-hidden ${
                    isCorrect
                      ? 'border-l-4 border-l-emerald-500 border-surface-200/80'
                      : 'border-l-4 border-l-red-500 border-surface-200/80'
                  }`}
                >
                  {/* Collapsed row */}
                  <button
                    onClick={() => toggleQuestion(answer.question_id)}
                    className="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-surface-50/50 transition-colors"
                  >
                    {/* Status icon */}
                    {isCorrect ? (
                      <CheckCircleIcon className="w-5 h-5 text-emerald-500 flex-shrink-0" />
                    ) : (
                      <XCircleIcon className="w-5 h-5 text-red-500 flex-shrink-0" />
                    )}

                    {/* Question number + truncated text */}
                    <div className="flex-1 min-w-0">
                      <span className="text-[13px] text-navy-900">
                        <span className="font-semibold mr-1.5">Q{idx + 1}.</span>
                        {questionText.length > 80 ? questionText.slice(0, 80) + '...' : questionText}
                      </span>
                    </div>

                    {/* Topic tag */}
                    {answer.topic_tag && (
                      <span className="rounded-lg bg-surface-100 text-surface-400 text-[10px] font-semibold uppercase tracking-wide px-2 py-0.5 flex-shrink-0 hidden sm:block">
                        {answer.topic_tag}
                      </span>
                    )}

                    {/* Expand chevron */}
                    <ChevronDownIcon className={`w-4 h-4 text-surface-300 flex-shrink-0 transition-transform ${
                      isExpanded ? 'rotate-180' : ''
                    }`} />
                  </button>

                  {/* Expanded content */}
                  {isExpanded && (
                    <div className="px-4 pb-4 pt-1 border-t border-surface-200/60 space-y-3">
                      {/* Full question */}
                      <p className="text-[14px] font-semibold text-navy-900 leading-relaxed">{questionText}</p>

                      {/* Your answer */}
                      <div className="flex items-start gap-2">
                        <span className="text-[11px] font-semibold text-navy-800 uppercase tracking-wider mt-0.5 flex-shrink-0 w-24">
                          Your answer
                        </span>
                        <span className={`text-[13px] ${isCorrect ? 'text-emerald-700' : 'text-red-700'}`}>
                          {answer.user_answer || '(no answer)'}
                        </span>
                      </div>

                      {/* Correct answer (shown for all questions) */}
                      {answer.correct_answer && (
                        <div className="flex items-start gap-2">
                          <span className="text-[11px] font-semibold text-navy-800 uppercase tracking-wider mt-0.5 flex-shrink-0 w-24">
                            Correct
                          </span>
                          <span className="text-[13px] text-emerald-700 font-semibold">{answer.correct_answer}</span>
                        </div>
                      )}

                      {/* Explanation */}
                      {answer.explanation && (
                        <div className={`rounded-lg p-3 mt-2 ${
                          isCorrect
                            ? 'bg-surface-50'
                            : 'bg-amber-50/60 border border-amber-200/60'
                        }`}>
                          <p className={`text-[11px] font-semibold uppercase tracking-wider mb-1 ${
                            isCorrect ? 'text-navy-800' : 'text-amber-800'
                          }`}>Explanation</p>
                          <p className="text-[13px] text-navy-900 leading-relaxed">{answer.explanation}</p>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* ─── Action buttons ─── */}
      <div className="flex flex-col items-center gap-3 pb-4">
        {/* Max-attempts warning */}
        {quiz?.remaining_attempts != null && quiz.remaining_attempts <= 1 && quiz.remaining_attempts > 0 && (
          <p className="text-[12px] text-amber-600 font-semibold">Last attempt remaining</p>
        )}
        {quiz?.remaining_attempts === 0 && (
          <p className="text-[12px] text-red-600 font-semibold">No attempts remaining — generate a new quiz to keep practicing</p>
        )}
        <div className="flex items-center justify-center gap-3">
        {onRetake && (quiz?.remaining_attempts == null || quiz.remaining_attempts > 0) && (
          <button
            onClick={onRetake}
            className="flex items-center gap-2 px-5 py-2.5 rounded-xl border border-navy-800 text-navy-800 text-[12px] font-semibold hover:bg-navy-800/[0.04] transition-all"
          >
            <RefreshIcon className="w-4 h-4" />
            Retake Quiz
          </button>
        )}

        {onCreateStudyPlan && weakestTopicName && (
          <button
            onClick={() => onCreateStudyPlan(weakestTopicName)}
            className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-navy-800 hover:bg-navy-900 text-white text-[12px] font-semibold transition-all"
          >
            <BookOpenIcon className="w-4 h-4" />
            Study Weak Topics
          </button>
        )}

        {onClose && (
          <button
            onClick={onClose}
            className="px-5 py-2.5 rounded-xl text-[12px] font-semibold text-surface-400 hover:text-navy-800 hover:bg-surface-100 transition-all"
          >
            Done
          </button>
        )}
        </div>
      </div>
    </div>
  )
}
