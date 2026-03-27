import { useState, useEffect, useCallback, useRef, memo } from 'react'
import { submitQuiz } from '../../services/api'

/* ─── Inline SVG Icons ─── */
const ClockIcon = ({ className }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8">
    <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
)

const ChevronLeftIcon = ({ className }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
    <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 19.5L8.25 12l7.5-7.5" />
  </svg>
)

const ChevronRightIcon = ({ className }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
    <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
  </svg>
)

const CheckIcon = ({ className }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5">
    <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
  </svg>
)

const SendIcon = ({ className }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8">
    <path strokeLinecap="round" strokeLinejoin="round" d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5" />
  </svg>
)

const ExclamationIcon = ({ className }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
    <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
  </svg>
)

/* ─── Difficulty badge colors ─── */
const DIFFICULTY_COLORS = {
  beginner: 'bg-emerald-50 text-emerald-700',
  intermediate: 'bg-amber-50 text-amber-700',
  advanced: 'bg-red-50 text-red-700',
  mixed: 'bg-surface-100 text-surface-400',
}

/* ─── Option letter labels ─── */
const OPTION_LETTERS = ['A', 'B', 'C', 'D', 'E', 'F']

/* ─── Helper: format seconds as MM:SS ─── */
function formatTime(seconds) {
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}

/* ─── Fisher-Yates shuffle ─── */
function shuffleArray(arr) {
  const shuffled = [...arr]
  for (let i = shuffled.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]]
  }
  return shuffled
}

const QuizPlayer = memo(function QuizPlayer({ quiz, onComplete, onCancel }) {
  const [started, setStarted] = useState(false)
  const [currentIndex, setCurrentIndex] = useState(0)
  const [answers, setAnswers] = useState(new Map())
  const [timeRemaining, setTimeRemaining] = useState(
    quiz.time_limit_minutes ? quiz.time_limit_minutes * 60 : null
  )
  const [submitting, setSubmitting] = useState(false)
  const [showReview, setShowReview] = useState(false)
  const [submitError, setSubmitError] = useState(null)
  const startTimeRef = useRef(null)
  const submittedRef = useRef(false)

  const [shuffledQuestions] = useState(() => shuffleArray(quiz.questions || []))
  const questions = shuffledQuestions
  const totalQuestions = questions.length
  const currentQuestion = questions[currentIndex]
  const progress = totalQuestions > 0 ? ((currentIndex + 1) / totalQuestions) * 100 : 0

  /* ─── Timer countdown (uses deadline to avoid drift) ─── */
  useEffect(() => {
    if (!started || timeRemaining === null) return

    const deadlineMs = Date.now() + timeRemaining * 1000

    const tick = () => {
      const remaining = Math.max(0, Math.round((deadlineMs - Date.now()) / 1000))
      setTimeRemaining(remaining)

      if (remaining <= 0) {
        // Auto-submit on timer expiry — guard prevents double submit
        if (!submittedRef.current) {
          submittedRef.current = true
          doSubmit(true)
        }
        return
      }
      timerId = requestAnimationFrame(() => {
        timerId = setTimeout(tick, 1000 - (Date.now() % 1000))
      })
    }

    let timerId = setTimeout(tick, 1000 - (Date.now() % 1000))

    return () => {
      clearTimeout(timerId)
      cancelAnimationFrame(timerId)
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [started])

  /* ─── Answer selection ─── */
  const setAnswer = useCallback((questionId, answer) => {
    setAnswers((prev) => {
      const next = new Map(prev)
      next.set(questionId, answer)
      return next
    })
  }, [])

  /* ─── Navigation ─── */
  const goToPrevious = () => {
    if (currentIndex > 0) setCurrentIndex(currentIndex - 1)
  }

  const goToNext = () => {
    if (currentIndex < totalQuestions - 1) setCurrentIndex(currentIndex + 1)
  }

  const goToQuestion = (index) => {
    setCurrentIndex(index)
  }

  /* ─── Submit (single-fire guard prevents double submission) ─── */
  const doSubmit = async (timedOut = false) => {
    setShowReview(false)
    setSubmitError(null)
    setSubmitting(true)
    const timeTakenSeconds = Math.round((Date.now() - (startTimeRef.current || Date.now())) / 1000)
    const answersArray = questions.map((q) => ({
      question_id: q.id,
      user_answer: answers.get(q.id) || '',
    }))

    try {
      const result = await submitQuiz(quiz.id, answersArray, timeTakenSeconds, timedOut)
      onComplete(result)
    } catch (err) {
      console.error('Error submitting quiz:', err)
      submittedRef.current = false
      setSubmitting(false)
      const detail = err.response?.data?.detail || err.detail
      setSubmitError(detail || 'Failed to submit quiz. Please try again.')
    }
  }

  const handleSubmit = (timedOut = false) => {
    if (submittedRef.current || submitting) return
    submittedRef.current = true
    doSubmit(timedOut)
  }

  const handleSubmitClick = () => {
    setShowReview(true)
  }

  const isLastQuestion = currentIndex === totalQuestions - 1
  const answeredCount = questions.filter((q) => answers.has(q.id) && answers.get(q.id) !== '').length
  const unansweredCount = totalQuestions - answeredCount

  if (!currentQuestion) return null

  /* ─── Ready screen (shown before quiz starts) ─── */
  if (!started) {
    const handleStart = () => {
      startTimeRef.current = Date.now()
      setStarted(true)
    }
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] p-8 text-center">
        {/* Decorative ring + icon */}
        <div className="relative w-20 h-20 mb-6 animate-fade-up">
          <svg className="w-20 h-20 -rotate-90" viewBox="0 0 80 80">
            <circle cx="40" cy="40" r="36" fill="none" stroke="#e5e7ee" strokeWidth="2" />
            <circle cx="40" cy="40" r="36" fill="none" stroke="#7c3aed" strokeWidth="2"
              strokeDasharray="226.19" strokeDashoffset="0"
              className="animate-ring-fill" strokeLinecap="round" />
          </svg>
          <div className="absolute inset-0 flex items-center justify-center">
            <ClockIcon className="w-8 h-8 text-violet-600" />
          </div>
        </div>

        <h2 className="text-[22px] font-display font-bold text-navy-900 mb-2 animate-fade-up-1">Ready to Begin?</h2>
        <p className="text-[14px] text-surface-400 max-w-sm mb-3 animate-fade-up-2">
          {quiz.title || quiz.topic || 'Quiz'}
        </p>

        <div className="flex items-center gap-4 text-[13px] mb-6 animate-fade-up-2">
          <span className="px-3 py-1 rounded-lg bg-navy-800/[0.06] font-semibold text-navy-800">{totalQuestions} questions</span>
          {quiz.time_limit_minutes && (
            <span className="px-3 py-1 rounded-lg bg-violet-500/[0.06] font-semibold text-violet-700">{quiz.time_limit_minutes} min</span>
          )}
        </div>

        {quiz.time_limit_minutes && (
          <p className="text-[12px] text-surface-400 bg-white/80 border border-surface-200/60 rounded-lg px-4 py-2 mb-6 animate-fade-up-3">
            Timer starts when you click "Start Quiz"
          </p>
        )}

        <div className="flex items-center gap-3 animate-fade-up-4">
          <button
            onClick={onCancel}
            className="px-5 py-2.5 text-[13px] font-semibold text-surface-400 hover:text-navy-800 hover:bg-surface-100 rounded-xl transition-all"
          >
            Cancel
          </button>
          <button
            onClick={handleStart}
            className="px-6 py-2.5 bg-navy-800 hover:bg-navy-900 text-white text-[13px] font-semibold rounded-xl transition-all animate-pulse-subtle flex items-center gap-2"
          >
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
              <path d="M8 5v14l11-7z"/>
            </svg>
            Start Quiz
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col min-h-screen bg-surface-50">

      {/* ─── Header bar (sticky) ─── */}
      <div className="sticky top-0 z-30 bg-navy-800 text-white">
        <div className="flex items-center justify-between px-4 sm:px-6 py-3">
          {/* Left: quiz title */}
          <div className="flex items-center gap-3 min-w-0 flex-1">
            <button
              onClick={onCancel}
              className="p-1.5 rounded-lg hover:bg-white/10 transition-colors flex-shrink-0"
            >
              <ChevronLeftIcon className="w-4 h-4" />
            </button>
            <h1 className="text-[13px] font-semibold truncate">
              {quiz.title || quiz.topic || 'Quiz'}
            </h1>
          </div>

          {/* Center: question counter */}
          <div className="text-[12px] font-semibold text-white/80 flex-shrink-0 px-4">
            Question {currentIndex + 1} of {totalQuestions}
          </div>

          {/* Right: timer */}
          <div className="flex items-center gap-2 flex-shrink-0">
            {timeRemaining !== null && (
              <div className={`flex items-center gap-1.5 font-mono text-lg ${
                timeRemaining < 60 ? 'text-red-400' : 'text-white'
              }`}>
                <ClockIcon className="w-4 h-4" />
                <span>{formatTime(timeRemaining)}</span>
              </div>
            )}
          </div>
        </div>

        {/* Progress bar */}
        <div className="h-1 bg-navy-900">
          <div
            className="h-full bg-navy-300 transition-all duration-300 ease-out"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      {/* ─── Error banner ─── */}
      {submitError && (
        <div className="mx-4 sm:mx-6 mt-4 bg-red-50 border border-red-200/60 rounded-xl p-4 flex items-start gap-3">
          <ExclamationIcon className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="text-[13px] font-semibold text-red-800">{submitError}</p>
          </div>
          <button onClick={() => setSubmitError(null)} className="text-red-400 hover:text-red-600">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      )}

      {showReview ? (
        /* ─── Answer Review Screen ─── */
        <div className="flex-1 flex flex-col px-4 sm:px-6 py-6">
          <div className="w-full max-w-2xl mx-auto flex flex-col flex-1">
            {/* Review header */}
            <div className="flex items-center gap-3 mb-6">
              <button
                onClick={() => setShowReview(false)}
                className="p-2 rounded-xl hover:bg-surface-100 transition-colors flex-shrink-0"
              >
                <ChevronLeftIcon className="w-4 h-4 text-navy-800" />
              </button>
              <div>
                <h2 className="text-[18px] font-display font-bold text-navy-900">Review Your Answers</h2>
                <p className="text-[12px] text-surface-400 mt-0.5">
                  {answeredCount} answered, {unansweredCount} unanswered
                </p>
              </div>
            </div>

            {/* Unanswered warning */}
            {unansweredCount > 0 && (
              <div className="mb-4 bg-amber-50 border border-amber-200/60 rounded-xl p-3.5 flex items-start gap-3">
                <ExclamationIcon className="w-5 h-5 text-amber-500 flex-shrink-0 mt-0.5" />
                <p className="text-[13px] text-amber-800">
                  You have <span className="font-semibold">{unansweredCount}</span> unanswered {unansweredCount === 1 ? 'question' : 'questions'}. Unanswered questions will be marked as incorrect.
                </p>
              </div>
            )}

            {/* Question grid */}
            <div className="flex-1 overflow-y-auto mb-6">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {questions.map((q, idx) => {
                  const userAnswer = answers.get(q.id)
                  const isAnswered = userAnswer != null && userAnswer !== ''
                  const optionIndex = isAnswered && q.options ? q.options.indexOf(userAnswer) : -1
                  const answerLabel = isAnswered
                    ? (q.type === 'multiple_choice' && optionIndex >= 0 ? OPTION_LETTERS[optionIndex] : (q.type === 'true_false' ? userAnswer : 'Answered'))
                    : null

                  return (
                    <button
                      key={q.id}
                      onClick={() => { setCurrentIndex(idx); setShowReview(false) }}
                      className="flex items-start gap-3 p-3.5 rounded-xl border border-surface-200/60 bg-white hover:border-navy-300 hover:shadow-sm transition-all text-left"
                    >
                      {/* Question number badge */}
                      <span className="w-7 h-7 rounded-lg bg-navy-800 text-white text-[11px] font-bold flex items-center justify-center flex-shrink-0">
                        {idx + 1}
                      </span>

                      {/* Question text + answer status */}
                      <div className="flex-1 min-w-0">
                        <p className="text-[13px] text-navy-900 leading-snug truncate">
                          {q.question.length > 60 ? q.question.slice(0, 60) + '...' : q.question}
                        </p>
                        <div className="mt-1.5 flex items-center gap-1.5">
                          {isAnswered ? (
                            <>
                              <CheckIcon className="w-3.5 h-3.5 text-emerald-500 flex-shrink-0" />
                              <span className="text-[12px] font-semibold text-emerald-600">{answerLabel}</span>
                            </>
                          ) : (
                            <>
                              <ExclamationIcon className="w-3.5 h-3.5 text-red-400 flex-shrink-0" />
                              <span className="text-[12px] font-semibold text-red-500">Unanswered</span>
                            </>
                          )}
                        </div>
                      </div>

                      {/* Chevron */}
                      <ChevronRightIcon className="w-4 h-4 text-surface-300 flex-shrink-0 mt-1" />
                    </button>
                  )
                })}
              </div>
            </div>

            {/* Submit button */}
            <div className="sticky bottom-0 bg-surface-50 pt-4 pb-2">
              <button
                onClick={() => handleSubmit(false)}
                disabled={submitting}
                className="w-full flex items-center justify-center gap-2 bg-navy-800 hover:bg-navy-900 disabled:bg-surface-200 text-white px-5 py-3 rounded-xl text-[13px] font-semibold transition-all"
              >
                {submitting ? (
                  <>
                    <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    Submitting...
                  </>
                ) : (
                  <>
                    <SendIcon className="w-4 h-4" />
                    Submit Quiz
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      ) : (
        <>
          {/* ─── Question card ─── */}
          <div className="flex-1 flex items-start justify-center px-4 sm:px-6 py-8">
            <div className="w-full max-w-2xl">
              <div className="rounded-2xl border border-surface-200/80 bg-white p-6 sm:p-8 shadow-sm">

                {/* Badges */}
                <div className="flex flex-wrap items-center gap-2 mb-4">
                  <span className="rounded-lg bg-navy-800 text-white text-[10px] font-semibold uppercase tracking-wide px-2 py-1">
                    Q{currentIndex + 1}
                  </span>
                  {currentQuestion.difficulty && (
                    <span className={`rounded-lg text-[10px] font-semibold uppercase tracking-wide px-2 py-1 ${
                      DIFFICULTY_COLORS[currentQuestion.difficulty] || DIFFICULTY_COLORS.mixed
                    }`}>
                      {currentQuestion.difficulty}
                    </span>
                  )}
                  {currentQuestion.topic_tag && (
                    <span className="rounded-lg bg-surface-100 text-surface-400 text-[10px] font-semibold uppercase tracking-wide px-2 py-1">
                      {currentQuestion.topic_tag}
                    </span>
                  )}
                </div>

                {/* Question text */}
                <p className="text-[16px] font-semibold text-navy-900 leading-relaxed mb-6">
                  {currentQuestion.question}
                </p>

                {/* Answer area */}
                {currentQuestion.type === 'multiple_choice' && (
                  <div className="space-y-3">
                    {(currentQuestion.options || []).map((option, idx) => {
                      const isSelected = answers.get(currentQuestion.id) === option
                      return (
                        <button
                          key={idx}
                          type="button"
                          onClick={() => setAnswer(currentQuestion.id, option)}
                          className={`w-full flex items-center gap-3 px-4 py-3.5 rounded-xl border text-left transition-all ${
                            isSelected
                              ? 'bg-navy-800 border-navy-800 text-white'
                              : 'bg-white border-surface-200 hover:border-navy-300 text-navy-900'
                          }`}
                        >
                          <span className={`w-7 h-7 rounded-lg flex items-center justify-center text-[11px] font-bold flex-shrink-0 ${
                            isSelected
                              ? 'bg-white/20 text-white'
                              : 'bg-surface-100 text-surface-400'
                          }`}>
                            {OPTION_LETTERS[idx]}
                          </span>
                          <span className="text-[14px]">{option}</span>
                        </button>
                      )
                    })}
                  </div>
                )}

                {currentQuestion.type === 'true_false' && (
                  <div className="grid grid-cols-2 gap-3">
                    {['True', 'False'].map((value) => {
                      const isSelected = answers.get(currentQuestion.id) === value
                      return (
                        <button
                          key={value}
                          type="button"
                          onClick={() => setAnswer(currentQuestion.id, value)}
                          className={`flex items-center justify-center gap-2 px-4 py-4 rounded-xl border text-[14px] font-semibold transition-all ${
                            isSelected
                              ? 'bg-navy-800 border-navy-800 text-white'
                              : 'bg-white border-surface-200 hover:border-navy-300 text-navy-900'
                          }`}
                        >
                          {value === 'True' ? (
                            <svg className={`w-5 h-5 ${isSelected ? 'text-white' : 'text-emerald-500'}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                              <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                          ) : (
                            <svg className={`w-5 h-5 ${isSelected ? 'text-white' : 'text-red-500'}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                              <path strokeLinecap="round" strokeLinejoin="round" d="M9.75 9.75l4.5 4.5m0-4.5l-4.5 4.5M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                          )}
                          {value}
                        </button>
                      )
                    })}
                  </div>
                )}

                {currentQuestion.type === 'short_answer' && (
                  <textarea
                    rows={4}
                    value={answers.get(currentQuestion.id) || ''}
                    onChange={(e) => setAnswer(currentQuestion.id, e.target.value)}
                    placeholder="Type your answer here..."
                    className="w-full bg-surface-50 border border-surface-200 rounded-xl px-4 py-3 text-[14px] text-navy-900 placeholder:text-surface-300 focus:border-navy-300 focus:ring-2 focus:ring-navy-100 focus:bg-white transition-all outline-none resize-none"
                  />
                )}
              </div>
            </div>
          </div>

          {/* ─── Navigation footer ─── */}
          <div className="sticky bottom-0 bg-white border-t border-surface-200/80">
            <div className="max-w-2xl mx-auto px-4 sm:px-6 py-4 flex items-center justify-between">
              {/* Previous */}
              <button
                onClick={goToPrevious}
                disabled={currentIndex === 0}
                className={`flex items-center gap-1.5 px-4 py-2 rounded-xl text-[12px] font-semibold transition-all ${
                  currentIndex === 0
                    ? 'text-surface-300 cursor-not-allowed'
                    : 'text-navy-800 hover:bg-surface-100'
                }`}
              >
                <ChevronLeftIcon className="w-4 h-4" />
                Previous
              </button>

              {/* Dot indicators */}
              <div className="flex items-center gap-1.5 flex-wrap justify-center max-w-xs sm:max-w-md">
                {questions.map((q, idx) => {
                  const isAnswered = answers.has(q.id) && answers.get(q.id) !== ''
                  const isCurrent = idx === currentIndex
                  return (
                    <button
                      key={q.id}
                      onClick={() => goToQuestion(idx)}
                      className={`rounded-full transition-all ${
                        isCurrent
                          ? 'w-3 h-3 bg-navy-800'
                          : isAnswered
                            ? 'w-2.5 h-2.5 bg-navy-300'
                            : 'w-2.5 h-2.5 bg-surface-200'
                      }`}
                      title={`Question ${idx + 1}${isAnswered ? ' (answered)' : ''}`}
                    />
                  )
                })}
              </div>

              {/* Next / Submit */}
              {isLastQuestion ? (
                <button
                  onClick={handleSubmitClick}
                  disabled={submitting}
                  className="flex items-center gap-1.5 bg-navy-800 hover:bg-navy-900 disabled:bg-surface-200 text-white px-5 py-2 rounded-xl text-[12px] font-semibold transition-all"
                >
                  {submitting ? (
                    <>
                      <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                      Submitting...
                    </>
                  ) : (
                    <>
                      <SendIcon className="w-4 h-4" />
                      Submit Quiz
                    </>
                  )}
                </button>
              ) : (
                <button
                  onClick={goToNext}
                  className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-[12px] font-semibold text-navy-800 hover:bg-surface-100 transition-all"
                >
                  Next
                  <ChevronRightIcon className="w-4 h-4" />
                </button>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  )
})

export default QuizPlayer
