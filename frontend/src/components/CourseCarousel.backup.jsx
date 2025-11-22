import { useRef, useState, useEffect } from 'react'

/**
 * Get gradient class based on predicted grade
 */
const getGradeGradient = (gradePoint) => {
  if (!gradePoint) return 'from-stone-600 to-stone-700'
  if (gradePoint >= 4.5) return 'from-emerald-500 to-emerald-700' // A
  if (gradePoint >= 3.5) return 'from-blue-500 to-blue-700'       // B
  if (gradePoint >= 2.5) return 'from-amber-500 to-amber-700'     // C
  if (gradePoint >= 1.5) return 'from-orange-500 to-orange-700'   // D
  return 'from-red-500 to-red-700'                                 // E/F
}

/**
 * Get grade letter from grade point
 */
const getGradeLetter = (gradePoint) => {
  if (!gradePoint) return '-'
  if (gradePoint >= 4.5) return 'A'
  if (gradePoint >= 3.5) return 'B'
  if (gradePoint >= 2.5) return 'C'
  if (gradePoint >= 1.5) return 'D'
  if (gradePoint >= 1.0) return 'E'
  return 'F'
}

/**
 * CourseCarousel - Auto-scrolling infinite carousel of enrolled courses
 * Shows at top of dashboard, continuously scrolls, pauses on hover
 */
export default function CourseCarousel({ enrolledCourses, onCourseClick }) {
  const scrollRef = useRef(null)
  const [isPaused, setIsPaused] = useState(false)
  const animationRef = useRef(null)
  const scrollPositionRef = useRef(0)

  // Duplicate courses for infinite scroll effect
  const duplicatedCourses = enrolledCourses?.length > 0
    ? [...enrolledCourses, ...enrolledCourses, ...enrolledCourses]
    : []

  useEffect(() => {
    if (!enrolledCourses || enrolledCourses.length === 0) return

    const scrollContainer = scrollRef.current
    if (!scrollContainer) return

    const cardWidth = 220 // Card width + gap
    const totalWidth = cardWidth * enrolledCourses.length

    // Start from middle set
    scrollPositionRef.current = totalWidth
    scrollContainer.scrollLeft = totalWidth

    const animate = () => {
      if (!isPaused && scrollContainer) {
        scrollPositionRef.current += 0.5 // Speed of scroll

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
    return null // Don't show carousel if no courses
  }

  return (
    <div
      className="relative overflow-hidden rounded-xl bg-gradient-to-r from-stone-100 via-stone-50 to-stone-100 py-4"
      onMouseEnter={() => setIsPaused(true)}
      onMouseLeave={() => setIsPaused(false)}
    >
      {/* Label */}
      <div className="absolute top-2 left-4 z-10">
        <span className="text-xs font-medium text-stone-500 uppercase tracking-wider">
          Your Courses
        </span>
      </div>

      {/* Pause indicator */}
      {isPaused && (
        <div className="absolute top-2 right-4 z-10">
          <span className="text-xs font-medium text-navy-800 bg-white/80 px-2 py-1 rounded-full">
            ⏸ Paused - Click a course
          </span>
        </div>
      )}

      {/* Gradient fade edges */}
      <div className="absolute left-0 top-0 bottom-0 w-16 bg-gradient-to-r from-stone-100 to-transparent z-10 pointer-events-none" />
      <div className="absolute right-0 top-0 bottom-0 w-16 bg-gradient-to-l from-stone-100 to-transparent z-10 pointer-events-none" />

      {/* Scrolling container */}
      <div
        ref={scrollRef}
        className="flex gap-4 overflow-x-hidden pt-6 pb-2 px-4"
      >
        {duplicatedCourses.map((enrollment, index) => {
          const gradePoint = enrollment.predicted_grade_point
          const gradeLetter = enrollment.predicted_letter_grade || getGradeLetter(gradePoint)
          const totalScore = (enrollment.ca_score || 0) + (enrollment.exam_score || 0)

          return (
            <div
              key={`${enrollment.id}-${index}`}
              onClick={() => onCourseClick?.(enrollment)}
              className={`flex-shrink-0 w-52 h-28 rounded-xl bg-gradient-to-br ${getGradeGradient(gradePoint)} p-4 cursor-pointer transform hover:scale-105 hover:shadow-lg transition-all duration-200`}
            >
              {/* Course Info */}
              <div className="flex justify-between items-start">
                <div className="flex-1 min-w-0">
                  <h3 className="text-white font-bold text-lg truncate">
                    {enrollment.course.code}
                  </h3>
                  <p className="text-white/70 text-xs truncate">
                    {enrollment.course.title}
                  </p>
                </div>

                {/* Grade Badge */}
                <div className="bg-white/25 backdrop-blur-sm rounded-lg px-2.5 py-1 ml-2">
                  <span className="text-white font-black text-xl">{gradeLetter}</span>
                </div>
              </div>

              {/* Bottom stats */}
              <div className="flex justify-between items-end mt-3">
                <div className="text-white/80 text-xs">
                  <span className="font-semibold text-white">{totalScore.toFixed(0)}</span>/100
                </div>
                <div className="text-white/80 text-xs">
                  CA: <span className="font-semibold text-white">{(enrollment.ca_score || 0).toFixed(0)}</span>/35
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
