import { useRef, useState, useEffect, memo } from 'react'
import { useNavigate } from 'react-router-dom'

/* ─── Grade system (PAU 5.0 scale) — Deep gemstone tones ───
   Rich enough to clearly indicate course health against
   the dark navy container, but not billboard-bright.       */
const gradeConfig = (gp) => {
  if (!gp || gp === 0) return { letter: 'F', from: '#b83a3a', to: '#7a2222', glow: 'rgba(184,58,58,0.30)' }
  if (gp >= 5.0) return { letter: 'A', from: '#1d8a62', to: '#0f5e40', glow: 'rgba(29,138,98,0.30)' }
  if (gp >= 4.0) return { letter: 'B', from: '#2e6db8', to: '#1b4a8a', glow: 'rgba(46,109,184,0.30)' }
  if (gp >= 3.0) return { letter: 'C', from: '#b8862e', to: '#8a631e', glow: 'rgba(184,134,46,0.30)' }
  if (gp >= 2.0) return { letter: 'D', from: '#b8622e', to: '#8a441e', glow: 'rgba(184,98,46,0.30)' }
  if (gp >= 1.0) return { letter: 'E', from: '#b83a3a', to: '#7a2222', glow: 'rgba(184,58,58,0.30)' }
  return { letter: 'F', from: '#b83a3a', to: '#7a2222', glow: 'rgba(184,58,58,0.30)' }
}

const getGradeLetter = (gp) => gradeConfig(gp).letter

/* ═══════════════════════════════════════
   CourseCarousel
   ═══════════════════════════════════════ */
const CourseCarousel = memo(function CourseCarousel({ enrolledCourses, onCourseClick }) {
  const navigate = useNavigate()
  const scrollRef = useRef(null)
  const [isPaused, setIsPaused] = useState(false)
  const animRef = useRef(null)
  const posRef = useRef(0)
  const pauseTimer = useRef(null)

  const pause = () => { clearTimeout(pauseTimer.current); setIsPaused(true) }
  const resume = () => { pauseTimer.current = setTimeout(() => setIsPaused(false), 200) }

  const duped = enrolledCourses?.length > 0
    ? [...enrolledCourses, ...enrolledCourses, ...enrolledCourses]
    : []

  useEffect(() => {
    if (!enrolledCourses?.length) return
    const el = scrollRef.current
    if (!el) return

    const cardW = 260
    const setW = cardW * enrolledCourses.length
    posRef.current = setW
    el.scrollLeft = setW

    const tick = () => {
      if (!isPaused && el) {
        posRef.current += 0.5
        if (posRef.current >= setW * 2) posRef.current = setW
        el.scrollLeft = posRef.current
      }
      animRef.current = requestAnimationFrame(tick)
    }
    animRef.current = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(animRef.current)
  }, [enrolledCourses, isPaused])

  if (!enrolledCourses?.length) return null

  return (
    <div className="relative overflow-hidden rounded-2xl">
      {/* Dark container */}
      <div className="absolute inset-0 bg-gradient-to-br from-[#0c1425] via-[#111b33] to-[#0e1628]" />
      <div className="absolute inset-0 opacity-[0.02]" style={{
        backgroundImage: 'linear-gradient(rgba(255,255,255,0.12) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.12) 1px, transparent 1px)',
        backgroundSize: '32px 32px',
      }} />

      <div className="relative z-10 py-5">
        {/* Header */}
        <div className="flex items-center justify-between px-6 mb-4">
          <div className="flex items-center gap-2.5">
            <div className="w-1 h-4 rounded-full bg-gradient-to-b from-blue-400 to-navy-500" />
            <h3 className="text-[14px] font-bold text-white/90">Your Courses</h3>
            <span className="text-[11px] font-mono text-white/30">{enrolledCourses.length}</span>
          </div>
        </div>

        {/* Fade edges */}
        <div className="absolute left-0 top-0 bottom-0 w-16 bg-gradient-to-r from-[#0c1425] to-transparent z-20 pointer-events-none" />
        <div className="absolute right-0 top-0 bottom-0 w-16 bg-gradient-to-l from-[#0e1628] to-transparent z-20 pointer-events-none" />

        {/* Scroll track */}
        <div
          ref={scrollRef}
          className={`flex gap-3.5 px-6 ${isPaused ? 'overflow-x-auto scrollbar-hide' : 'overflow-x-hidden'}`}
        >
          {duped.map((enrollment, idx) => {
            // FYP / single-grade: one score out of 100 (stored in exam_score)
            const isFYP = enrollment.course?.grading_type === 'single_grade'
            const ca = enrollment.ca_score || 0
            const part = enrollment.participation_score || 0
            const totalCA = ca + part
            const exam = enrollment.exam_score || 0
            const total = isFYP ? exam : totalCA + exam
            const taskPct = enrollment.completion_rate || 0
            // Pending FYP: project hasn't been graded yet (no score, no predicted GP)
            const fypPending = isFYP && !exam && (enrollment.predicted_grade_point === null || enrollment.predicted_grade_point === undefined)

            let gp = enrollment.predicted_grade_point
            let estimated = false
            if (gp === null || gp === undefined || gp === 0) {
              estimated = true
              if (fypPending) {
                gp = 4  // neutral card colour while ungraded; shown as "Pending"
              } else if (isFYP) {
                gp = total >= 70 ? 5 : total >= 60 ? 4 : total >= 50 ? 3 : total >= 45 ? 2 : total >= 40 ? 1 : 0
              } else if (exam > 0) {
                gp = total >= 70 ? 5 : total >= 60 ? 4 : total >= 50 ? 3 : total >= 45 ? 2 : total >= 40 ? 1 : 0
              } else if (totalCA > 0) {
                const caP = (part ? totalCA : ca + 3) / 35
                const pred = (part ? totalCA : ca + 3) + caP * 0.85 * 65
                gp = pred >= 70 ? 5 : pred >= 60 ? 4 : pred >= 50 ? 3 : pred >= 45 ? 2 : pred >= 40 ? 1 : 0
              } else {
                gp = 4
              }
            }

            const letter = fypPending ? '—' : (enrollment.predicted_letter_grade || (estimated && total === 0 ? '—' : getGradeLetter(gp)))
            const g = gradeConfig(gp)
            const isAssumed = !enrollment.participation_score

            return (
              <div
                key={`${enrollment.id}-${idx}`}
                onClick={() => onCourseClick?.(enrollment)}
                onMouseEnter={pause}
                onMouseLeave={resume}
                className="flex-shrink-0 w-[244px] group cursor-pointer"
              >
                <div
                  className="relative rounded-xl h-[156px] flex flex-col justify-between transition-all duration-300 group-hover:-translate-y-1 group-hover:scale-[1.02] overflow-hidden"
                  style={{
                    background: `linear-gradient(135deg, ${g.from}, ${g.to})`,
                    boxShadow: `0 4px 14px -4px ${g.glow}, 0 0 0 0 transparent`,
                  }}
                  onMouseEnter={(e) => e.currentTarget.style.boxShadow = `0 12px 32px -6px ${g.glow}, 0 0 0 1px rgba(255,255,255,0.08)`}
                  onMouseLeave={(e) => e.currentTarget.style.boxShadow = `0 4px 14px -4px ${g.glow}, 0 0 0 0 transparent`}
                >
                  {/* Highlight shimmer */}
                  <div className="absolute inset-0 bg-gradient-to-br from-white/[0.12] via-transparent to-black/[0.08]" />
                  {/* Corner accent */}
                  <div className="absolute top-0 right-0 w-24 h-24 bg-white/[0.06] rounded-bl-[60px]" />

                  {/* Content */}
                  <div className="relative z-10 p-4 flex flex-col h-full justify-between">
                    {/* Top: code + grade */}
                    <div className="flex items-start justify-between">
                      <div className="min-w-0 flex-1 pr-3">
                        <h4 className="text-[16px] font-bold text-white truncate leading-tight tracking-tight">{enrollment.course.code}</h4>
                        <p className="text-[10px] text-white/60 truncate mt-0.5">{enrollment.course.title}</p>
                      </div>
                      <div className="w-11 h-11 rounded-lg bg-white/20 backdrop-blur-sm flex items-center justify-center border border-white/10">
                        <span className="font-display text-[22px] font-bold text-white drop-shadow-sm">{letter}</span>
                      </div>
                    </div>

                    {/* Bottom: scores */}
                    <div>
                      {/* Score + CA breakdown */}
                      <div className="flex items-end justify-between mb-2">
                        <div className="flex items-baseline gap-1">
                          {fypPending ? (
                            <span className="font-display text-[15px] font-semibold text-white/80 leading-none">Pending</span>
                          ) : (
                            <>
                              <span className="font-mono text-[22px] font-bold text-white leading-none">{total}</span>
                              <span className="text-[11px] text-white/50">/100</span>
                            </>
                          )}
                        </div>
                        <div className="text-right">
                          <span className="text-[10px] text-white/60">
                            {isFYP ? (fypPending ? 'Not graded yet' : 'Project') : <>CA {totalCA}/35{isAssumed && '*'}</>}
                          </span>
                          <span className="text-white/30 mx-1">·</span>
                          <span className="text-[10px] text-white/60">{enrollment.course.credits}cr</span>
                        </div>
                      </div>

                      {/* Full-width score bar */}
                      <div className="h-1.5 bg-black/20 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-white/70 rounded-full transition-all duration-700"
                          style={{ width: `${total}%` }}
                        />
                      </div>

                      {/* Tasks completion row */}
                      <div className="flex items-center justify-between mt-1.5">
                        <span className="text-[9px] text-white/40 uppercase tracking-wider font-medium">Tasks</span>
                        <div className="flex items-center gap-1.5">
                          <div className="w-14 h-1 bg-black/20 rounded-full overflow-hidden">
                            <div className="h-full bg-white/50 rounded-full transition-all duration-500" style={{ width: `${taskPct}%` }} />
                          </div>
                          <span className="font-mono text-[9px] font-semibold text-white/50">{Math.round(taskPct)}%</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Priority flag */}
                  {enrollment.is_priority && (
                    <div className="absolute top-3 right-3 z-20">
                      <div className="bg-white/25 backdrop-blur-sm text-white text-[8px] font-bold px-2 py-0.5 rounded-md uppercase tracking-wider border border-white/20">
                        Priority
                      </div>
                    </div>
                  )}

                  {/* Get Help indicator for struggling courses */}
                  {gp < 3.0 && gp > 0 && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        navigate('/smartstudy', { state: { courseCode: enrollment.course.code, courseName: enrollment.course.title } })
                      }}
                      className="absolute bottom-2.5 right-3 z-20 flex items-center gap-1 bg-white/20 backdrop-blur-sm text-white text-[9px] font-semibold px-2 py-1 rounded-md border border-white/15 hover:bg-white/30 transition-colors"
                      title={`Get study help for ${enrollment.course.code}`}
                    >
                      <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M4.26 10.147a60.438 60.438 0 0 0-.491 6.347A48.62 48.62 0 0 1 12 20.904a48.62 48.62 0 0 1 8.232-4.41 60.46 60.46 0 0 0-.491-6.347m-15.482 0a50.636 50.636 0 0 0-2.658-.813A59.906 59.906 0 0 1 12 3.493a59.903 59.903 0 0 1 10.399 5.84c-.896.248-1.783.52-2.658.814m-15.482 0A50.717 50.717 0 0 1 12 13.489a50.702 50.702 0 0 1 7.74-3.342" />
                      </svg>
                      Get Help
                    </button>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
})

export default CourseCarousel
