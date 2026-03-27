import { useState, useEffect, useCallback, memo } from 'react'
import { useNavigate } from 'react-router-dom'

/* ─── Walkthrough Steps ─── */
const STEPS = [
  {
    number: '01',
    title: 'Welcome to Shadow',
    subtitle: 'Your academic command centre',
    description: 'Shadow tracks every point toward your target CGPA — courses, tasks, grades, and AI-powered study plans built around how you learn best.',
    accent: 'from-navy-600 to-navy-800',
    orb: 'bg-navy-500/20',
    icon: (
      <svg className="w-full h-full" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.2">
        <path strokeLinecap="round" strokeLinejoin="round" d="M4.26 10.147a60.436 60.436 0 00-.491 6.347A48.627 48.627 0 0112 20.904a48.627 48.627 0 018.232-4.41 60.46 60.46 0 00-.491-6.347m-15.482 0a50.57 50.57 0 00-2.658-.813A59.905 59.905 0 0112 3.493a59.902 59.902 0 0110.399 5.84c-.896.248-1.783.52-2.658.814m-15.482 0A50.697 50.697 0 0112 13.489a50.702 50.702 0 017.74-3.342M6.75 15a.75.75 0 100-1.5.75.75 0 000 1.5zm0 0v-3.675A55.378 55.378 0 0112 8.443m-7.007 11.55A5.981 5.981 0 006.75 15.75v-1.5" />
      </svg>
    ),
  },
  {
    number: '02',
    title: 'Your Dashboard',
    subtitle: 'Everything at a glance',
    description: 'See your CGPA progress ring, upcoming tasks ranked by priority, enrolled courses, and mood-aware recommendations — all in real time.',
    accent: 'from-emerald-500 to-emerald-700',
    orb: 'bg-emerald-500/20',
    icon: (
      <svg className="w-full h-full" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.2">
        <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 3v11.25A2.25 2.25 0 006 16.5h2.25M3.75 3h-1.5m1.5 0h16.5m0 0h1.5m-1.5 0v11.25A2.25 2.25 0 0118 16.5h-2.25m-7.5 0h7.5m-7.5 0l-1 3m8.5-3l1 3m0 0l.5 1.5m-.5-1.5h-9.5m0 0l-.5 1.5M9 11.25v1.5M12 9v3.75m3-6v6" />
      </svg>
    ),
  },
  {
    number: '03',
    title: 'Courses & CGPA',
    subtitle: 'Track every point',
    description: 'Enroll in your PAU courses, log CA and exam scores, and watch your CGPA update instantly. Use the What-If Calculator to plan ahead.',
    accent: 'from-blue-500 to-blue-700',
    orb: 'bg-blue-500/20',
    icon: (
      <svg className="w-full h-full" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.2">
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 016-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0018 18a8.967 8.967 0 00-6 2.292m0-14.25v14.25" />
      </svg>
    ),
  },
  {
    number: '04',
    title: 'SmartStudy AI',
    subtitle: 'Learn your way',
    description: 'Upload your slides, pick your learning style — Visual, Audio, Reading, or Hands-on — and get a personalised study plan with videos, podcasts, quizzes, and exercises.',
    accent: 'from-violet-500 to-violet-700',
    orb: 'bg-violet-500/20',
    icon: (
      <svg className="w-full h-full" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.2">
        <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 00-2.455 2.456zM16.894 20.567L16.5 21.75l-.394-1.183a2.25 2.25 0 00-1.423-1.423L13.5 18.75l1.183-.394a2.25 2.25 0 001.423-1.423l.394-1.183.394 1.183a2.25 2.25 0 001.423 1.423l1.183.394-1.183.394a2.25 2.25 0 00-1.423 1.423z" />
      </svg>
    ),
  },
  {
    number: '05',
    title: 'Learning Library',
    subtitle: 'Share & discover',
    description: 'Upload PDFs and lecture slides for your classmates. Browse resources by course. Everything your class needs in one place.',
    accent: 'from-amber-500 to-amber-700',
    orb: 'bg-amber-500/20',
    icon: (
      <svg className="w-full h-full" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.2">
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 21v-8.25M15.75 21v-8.25M8.25 21v-8.25M3 9l9-6 9 6m-1.5 12V10.332A48.36 48.36 0 0012 9.75c-2.551 0-5.056.2-7.5.582V21M3 21h18M12 6.75h.008v.008H12V6.75z" />
      </svg>
    ),
  },
  {
    number: '06',
    title: "You're all set",
    subtitle: 'Start with your courses',
    description: "Enroll in your courses first — that unlocks CGPA tracking, task management, and personalised SmartStudy plans. Let's go.",
    accent: 'from-emerald-500 to-navy-700',
    orb: 'bg-emerald-500/15',
    icon: (
      <svg className="w-full h-full" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.2">
        <path strokeLinecap="round" strokeLinejoin="round" d="M15.59 14.37a6 6 0 01-5.84 7.38v-4.8m5.84-2.58a14.98 14.98 0 006.16-12.12A14.98 14.98 0 009.631 8.41m5.96 5.96a14.926 14.926 0 01-5.841 2.58m-.119-8.54a6 6 0 00-7.381 5.84h4.8m2.581-5.84a14.927 14.927 0 00-2.58 5.84m2.699 2.7c-.103.021-.207.041-.311.06a15.09 15.09 0 01-2.448-2.448 14.9 14.9 0 01.06-.312m-2.24 2.39a4.493 4.493 0 00-1.757 4.306 4.493 4.493 0 004.306-1.758M16.5 9a1.5 1.5 0 11-3 0 1.5 1.5 0 013 0z" />
      </svg>
    ),
    isFinal: true,
  },
]

const STORAGE_KEY = 'shadow_onboarding_complete'

const OnboardingWalkthrough = memo(function OnboardingWalkthrough({ userName }) {
  const [currentStep, setCurrentStep] = useState(0)
  const [isVisible, setIsVisible] = useState(false)
  const [direction, setDirection] = useState(1) // 1 = forward, -1 = backward
  const [isTransitioning, setIsTransitioning] = useState(false)
  const navigate = useNavigate()

  useEffect(() => {
    const done = localStorage.getItem(STORAGE_KEY)
    if (!done) setIsVisible(true)
  }, [])

  const close = useCallback(() => {
    setIsVisible(false)
    localStorage.setItem(STORAGE_KEY, 'true')
  }, [])

  const goTo = useCallback((idx) => {
    if (isTransitioning || idx === currentStep) return
    setIsTransitioning(true)
    setDirection(idx > currentStep ? 1 : -1)
    setTimeout(() => {
      setCurrentStep(idx)
      setIsTransitioning(false)
    }, 250)
  }, [currentStep, isTransitioning])

  const next = useCallback(() => {
    if (currentStep < STEPS.length - 1) goTo(currentStep + 1)
  }, [currentStep, goTo])

  const prev = useCallback(() => {
    if (currentStep > 0) goTo(currentStep - 1)
  }, [currentStep, goTo])

  const finish = useCallback(() => {
    close()
    navigate('/courses')
  }, [close, navigate])

  // Keyboard navigation
  useEffect(() => {
    const handleKey = (e) => {
      if (!isVisible) return
      if (e.key === 'ArrowRight' || e.key === ' ') { e.preventDefault(); next() }
      if (e.key === 'ArrowLeft') { e.preventDefault(); prev() }
      if (e.key === 'Escape') close()
    }
    window.addEventListener('keydown', handleKey)
    return () => window.removeEventListener('keydown', handleKey)
  }, [isVisible, next, prev, close])

  if (!isVisible) return null

  const step = STEPS[currentStep]
  const progress = ((currentStep + 1) / STEPS.length) * 100
  const firstName = userName?.split(' ')[0] || 'there'

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-navy-950/95 backdrop-blur-xl" />

      {/* Animated grid background */}
      <div className="absolute inset-0 opacity-[0.04]" style={{
        backgroundImage: 'linear-gradient(rgba(255,255,255,0.15) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.15) 1px, transparent 1px)',
        backgroundSize: '60px 60px',
      }} />

      {/* Floating accent orb */}
      <div
        className={`absolute w-[500px] h-[500px] rounded-full blur-[150px] transition-all duration-700 ease-out ${step.orb}`}
        style={{
          top: '20%',
          left: currentStep % 2 === 0 ? '10%' : '50%',
          transition: 'left 0.7s cubic-bezier(0.4, 0, 0.2, 1), background-color 0.7s',
        }}
      />

      {/* Content */}
      <div className="relative z-10 w-full max-w-lg mx-auto px-6">

        {/* Skip button */}
        <button
          onClick={close}
          className="absolute -top-16 right-0 text-[12px] font-semibold text-white/30 hover:text-white/60 transition-colors tracking-wider uppercase"
        >
          Skip tour
        </button>

        {/* Step number watermark */}
        <div className="absolute -top-8 -left-4 sm:-left-8 select-none pointer-events-none">
          <span
            className="font-display text-[5rem] sm:text-[7rem] md:text-[9rem] font-bold leading-none tracking-tighter"
            style={{
              background: `linear-gradient(135deg, rgba(255,255,255,0.06), rgba(255,255,255,0.02))`,
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
            }}
          >
            {step.number}
          </span>
        </div>

        {/* Card */}
        <div
          className={`relative transition-all duration-300 ease-out ${
            isTransitioning
              ? `opacity-0 ${direction > 0 ? 'translate-x-8' : '-translate-x-8'}`
              : 'opacity-100 translate-x-0'
          }`}
        >
          {/* Icon */}
          <div className={`w-16 h-16 sm:w-20 sm:h-20 rounded-2xl bg-gradient-to-br ${step.accent} p-4 sm:p-5 mb-8 shadow-lg`}>
            <div className="text-white/90">
              {step.icon}
            </div>
          </div>

          {/* Title */}
          <h1 className="font-display text-[2rem] sm:text-[2.5rem] font-bold text-white leading-[1.1] tracking-tight mb-2">
            {currentStep === 0 ? (
              <>Welcome, <span className="text-emerald-400">{firstName}</span></>
            ) : (
              step.title
            )}
          </h1>

          {/* Subtitle */}
          <p className="text-[15px] sm:text-[17px] font-semibold text-white/40 mb-5 tracking-wide">
            {step.subtitle}
          </p>

          {/* Description */}
          <p className="text-[14px] sm:text-[15px] text-white/50 leading-relaxed max-w-md mb-10">
            {step.description}
          </p>

          {/* Actions */}
          <div className="flex items-center gap-4">
            {step.isFinal ? (
              <button
                onClick={finish}
                className="group relative px-7 py-3.5 bg-white text-navy-900 font-display text-[14px] font-bold rounded-xl transition-all hover:shadow-xl hover:shadow-white/10 hover:scale-[1.02] active:scale-[0.98]"
              >
                <span className="relative z-10">Enroll in courses</span>
                <div className="absolute inset-0 rounded-xl bg-gradient-to-r from-emerald-100 to-white opacity-0 group-hover:opacity-100 transition-opacity" />
              </button>
            ) : (
              <button
                onClick={next}
                className="group px-6 py-3 bg-white/[0.08] hover:bg-white/[0.14] border border-white/[0.08] hover:border-white/[0.15] text-white font-display text-[13px] font-semibold rounded-xl transition-all"
              >
                Continue
                <svg className="inline-block w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
                </svg>
              </button>
            )}

            {currentStep > 0 && (
              <button
                onClick={prev}
                className="text-[12px] font-semibold text-white/30 hover:text-white/60 transition-colors"
              >
                Back
              </button>
            )}
          </div>
        </div>

        {/* Progress bar + dots */}
        <div className="mt-12">
          {/* Progress bar */}
          <div className="h-[2px] bg-white/[0.06] rounded-full mb-4 overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-white/40 to-white/20 rounded-full transition-all duration-500 ease-out"
              style={{ width: `${progress}%` }}
            />
          </div>

          {/* Dots */}
          <div className="flex items-center justify-center gap-2">
            {STEPS.map((_, idx) => (
              <button
                key={idx}
                onClick={() => goTo(idx)}
                className={`transition-all duration-300 rounded-full ${
                  idx === currentStep
                    ? 'w-6 h-2 bg-white/60'
                    : idx < currentStep
                      ? 'w-2 h-2 bg-white/30 hover:bg-white/50'
                      : 'w-2 h-2 bg-white/10 hover:bg-white/20'
                }`}
                aria-label={`Step ${idx + 1}`}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  )
})

export default OnboardingWalkthrough
