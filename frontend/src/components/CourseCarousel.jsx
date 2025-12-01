import { useRef, useState, useEffect } from 'react'

/**
 * Get gradient colors based on predicted grade (PAU scale)
 * A: 5.0, B: 4.0, C: 3.0, D: 2.0, E: 1.0, F: 0.0
 */
const getGradeColors = (gradePoint) => {
  if (!gradePoint || gradePoint === 0) return { from: '#f87171', to: '#dc2626' } // red - F
  if (gradePoint >= 5.0) return { from: '#34d399', to: '#059669' } // emerald-400 to emerald-600 - A
  if (gradePoint >= 4.0) return { from: '#60a5fa', to: '#2563eb' } // blue-400 to blue-600 - B
  if (gradePoint >= 3.0) return { from: '#fbbf24', to: '#d97706' } // amber-400 to amber-600 - C
  if (gradePoint >= 2.0) return { from: '#fb923c', to: '#ea580c' } // orange-400 to orange-600 - D
  return { from: '#ef4444', to: '#b91c1c' } // red-500 to red-700 - E
}

/**
 * Get box shadow based on grade (PAU scale)
 */
const getGradeShadow = (gradePoint) => {
  if (!gradePoint || gradePoint === 0) return '0 10px 15px -3px rgba(239, 68, 68, 0.4), 0 4px 6px -4px rgba(239, 68, 68, 0.4)'
  if (gradePoint >= 5.0) return '0 10px 15px -3px rgba(16, 185, 129, 0.4), 0 4px 6px -4px rgba(16, 185, 129, 0.4)'
  if (gradePoint >= 4.0) return '0 10px 15px -3px rgba(59, 130, 246, 0.4), 0 4px 6px -4px rgba(59, 130, 246, 0.4)'
  if (gradePoint >= 3.0) return '0 10px 15px -3px rgba(245, 158, 11, 0.4), 0 4px 6px -4px rgba(245, 158, 11, 0.4)'
  if (gradePoint >= 2.0) return '0 10px 15px -3px rgba(249, 115, 22, 0.4), 0 4px 6px -4px rgba(249, 115, 22, 0.4)'
  return '0 10px 15px -3px rgba(220, 38, 38, 0.4), 0 4px 6px -4px rgba(220, 38, 38, 0.4)'
}

/**
 * Get grade letter from grade point (PAU scale)
 */
const getGradeLetter = (gradePoint) => {
  if (!gradePoint || gradePoint === 0) return 'F'
  if (gradePoint >= 5.0) return 'A'
  if (gradePoint >= 4.0) return 'B'
  if (gradePoint >= 3.0) return 'C'
  if (gradePoint >= 2.0) return 'D'
  if (gradePoint >= 1.0) return 'E'
  return 'F'
}

/**
 * Mini circular progress ring
 */
const MiniProgress = ({ value, max }) => {
  const percentage = Math.min((value / max) * 100, 100)
  return (
    <div className="relative w-10 h-10">
      <svg className="w-10 h-10 transform -rotate-90">
        <circle
          cx="20" cy="20" r="16"
          fill="none"
          stroke="rgba(255,255,255,0.2)"
          strokeWidth="3"
        />
        <circle
          cx="20" cy="20" r="16"
          fill="none"
          stroke="white"
          strokeWidth="3"
          strokeLinecap="round"
          strokeDasharray={100.53}
          strokeDashoffset={100.53 - (percentage / 100) * 100.53}
          className="transition-all duration-500"
        />
      </svg>
      <div className="absolute inset-0 flex items-center justify-center">
        <span className="text-white text-xs font-bold">{Math.round(percentage)}%</span>
      </div>
    </div>
  )
}

/**
 * CourseCarousel - Auto-scrolling infinite carousel of enrolled courses
 * Premium design with dark background and glowing cards
 */
export default function CourseCarousel({ enrolledCourses, onCourseClick }) {
  const scrollRef = useRef(null)
  const [isPaused, setIsPaused] = useState(false)
  const animationRef = useRef(null)
  const scrollPositionRef = useRef(0)
  const pauseTimeoutRef = useRef(null)

  const handleCardEnter = () => {
    if (pauseTimeoutRef.current) clearTimeout(pauseTimeoutRef.current)
    setIsPaused(true)
  }

  const handleCardLeave = () => {
    // Small delay before resuming to prevent jitter between cards
    pauseTimeoutRef.current = setTimeout(() => setIsPaused(false), 150)
  }

  // Duplicate courses for infinite scroll effect
  const duplicatedCourses = enrolledCourses?.length > 0
    ? [...enrolledCourses, ...enrolledCourses, ...enrolledCourses]
    : []

  useEffect(() => {
    if (!enrolledCourses || enrolledCourses.length === 0) return

    const scrollContainer = scrollRef.current
    if (!scrollContainer) return

    const cardWidth = 280 // Card width + gap
    const totalWidth = cardWidth * enrolledCourses.length

    // Start from middle set
    scrollPositionRef.current = totalWidth
    scrollContainer.scrollLeft = totalWidth

    const animate = () => {
      if (!isPaused && scrollContainer) {
        scrollPositionRef.current += 0.6 // Smooth scroll speed

        // Reset to middle when reaching end
        if (scrollPositionRef.current >= totalWidth * 2) {
          scrollPositionRef.current = totalWidth
        }

        scrollContainer.scrollLeft = scrollPositionRef.current
      }
      animationRef.current = requestAnimationFrame(animate)
    }

    animationRef.current = requestAnimationFrame(animate)

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current)
      }
    }
  }, [enrolledCourses, isPaused])

  if (!enrolledCourses || enrolledCourses.length === 0) {
    return null
  }

  return (
    <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-navy-900 via-navy-800 to-slate-900 py-6 pb-8">
      {/* Decorative background elements */}
      <div className="absolute top-0 left-1/4 w-64 h-64 bg-navy-600/20 rounded-full blur-3xl" />
      <div className="absolute bottom-0 right-1/4 w-48 h-48 bg-blue-600/20 rounded-full blur-3xl" />

      {/* Header */}
      <div className="relative z-10 flex justify-between items-center px-6 mb-4">
        <div>
          <h3 className="text-white font-bold text-lg">Your Courses</h3>
          <p className="text-white/60 text-sm">{enrolledCourses.length} enrolled courses</p>
        </div>
      </div>

      {/* Gradient fade edges */}
      <div className="absolute left-0 top-0 bottom-0 w-20 bg-gradient-to-r from-navy-900 to-transparent z-10 pointer-events-none" />
      <div className="absolute right-0 top-0 bottom-0 w-20 bg-gradient-to-l from-slate-900 to-transparent z-10 pointer-events-none" />

      {/* Scrolling container */}
      <div
        ref={scrollRef}
        className={`flex gap-5 px-6 py-4 ${isPaused ? 'overflow-x-auto scrollbar-hide' : 'overflow-x-hidden'}`}
      >
        {duplicatedCourses.map((enrollment, index) => {
          // Calculate ACTUAL total score including participation
          const caFromTasks = enrollment.ca_score || 0  // Out of 30
          const participationScore = enrollment.participation_score || 0  // Out of 5
          const totalCA = caFromTasks + participationScore  // Out of 35
          const examScore = enrollment.exam_score || 0  // Out of 65
          const totalScore = totalCA + examScore  // Out of 100

          const taskCompletion = enrollment.completion_rate || 0

          // Use predicted grade point if available, otherwise estimate from current score
          let gradePoint = enrollment.predicted_grade_point
          let isEstimated = false

          // Only use predicted grade point if it's a valid number (and not 0)
          if (gradePoint === null || gradePoint === undefined || gradePoint === 0) {
            if (examScore > 0) {
              // Both CA and exam exist - use actual total score with PAU grading scale
              if (totalScore >= 70) gradePoint = 5.0        // A
              else if (totalScore >= 60) gradePoint = 4.0   // B
              else if (totalScore >= 50) gradePoint = 3.0   // C
              else if (totalScore >= 45) gradePoint = 2.0   // D
              else if (totalScore >= 40) gradePoint = 1.0   // E
              else gradePoint = 0.0                         // F
              isEstimated = true
            } else if (totalCA > 0) {
              // Only CA exists - predict using 85% retention model
              // If participation not entered, assume 3/5 (average)
              const caForPrediction = enrollment.participation_score
                ? totalCA  // Use actual total CA
                : caFromTasks + 3.0  // Add assumed 3 if not set

              // Predict exam score: (CA/35) * 0.85 * 65
              const caPercentage = caForPrediction / 35.0
              const predictedExam = caPercentage * 0.85 * 65.0
              const predictedTotal = caForPrediction + predictedExam

              // Apply PAU grading scale to predicted total
              if (predictedTotal >= 70) gradePoint = 5.0      // A
              else if (predictedTotal >= 60) gradePoint = 4.0 // B
              else if (predictedTotal >= 50) gradePoint = 3.0 // C
              else if (predictedTotal >= 45) gradePoint = 2.0 // D
              else if (predictedTotal >= 40) gradePoint = 1.0 // E
              else gradePoint = 0.0                           // F
              isEstimated = true
            } else {
              // No data yet - use a neutral blue color to indicate potential (optimistic view)
              gradePoint = 4.0 // B grade color - represents potential/target
              isEstimated = true
            }
          }

          const gradeLetter = enrollment.predicted_letter_grade || (isEstimated && totalScore === 0 ? '?' : getGradeLetter(gradePoint))

          const colors = getGradeColors(gradePoint)
          const shadow = getGradeShadow(gradePoint)

          return (
            <div
              key={`${enrollment.id}-${index}`}
              onClick={() => onCourseClick?.(enrollment)}
              onMouseEnter={handleCardEnter}
              onMouseLeave={handleCardLeave}
              className="flex-shrink-0 w-64 h-36 rounded-xl p-5 cursor-pointer transform hover:scale-105 hover:-translate-y-1 transition-all duration-300 relative"
              style={{
                background: `linear-gradient(to bottom right, ${colors.from}, ${colors.to})`,
                boxShadow: shadow
              }}
            >
              {/* Top row - Course code and grade */}
              <div className="flex justify-between items-start mb-3">
                <div className="flex-1 min-w-0 pr-3">
                  <h4 className="text-white font-bold text-xl truncate">
                    {enrollment.course.code}
                  </h4>
                  <p className="text-white/70 text-xs truncate mt-0.5">
                    {enrollment.course.title}
                  </p>
                </div>

                {/* Grade badge */}
                <div className="flex flex-col items-center">
                  <span className="text-[10px] text-white/60 uppercase tracking-wider">Grade</span>
                  <div className="bg-white/20 backdrop-blur-sm rounded-lg px-3 py-1 mt-0.5">
                    <span className="text-white font-black text-2xl">{gradeLetter}</span>
                  </div>
                </div>
              </div>

              {/* Bottom row - Stats */}
              <div className="flex justify-between items-end">
                {/* Score info */}
                <div>
                  <div className="flex items-baseline gap-1">
                    <span className="text-white font-bold text-2xl">{totalScore.toFixed(0)}</span>
                    <span className="text-white/60 text-sm">/100</span>
                  </div>
                  <div className="flex items-center gap-2 mt-1">
                    {/* Show CA breakdown */}
                    {(() => {
                      const isAssumed = !enrollment.participation_score

                      return (
                        <>
                          <span className="text-white/70 text-xs">
                            CA: {totalCA.toFixed(0)}/35
                          </span>
                          {isAssumed && (
                            <span className="text-white/50 text-[10px]">(+3 est.)</span>
                          )}
                        </>
                      )
                    })()}
                    <span className="text-white/40">•</span>
                    <span className="text-white/70 text-xs">{enrollment.course.credits} cr</span>
                  </div>
                </div>

                {/* Task completion ring */}
                <div className="flex flex-col items-center">
                  <MiniProgress value={taskCompletion} max={100} />
                  <span className="text-[10px] text-white/60 mt-1">Tasks</span>
                </div>
              </div>

              {/* Priority indicator */}
              {enrollment.is_priority && (
                <div className="absolute -top-1 -right-1">
                  <div className="bg-amber-400 text-amber-900 text-[10px] font-bold px-2 py-0.5 rounded-full shadow-lg">
                    PRIORITY
                  </div>
                </div>
              )}
            </div>
          )
        })}
      </div>

    </div>
  )
}
