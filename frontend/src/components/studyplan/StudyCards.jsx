import { useState, useMemo } from 'react'
import { generateStudyCards } from '../../services/api'

/* ─── Icons ─── */
const BookIcon = ({ className }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8">
    <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 016-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0018 18a8.967 8.967 0 00-6 2.292m0-14.25v14.25" />
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
const ChevronDownIcon = ({ className }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
    <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
  </svg>
)
const CheckCircleIcon = ({ className }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
    <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
)
const LightBulbIcon = ({ className }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8">
    <path strokeLinecap="round" strokeLinejoin="round" d="M12 18v-5.25m0 0a6.01 6.01 0 001.5-.189m-1.5.189a6.01 6.01 0 01-1.5-.189m3.75 7.478a12.06 12.06 0 01-4.5 0m3.75 2.383a14.406 14.406 0 01-3 0M14.25 18v-.192c0-.983.658-1.823 1.508-2.316a7.5 7.5 0 10-7.517 0c.85.493 1.509 1.333 1.509 2.316V18" />
  </svg>
)
const QuestionIcon = ({ className }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8">
    <path strokeLinecap="round" strokeLinejoin="round" d="M9.879 7.519c1.171-1.025 3.071-1.025 4.242 0 1.172 1.025 1.172 2.687 0 3.712-.203.179-.43.326-.67.442-.745.361-1.45.999-1.45 1.827v.75M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9 5.25h.008v.008H12v-.008z" />
  </svg>
)

const CATEGORY_COLORS = {
  definition: { bg: 'bg-emerald-100', text: 'text-emerald-700', border: 'border-emerald-300' },
  concept:    { bg: 'bg-blue-100',    text: 'text-blue-700',    border: 'border-blue-300' },
  formula:    { bg: 'bg-amber-100',   text: 'text-amber-700',   border: 'border-amber-300' },
  example:    { bg: 'bg-violet-100',  text: 'text-violet-700',  border: 'border-violet-300' },
}

const IMPORTANCE_STYLES = {
  critical:      { bar: 'bg-emerald-600', title: 'font-bold text-navy-900', wrapper: 'bg-emerald-50/50 border-emerald-200/60' },
  important:     { bar: 'bg-emerald-400', title: 'font-semibold text-navy-800', wrapper: 'bg-white border-surface-200/60' },
  supplementary: { bar: 'bg-surface-300', title: 'font-medium text-surface-500', wrapper: 'bg-surface-50/40 border-surface-200/40' },
}

const TABS = [
  { label: 'Flashcards',   icon: BookIcon },
  { label: 'Key Concepts', icon: LightBulbIcon },
  { label: 'Comprehension', icon: QuestionIcon },
]

export default function StudyCards({ planId, resource, topic, activityDescription = '', pageRange = null }) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [isFallback, setIsFallback] = useState(false)
  const [activeTab, setActiveTab] = useState(0)

  // Flashcard state
  const [currentCard, setCurrentCard] = useState(0)
  const [flipped, setFlipped] = useState(false)
  const [knownCards, setKnownCards] = useState(new Set())
  const [reviewQueue, setReviewQueue] = useState([])

  // Key concepts state
  const [expandedConcepts, setExpandedConcepts] = useState(new Set())

  // Comprehension state
  const [currentQuestion, setCurrentQuestion] = useState(0)
  const [answers, setAnswers] = useState({})
  const [revealed, setRevealed] = useState(new Set())
  const [ratings, setRatings] = useState({})

  const handleGenerate = async () => {
    if (!resource?.id) return
    setLoading(true)
    setError(null)
    try {
      const result = await generateStudyCards(planId, resource.id, activityDescription, pageRange)
      setData(result)
      setIsFallback(result.is_fallback || false)
      // Build initial card order from flashcards indices
      if (result.flashcards?.length > 0) {
        setReviewQueue(result.flashcards.map((_, i) => i))
      }
    } catch (err) {
      console.error('Failed to generate study cards:', err)
      setError('Failed to generate study cards. Try again.')
    } finally {
      setLoading(false)
    }
  }

  // ── Flashcard helpers ──
  const activeCards = useMemo(
    () => reviewQueue.length > 0 ? reviewQueue : (data?.flashcards?.map((_, i) => i) || []),
    [reviewQueue, data?.flashcards]
  )
  const currentCardIndex = activeCards[currentCard] ?? 0
  const flashcard = data?.flashcards?.[currentCardIndex]
  const totalActiveCards = activeCards.length

  const goNextCard = () => {
    setFlipped(false)
    if (currentCard < totalActiveCards - 1) {
      setCurrentCard(prev => prev + 1)
    }
  }

  const goPrevCard = () => {
    setFlipped(false)
    if (currentCard > 0) {
      setCurrentCard(prev => prev - 1)
    }
  }

  const markKnown = () => {
    setKnownCards(prev => new Set([...prev, currentCardIndex]))
    const next = activeCards.filter((_, i) => i !== currentCard)
    if (next.length === 0) {
      // All cards known — show completion
      setReviewQueue([])
      setCurrentCard(0)
      setFlipped(false)
      return
    }
    setReviewQueue(next)
    setCurrentCard(prev => Math.min(prev, next.length - 1))
    setFlipped(false)
  }

  const markReviewAgain = () => {
    // Move current card to end of queue
    const cardIdx = activeCards[currentCard]
    const next = [...activeCards.filter((_, i) => i !== currentCard), cardIdx]
    setReviewQueue(next)
    setCurrentCard(prev => Math.min(prev, next.length - 2))
    setFlipped(false)
  }

  // ── Key concepts helpers ──
  const toggleConcept = (idx) => {
    setExpandedConcepts(prev => {
      const next = new Set(prev)
      next.has(idx) ? next.delete(idx) : next.add(idx)
      return next
    })
  }

  // ── Comprehension helpers ──
  const questions = data?.comprehension_questions || []
  const currentQ = questions[currentQuestion]

  const revealAnswer = () => {
    setRevealed(prev => new Set([...prev, currentQuestion]))
  }

  const rateQuestion = (rating) => {
    setRatings(prev => ({ ...prev, [currentQuestion]: rating }))
    // Auto-advance to next question after a brief moment
    if (currentQuestion < questions.length - 1) {
      setTimeout(() => setCurrentQuestion(prev => prev + 1), 300)
    }
  }

  // ── Not yet generated ──
  if (!data) {
    return (
      <div className="bg-emerald-50/40 border border-emerald-200/60 rounded-lg p-3">
        <button
          onClick={handleGenerate}
          disabled={loading}
          className="flex items-center gap-2 w-full justify-center px-3 py-2 bg-emerald-600 hover:bg-emerald-700 disabled:bg-emerald-300 text-white rounded-lg text-[12px] font-semibold transition-all"
        >
          {loading ? (
            <>
              <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              Generating study cards...
            </>
          ) : (
            <>
              <BookIcon className="w-3.5 h-3.5" />
              Generate Study Cards
            </>
          )}
        </button>
        {error && (
          <p className="text-[11px] text-red-500 mt-2 text-center">{error}</p>
        )}
      </div>
    )
  }

  // ── All cards known (completion state) ──
  const allFlashcardsKnown = data.flashcards?.length > 0 && knownCards.size >= data.flashcards.length
  const ratedCount = Object.keys(ratings).length
  const totalQuestions = questions.length

  return (
    <div className="bg-emerald-50/30 border border-emerald-200/60 rounded-lg overflow-hidden">
      {/* Header */}
      <div className="px-3 py-2.5 bg-emerald-50/60 border-b border-emerald-200/40 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <BookIcon className="w-4 h-4 text-emerald-600" />
          <span className="text-[12px] font-bold text-emerald-800">Study Cards</span>
          <span className="text-[10px] font-semibold text-emerald-500">
            {data.flashcards?.length || 0} cards
          </span>
        </div>
        {allFlashcardsKnown && (
          <span className="flex items-center gap-1 text-[10px] font-semibold text-emerald-600">
            <CheckCircleIcon className="w-3.5 h-3.5" />
            All mastered!
          </span>
        )}
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
            <span className="text-[11px] text-amber-800 font-semibold">General study cards</span>
            <span className="text-[11px] text-amber-600 ml-1">— upload slides for targeted, content-specific flashcards</span>
          </div>
        </div>
      )}

      {/* Tab bar */}
      <div className="flex border-b border-emerald-200/40">
        {TABS.map((tab, idx) => {
          const Icon = tab.icon
          const isActive = activeTab === idx
          return (
            <button
              key={tab.label}
              onClick={() => setActiveTab(idx)}
              className={`flex-1 flex items-center justify-center gap-1.5 px-2 py-2 text-[11px] font-semibold transition-all ${
                isActive
                  ? 'text-emerald-700 border-b-2 border-emerald-500 bg-emerald-50/40'
                  : 'text-surface-400 hover:text-emerald-600 hover:bg-emerald-50/20'
              }`}
            >
              <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-emerald-600' : 'text-surface-300'}`} />
              {tab.label}
            </button>
          )
        })}
      </div>

      {/* Tab content */}
      <div className="p-3">
        {/* ═══ Tab 0: Flashcards ═══ */}
        {activeTab === 0 && (
          <div>
            {allFlashcardsKnown ? (
              /* Completion state */
              <div className="text-center py-6">
                <CheckCircleIcon className="w-8 h-8 text-emerald-500 mx-auto mb-2" />
                <p className="text-[12px] font-bold text-navy-900 mb-1">All cards mastered!</p>
                <p className="text-[11px] text-surface-400 mb-3">You marked all {data.flashcards.length} cards as known.</p>
                <button
                  onClick={() => {
                    setKnownCards(new Set())
                    setReviewQueue(data.flashcards.map((_, i) => i))
                    setCurrentCard(0)
                    setFlipped(false)
                  }}
                  className="text-[11px] font-semibold text-emerald-600 hover:text-emerald-700 underline transition-colors"
                >
                  Review again from the start
                </button>
              </div>
            ) : flashcard ? (
              <div>
                {/* Progress */}
                <div className="flex items-center justify-between mb-2.5">
                  <span className="text-[10px] font-semibold text-surface-400">
                    Card {currentCard + 1} of {totalActiveCards}
                  </span>
                  {knownCards.size > 0 && (
                    <span className="text-[10px] font-semibold text-emerald-600">
                      {knownCards.size} mastered
                    </span>
                  )}
                </div>

                {/* Progress bar */}
                <div className="h-1 bg-emerald-100 rounded-full mb-3 overflow-hidden">
                  <div
                    className="h-full bg-emerald-500 rounded-full transition-all duration-300"
                    style={{ width: `${((currentCard + 1) / totalActiveCards) * 100}%` }}
                  />
                </div>

                {/* 3D Flip Card */}
                <div
                  className="relative mx-auto mb-3 cursor-pointer"
                  style={{ perspective: '1000px', minHeight: '160px' }}
                  onClick={() => setFlipped(!flipped)}
                >
                  <div
                    className="relative w-full transition-transform duration-500"
                    style={{
                      transformStyle: 'preserve-3d',
                      transform: flipped ? 'rotateY(180deg)' : 'rotateY(0deg)',
                      minHeight: '160px',
                    }}
                  >
                    {/* Front face */}
                    <div
                      className="absolute inset-0 rounded-xl border border-emerald-200/80 bg-white p-4 flex flex-col shadow-sm"
                      style={{ backfaceVisibility: 'hidden', WebkitBackfaceVisibility: 'hidden' }}
                    >
                      <div className="flex items-center justify-between mb-3">
                        <span className={`text-[9px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full border ${
                          CATEGORY_COLORS[flashcard.category]?.bg || 'bg-emerald-100'
                        } ${CATEGORY_COLORS[flashcard.category]?.text || 'text-emerald-700'} ${
                          CATEGORY_COLORS[flashcard.category]?.border || 'border-emerald-300'
                        }`}>
                          {flashcard.category}
                        </span>
                        <span className="text-[10px] text-surface-300">Click to flip</span>
                      </div>
                      <div className="flex-1 flex items-center justify-center">
                        <p className="text-[13px] font-semibold text-navy-900 text-center leading-relaxed">
                          {flashcard.front}
                        </p>
                      </div>
                    </div>

                    {/* Back face */}
                    <div
                      className="absolute inset-0 rounded-xl border border-emerald-200/80 bg-emerald-50/60 p-4 flex flex-col shadow-sm"
                      style={{
                        backfaceVisibility: 'hidden',
                        WebkitBackfaceVisibility: 'hidden',
                        transform: 'rotateY(180deg)',
                      }}
                    >
                      <div className="flex items-center justify-between mb-3">
                        <span className="text-[9px] font-bold uppercase tracking-wider text-emerald-600">
                          Answer
                        </span>
                        <span className="text-[10px] text-surface-300">Click to flip back</span>
                      </div>
                      <div className="flex-1 flex items-center justify-center">
                        <p className="text-[12px] text-navy-800 text-center leading-relaxed">
                          {flashcard.back}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Navigation + actions */}
                <div className="flex items-center justify-between">
                  <button
                    onClick={goPrevCard}
                    disabled={currentCard === 0}
                    className="p-1.5 rounded-lg hover:bg-emerald-50 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                  >
                    <ChevronLeftIcon className="w-4 h-4 text-emerald-600" />
                  </button>

                  <div className="flex items-center gap-2">
                    <button
                      onClick={markReviewAgain}
                      className="px-3 py-1.5 rounded-lg text-[11px] font-semibold border border-amber-200 bg-amber-50 text-amber-700 hover:bg-amber-100 transition-all"
                    >
                      Review again
                    </button>
                    <button
                      onClick={markKnown}
                      className="px-3 py-1.5 rounded-lg text-[11px] font-semibold bg-emerald-600 text-white hover:bg-emerald-700 transition-all"
                    >
                      Know it
                    </button>
                  </div>

                  <button
                    onClick={goNextCard}
                    disabled={currentCard >= totalActiveCards - 1}
                    className="p-1.5 rounded-lg hover:bg-emerald-50 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                  >
                    <ChevronRightIcon className="w-4 h-4 text-emerald-600" />
                  </button>
                </div>
              </div>
            ) : null}
          </div>
        )}

        {/* ═══ Tab 1: Key Concepts ═══ */}
        {activeTab === 1 && (
          <div className="space-y-2">
            {(data.key_concepts || []).length === 0 ? (
              <p className="text-[11px] text-surface-400 text-center py-4">No key concepts generated.</p>
            ) : (
              (data.key_concepts || []).map((concept, idx) => {
                const styles = IMPORTANCE_STYLES[concept.importance] || IMPORTANCE_STYLES.important
                const isExpanded = expandedConcepts.has(idx)
                return (
                  <div
                    key={idx}
                    className={`rounded-lg border overflow-hidden transition-all ${styles.wrapper}`}
                  >
                    <button
                      onClick={() => toggleConcept(idx)}
                      className="w-full flex items-start gap-0 text-left"
                    >
                      {/* Importance accent bar */}
                      <div className={`w-[3px] self-stretch flex-shrink-0 rounded-l-lg ${styles.bar}`} />

                      <div className="flex-1 flex items-center justify-between px-3 py-2.5">
                        <div className="flex items-center gap-2 min-w-0">
                          <p className={`text-[12px] ${styles.title} truncate`}>
                            {concept.concept}
                          </p>
                          {concept.importance === 'critical' && (
                            <span className="flex-shrink-0 text-[8px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded bg-emerald-600 text-white">
                              Critical
                            </span>
                          )}
                          {concept.importance === 'supplementary' && (
                            <span className="flex-shrink-0 text-[8px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded bg-surface-200 text-surface-500">
                              Extra
                            </span>
                          )}
                        </div>
                        <ChevronDownIcon className={`w-3.5 h-3.5 text-surface-300 flex-shrink-0 ml-2 transition-transform duration-200 ${
                          isExpanded ? 'rotate-180' : ''
                        }`} />
                      </div>
                    </button>

                    {isExpanded && (
                      <div className="px-3 pb-2.5 ml-[3px]">
                        <p className="text-[11px] text-surface-400 leading-relaxed pl-0">
                          {concept.explanation}
                        </p>
                      </div>
                    )}
                  </div>
                )
              })
            )}
          </div>
        )}

        {/* ═══ Tab 2: Comprehension Check ═══ */}
        {activeTab === 2 && (
          <div>
            {totalQuestions === 0 ? (
              <p className="text-[11px] text-surface-400 text-center py-4">No comprehension questions generated.</p>
            ) : currentQ ? (
              <div>
                {/* Question card */}
                <div className="rounded-xl border border-emerald-200/60 bg-white p-4 mb-3 shadow-sm">
                  <div className="flex items-center gap-2 mb-2.5">
                    <span className="text-[9px] font-bold uppercase tracking-wider text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full">
                      Question {currentQuestion + 1}
                    </span>
                    {ratings[currentQuestion] && (
                      <span className={`text-[9px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full ${
                        ratings[currentQuestion] === 'got_it'
                          ? 'bg-emerald-100 text-emerald-700'
                          : ratings[currentQuestion] === 'partially'
                            ? 'bg-amber-100 text-amber-700'
                            : 'bg-red-100 text-red-600'
                      }`}>
                        {ratings[currentQuestion] === 'got_it' ? 'Got it' : ratings[currentQuestion] === 'partially' ? 'Partial' : 'Review'}
                      </span>
                    )}
                  </div>

                  <p className="text-[13px] font-semibold text-navy-900 leading-relaxed mb-3">
                    {currentQ.question}
                  </p>

                  {/* Hint */}
                  {currentQ.hint && (
                    <div className="bg-amber-50/60 border border-amber-200/40 rounded-lg px-2.5 py-1.5 mb-3">
                      <p className="text-[10px] font-semibold text-amber-700 mb-0.5">Hint</p>
                      <p className="text-[11px] text-amber-600 leading-relaxed">{currentQ.hint}</p>
                    </div>
                  )}

                  {/* Student answer textarea */}
                  <textarea
                    value={answers[currentQuestion] || ''}
                    onChange={(e) => setAnswers(prev => ({ ...prev, [currentQuestion]: e.target.value }))}
                    placeholder="Write your answer here..."
                    className="w-full border border-surface-200/60 rounded-lg px-3 py-2 text-[12px] text-navy-800 placeholder:text-surface-300 focus:outline-none focus:ring-2 focus:ring-emerald-300 focus:border-emerald-400 resize-none transition-all"
                    rows={3}
                  />

                  {/* Reveal button */}
                  {!revealed.has(currentQuestion) ? (
                    <button
                      onClick={revealAnswer}
                      className="mt-2.5 w-full px-3 py-2 rounded-lg text-[11px] font-semibold bg-emerald-50 border border-emerald-200/60 text-emerald-700 hover:bg-emerald-100 transition-all"
                    >
                      Reveal Sample Answer
                    </button>
                  ) : (
                    <div className="mt-2.5">
                      <div className="bg-emerald-50/60 border border-emerald-200/60 rounded-lg px-3 py-2.5 mb-2.5">
                        <p className="text-[10px] font-bold text-emerald-700 mb-1">Sample Answer</p>
                        <p className="text-[11px] text-emerald-800 leading-relaxed">{currentQ.sample_answer}</p>
                      </div>

                      {/* Self-rating buttons */}
                      {!ratings[currentQuestion] && (
                        <div className="flex items-center gap-2">
                          <span className="text-[10px] font-semibold text-surface-400 mr-1">Rate yourself:</span>
                          <button
                            onClick={() => rateQuestion('got_it')}
                            className="flex-1 px-2 py-1.5 rounded-lg text-[11px] font-semibold bg-emerald-600 text-white hover:bg-emerald-700 transition-all"
                          >
                            Got it
                          </button>
                          <button
                            onClick={() => rateQuestion('partially')}
                            className="flex-1 px-2 py-1.5 rounded-lg text-[11px] font-semibold bg-amber-500 text-white hover:bg-amber-600 transition-all"
                          >
                            Partially
                          </button>
                          <button
                            onClick={() => rateQuestion('review')}
                            className="flex-1 px-2 py-1.5 rounded-lg text-[11px] font-semibold bg-red-500 text-white hover:bg-red-600 transition-all"
                          >
                            Need to review
                          </button>
                        </div>
                      )}
                    </div>
                  )}
                </div>

                {/* Navigation between questions */}
                <div className="flex items-center justify-between">
                  <button
                    onClick={() => setCurrentQuestion(prev => Math.max(0, prev - 1))}
                    disabled={currentQuestion === 0}
                    className="p-1.5 rounded-lg hover:bg-emerald-50 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                  >
                    <ChevronLeftIcon className="w-4 h-4 text-emerald-600" />
                  </button>

                  {/* Progress dots */}
                  <div className="flex items-center gap-1.5">
                    {questions.map((_, idx) => (
                      <button
                        key={idx}
                        onClick={() => setCurrentQuestion(idx)}
                        className={`w-2 h-2 rounded-full transition-all ${
                          idx === currentQuestion
                            ? 'bg-emerald-500 scale-125'
                            : ratings[idx]
                              ? ratings[idx] === 'got_it'
                                ? 'bg-emerald-300'
                                : ratings[idx] === 'partially'
                                  ? 'bg-amber-300'
                                  : 'bg-red-300'
                              : 'bg-surface-200'
                        }`}
                      />
                    ))}
                  </div>

                  <button
                    onClick={() => setCurrentQuestion(prev => Math.min(totalQuestions - 1, prev + 1))}
                    disabled={currentQuestion >= totalQuestions - 1}
                    className="p-1.5 rounded-lg hover:bg-emerald-50 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                  >
                    <ChevronRightIcon className="w-4 h-4 text-emerald-600" />
                  </button>
                </div>

                {/* Summary when all rated */}
                {ratedCount === totalQuestions && totalQuestions > 0 && (
                  <div className="mt-3 bg-emerald-50/60 border border-emerald-200/60 rounded-lg px-3 py-2.5 text-center">
                    <p className="text-[11px] font-bold text-emerald-800 mb-0.5">Comprehension Complete</p>
                    <p className="text-[10px] text-emerald-600">
                      {Object.values(ratings).filter(r => r === 'got_it').length} got it
                      {' / '}
                      {Object.values(ratings).filter(r => r === 'partially').length} partial
                      {' / '}
                      {Object.values(ratings).filter(r => r === 'review').length} need review
                    </p>
                  </div>
                )}
              </div>
            ) : null}
          </div>
        )}
      </div>
    </div>
  )
}
