import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { getStudyPlans, updateStudyPlanProgress, generateQuizFromPlan, createStudyPlanFromQuizGaps } from '../services/api'
import StudyPlanForm from '../components/studyplan/StudyPlanForm'
import StudyPlanDetails from '../components/studyplan/StudyPlanDetails'
import SmartStudyChat from '../components/SmartStudyChat'
import SmartRecommendations from '../components/SmartRecommendations'
import EffectivenessAnalytics from '../components/EffectivenessAnalytics'
import NotificationBell from '../components/NotificationBell'
import YouTubePlayer from '../components/YouTubePlayer'
import QuizForm from '../components/quiz/QuizForm'
import QuizPlayer from '../components/quiz/QuizPlayer'
import QuizResults from '../components/quiz/QuizResults'
import GeneratingOverlay from '../components/GeneratingOverlay'

/* ─── SVG Icons ─── */
const SparkleIcon = ({ className }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8">
    <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z" />
  </svg>
)
const BookIcon = ({ className }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8">
    <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 016-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0018 18a8.967 8.967 0 00-6 2.292m0-14.25v14.25" />
  </svg>
)
const ChartIcon = ({ className }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8">
    <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
  </svg>
)
const LightbulbIcon = ({ className }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8">
    <path strokeLinecap="round" strokeLinejoin="round" d="M12 18v-5.25m0 0a6.01 6.01 0 001.5-.189m-1.5.189a6.01 6.01 0 01-1.5-.189m3.75 7.478a12.06 12.06 0 01-4.5 0m3.75 2.383a14.406 14.406 0 01-3 0M14.25 18v-.192c0-.983.658-1.823 1.508-2.316a7.5 7.5 0 10-7.517 0c.85.493 1.509 1.333 1.509 2.316V18" />
  </svg>
)
const CheckCircleIcon = ({ className }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8">
    <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
)
const ClipboardIcon = ({ className }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8">
    <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h3.75M9 15h3.75M9 18h3.75m3 .75H18a2.25 2.25 0 002.25-2.25V6.108c0-1.135-.845-2.098-1.976-2.192a48.424 48.424 0 00-1.123-.08m-5.801 0c-.065.21-.1.433-.1.664 0 .414.336.75.75.75h4.5a.75.75 0 00.75-.75 2.25 2.25 0 00-.1-.664m-5.8 0A2.251 2.251 0 0113.5 2.25H15c1.012 0 1.867.668 2.15 1.586m-5.8 0c-.376.023-.75.05-1.124.08C9.095 4.01 8.25 4.973 8.25 6.108V8.25m0 0H4.875c-.621 0-1.125.504-1.125 1.125v11.25c0 .621.504 1.125 1.125 1.125h9.75c.621 0 1.125-.504 1.125-1.125V9.375c0-.621-.504-1.125-1.125-1.125H8.25z" />
  </svg>
)

/* ═══════════════════════════════════════
   SmartStudy Page — AI Learning Hub
   ═══════════════════════════════════════ */
export default function SmartStudyPage() {
  const navigate = useNavigate()
  const { user, logout } = useAuth()

  /* ─── Study plans state ─── */
  const [plans, setPlans] = useState([])
  const [currentPlan, setCurrentPlan] = useState(null)
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [showGenerateForm, setShowGenerateForm] = useState(false)

  /* ─── Modal states ─── */
  const [showChat, setShowChat] = useState(false)
  const [showInsights, setShowInsights] = useState(false)
  const [showAnalytics, setShowAnalytics] = useState(false)
  const [playingVideo, setPlayingVideo] = useState(null)
  const [menuOpen, setMenuOpen] = useState(false)

  /* ─── Quiz states ─── */
  const [quizPhase, setQuizPhase] = useState(null) // null | 'form' | 'playing' | 'results'
  const [activeQuiz, setActiveQuiz] = useState(null)
  const [quizAttempt, setQuizAttempt] = useState(null)
  const [quizPlanContext, setQuizPlanContext] = useState(null) // { studyPlanId, topic }

  /* ─── Generating step state ─── */
  const [generatingStep, setGeneratingStep] = useState(0)

  /* ─── Error + retry state ─── */
  const [loadError, setLoadError] = useState(null)

  /* ─── Mobile sidebar toggle ─── */
  const [sidebarOpen, setSidebarOpen] = useState(false)

  /* ─── Data loading ─── */
  useEffect(() => { loadStudyPlans() }, [])

  /* ─── Generating step cycle ─── */
  useEffect(() => {
    if (!generating || showGenerateForm) return
    setGeneratingStep(0)
    const interval = setInterval(() => {
      setGeneratingStep(prev => (prev + 1) % 3)
    }, 2500)
    return () => clearInterval(interval)
  }, [generating, showGenerateForm])

  const loadStudyPlans = async () => {
    try {
      setLoading(true)
      setLoadError(null)
      const data = await getStudyPlans(false)
      setPlans(data)
      const active = data.find(p => p.is_active)
      if (active) setCurrentPlan(active)
      else if (data.length > 0) setCurrentPlan(data[0])
    } catch (err) {
      console.error('Error loading study plans:', err)
      setLoadError('Failed to load study plans. Check your connection and try again.')
    } finally {
      setLoading(false)
    }
  }

  const handlePlanGenerated = async () => {
    await loadStudyPlans()
    setShowGenerateForm(false)
  }

  const handleBeforeScore = async (score) => {
    if (!currentPlan) return
    try {
      await updateStudyPlanProgress(currentPlan.id, { beforeScore: score })
      setCurrentPlan({ ...currentPlan, before_score: score })
    } catch (err) { console.error('Error saving before score:', err) }
  }

  const handleAfterScore = async (score) => {
    if (!currentPlan) return
    try {
      await updateStudyPlanProgress(currentPlan.id, { afterScore: score })
      setCurrentPlan({
        ...currentPlan,
        after_score: score,
        effectiveness_score: currentPlan.before_score != null ? score - currentPlan.before_score : null,
      })
    } catch (err) { console.error('Error saving after score:', err) }
  }

  const handleDayComplete = async (dayNumber) => {
    if (!currentPlan) return
    try {
      const totalDays = currentPlan.plan_data?.days?.length || 1
      const completed = currentPlan.completed_days || []
      const next = completed.includes(dayNumber)
        ? completed.filter(d => d !== dayNumber)
        : [...completed, dayNumber]
      const pct = (next.length / totalDays) * 100
      await updateStudyPlanProgress(currentPlan.id, { completionPercentage: pct, isActive: pct < 100, completedDays: next })
      setCurrentPlan({ ...currentPlan, completed_days: next, completion_percentage: pct, is_active: pct < 100 })
    } catch (err) { console.error('Error updating progress:', err) }
  }

  /* ─── Derived stats ─── */
  const activePlans = plans.filter(p => p.is_active).length
  const completedPlans = plans.filter(p => (p.completion_percentage || 0) >= 100).length
  const avgCompletion = plans.length > 0
    ? Math.round(plans.reduce((s, p) => s + (p.completion_percentage || 0), 0) / plans.length)
    : 0

  return (
    <div className="min-h-screen bg-surface-50">

      {/* ══════════ NAV ══════════ */}
      <nav className="sticky top-0 z-40 border-b border-surface-200/80 bg-white/80 backdrop-blur-xl">
        <div className="mx-auto flex h-14 max-w-[1360px] items-center justify-between px-5">
          <div className="flex items-center gap-6">
            <button onClick={() => navigate('/dashboard')} className="flex items-center gap-2 group">
              <div className="w-7 h-7 rounded-lg bg-navy-800 flex items-center justify-center">
                <span className="text-white font-display text-sm font-bold">S</span>
              </div>
              <span className="text-[15px] font-bold text-navy-900 group-hover:text-navy-700 transition-colors">Shadow</span>
            </button>
            <div className="hidden md:flex items-center gap-1">
              {[
                { label: 'Dashboard', path: '/dashboard' },
                { label: 'Courses', path: '/courses' },
                { label: 'CGPA', path: '/cgpa' },
                { label: 'Library', path: '/library' },
                { label: 'SmartStudy', path: '/smartstudy', active: true },
              ].map(link => (
                <button
                  key={link.path}
                  onClick={() => navigate(link.path)}
                  className={`px-3 py-1.5 rounded-lg text-[13px] font-medium transition-colors ${
                    link.active
                      ? 'bg-navy-800/[0.06] text-navy-800'
                      : 'text-surface-400 hover:text-navy-800 hover:bg-surface-100'
                  }`}
                >{link.label}</button>
              ))}
            </div>
          </div>

          <div className="flex items-center gap-2">
            <NotificationBell />
            <div className="hidden md:flex items-center gap-2">
              <div className="w-7 h-7 rounded-full bg-navy-100 flex items-center justify-center">
                <span className="text-[11px] font-bold text-navy-800">
                  {(user?.full_name || 'U').split(' ').map(n => n[0]).join('').slice(0, 2)}
                </span>
              </div>
              <span className="text-[13px] font-medium text-surface-400">{user?.full_name?.split(' ')[0] || 'User'}</span>
            </div>
            <button onClick={() => logout()} className="text-[12px] font-medium text-surface-400 hover:text-red-500 transition-colors hidden md:block">
              Sign out
            </button>
            <button onClick={() => setMenuOpen(!menuOpen)} className="md:hidden p-1.5 rounded-lg hover:bg-surface-100">
              <svg className="w-5 h-5 text-surface-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                {menuOpen
                  ? <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                  : <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h16" />}
              </svg>
            </button>
          </div>
        </div>

        {menuOpen && (
          <div className="md:hidden border-t border-surface-200 bg-white animate-fade-in">
            <div className="px-4 py-3 space-y-1">
              {[
                { label: 'Dashboard', path: '/dashboard' },
                { label: 'Courses', path: '/courses' },
                { label: 'CGPA', path: '/cgpa' },
                { label: 'Library', path: '/library' },
                { label: 'SmartStudy', path: '/smartstudy' },
              ].map(item => (
                <button key={item.label} onClick={() => { navigate(item.path); setMenuOpen(false) }}
                  className="block w-full text-left px-3 py-2 rounded-lg text-[14px] font-medium text-surface-400 hover:bg-surface-100"
                >{item.label}</button>
              ))}
              <div className="border-t border-surface-200 pt-2 mt-2">
                <button onClick={() => logout()} className="block w-full text-left px-3 py-2 rounded-lg text-[14px] font-medium text-red-500 hover:bg-red-50">
                  Sign out
                </button>
              </div>
            </div>
          </div>
        )}
      </nav>

      {/* ══════════ MAIN ══════════ */}
      <main className="mx-auto max-w-[1360px] px-5 py-6">

        {/* ─── Hero ─── */}
        <section className="mb-6 animate-fade-up hero-atmosphere rounded-2xl px-6 py-5 -mx-1">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-5 relative z-10">
            <div>
              <div className="flex items-center gap-3 mb-1">
                <h1 className="font-display text-[1.75rem] font-bold text-navy-900 leading-tight">SmartStudy</h1>
                <span className="px-2 py-0.5 rounded-md text-[10px] font-bold uppercase tracking-wider bg-navy-800/[0.07] text-navy-600">AI</span>
              </div>
              <p className="text-[13px] text-surface-400 mt-0.5">Your personal learning hub — study plans, coaching & analytics</p>
            </div>
            <button
              onClick={() => { setShowGenerateForm(true); setCurrentPlan(null) }}
              className="btn-glow flex items-center gap-2 bg-gradient-to-r from-navy-800 to-navy-900 hover:from-navy-900 hover:to-navy-950 text-white px-5 py-2.5 rounded-xl text-[13px] font-semibold transition-all shadow-sm self-start"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
              </svg>
              New Study Plan
            </button>
          </div>

          {/* Quick-launch cards */}
          <div className="grid grid-cols-1 sm:grid-cols-4 gap-3 mb-5 animate-fade-up-1">
            {[
              {
                icon: <SparkleIcon className="w-5 h-5" />,
                title: 'AI Coach',
                desc: 'Chat with your study assistant',
                bg: 'bg-navy-800/[0.06]',
                fg: 'text-navy-700',
                accent: 'bg-navy-800',
                action: () => setShowChat(true),
              },
              {
                icon: <ClipboardIcon className="w-5 h-5" />,
                title: 'Quiz',
                desc: 'Test your knowledge',
                bg: 'bg-violet-500/[0.06]',
                fg: 'text-violet-600',
                accent: 'bg-violet-500',
                action: () => { setQuizPlanContext(null); setQuizPhase('form') },
              },
              {
                icon: <LightbulbIcon className="w-5 h-5" />,
                title: 'Insights',
                desc: 'Personalized recommendations',
                bg: 'bg-emerald-500/[0.06]',
                fg: 'text-emerald-600',
                accent: 'bg-emerald-500',
                action: () => setShowInsights(true),
              },
              {
                icon: <ChartIcon className="w-5 h-5" />,
                title: 'Analytics',
                desc: 'Track learning effectiveness',
                bg: 'bg-amber-500/[0.06]',
                fg: 'text-amber-600',
                accent: 'bg-amber-500',
                action: () => setShowAnalytics(true),
              },
            ].map(card => (
              <button
                key={card.title}
                onClick={card.action}
                className="group flex items-center gap-4 p-4 rounded-2xl border border-surface-200/80 bg-white
                  hover:shadow-md transition-all duration-300 text-left relative overflow-hidden"
              >
                {/* Top accent line */}
                <div className={`absolute top-0 left-0 right-0 h-[2px] ${card.accent} opacity-0 group-hover:opacity-100 transition-opacity duration-300`} />

                <div className={`w-12 h-12 rounded-xl ${card.bg} flex items-center justify-center transition-all duration-300 group-hover:animate-gentle-float`}>
                  <span className={`${card.fg} transition-colors duration-300`}>{card.icon}</span>
                </div>
                <div className="flex-1">
                  <p className="text-[13px] font-semibold text-navy-900">{card.title}</p>
                  <p className="text-[11px] text-surface-500">{card.desc}</p>
                </div>
                {/* Hover arrow */}
                <svg className="w-4 h-4 text-surface-300 opacity-0 group-hover:opacity-100 group-hover:translate-x-0 -translate-x-1 transition-all duration-200" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
                </svg>
              </button>
            ))}
          </div>

          {/* Stats strip */}
          <div className="flex items-center gap-3 flex-wrap">
            {[
              { icon: <BookIcon className="w-3.5 h-3.5" />, label: 'plans', value: plans.length, color: 'text-navy-800' },
              { icon: <span className="w-2 h-2 rounded-full bg-emerald-400" />, label: 'active', value: activePlans, color: 'text-emerald-600' },
              { icon: <CheckCircleIcon className="w-3.5 h-3.5" />, label: 'completed', value: completedPlans, color: 'text-navy-800' },
              { icon: null, label: 'avg done', value: `${avgCompletion}%`, color: 'text-navy-800', hideMobile: true },
            ].map((stat, i) => (
              <div key={i} className={`items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/80 border border-surface-200/60 ${stat.hideMobile ? 'hidden sm:flex' : 'flex'}`}>
                {stat.icon}
                <span className="text-[12px] text-surface-400">
                  <span className={`font-semibold ${stat.color}`}>{stat.value}</span> {stat.label}
                </span>
              </div>
            ))}
          </div>
        </section>

        {/* ─── Generate Form ─── */}
        {showGenerateForm && (
          <section className="mb-6 animate-fade-up">
            <div className="rounded-2xl border border-surface-200/80 bg-white overflow-hidden">
              <div className="px-5 py-3.5 border-b border-surface-100 flex items-center justify-between">
                <h3 className="text-[14px] font-bold text-navy-900">Create a New Study Plan</h3>
                <button onClick={() => setShowGenerateForm(false)} className="p-1 rounded-lg text-surface-300 hover:text-surface-400 hover:bg-surface-100 transition-all">
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              <StudyPlanForm
                generating={generating}
                setGenerating={setGenerating}
                onPlanGenerated={handlePlanGenerated}
                onCancel={() => setShowGenerateForm(false)}
              />
            </div>
          </section>
        )}

        {/* ─── Main: Sidebar + Content ─── */}
        <section className="flex flex-col lg:flex-row gap-5 animate-fade-up-2">

          {/* Sidebar: Plan List */}
          <div className="w-full lg:w-80 flex-shrink-0">
            <div className="lg:sticky lg:top-20 rounded-2xl border border-surface-200/80 bg-white overflow-hidden">
              <button
                onClick={() => setSidebarOpen(prev => !prev)}
                className="w-full px-4 py-3.5 border-b border-surface-100 flex items-center justify-between lg:cursor-default"
              >
                <h3 className="text-[13px] font-bold text-navy-900">Your Plans</h3>
                <div className="flex items-center gap-2">
                  <span className="text-[11px] font-semibold text-surface-400">{plans.length}</span>
                  <svg className={`w-4 h-4 text-surface-300 lg:hidden transition-transform ${sidebarOpen ? 'rotate-180' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
                  </svg>
                </div>
              </button>
              <div className={`${sidebarOpen ? 'block' : 'hidden'} lg:block`}>

              {loading ? (
                <div className="p-3 space-y-2">
                  {[1, 2, 3].map(i => (
                    <div key={i} className="rounded-xl overflow-hidden p-3.5" >
                      <div className="h-4 w-3/4 rounded-md skeleton-shimmer mb-2.5" />
                      <div className="h-1.5 rounded-full skeleton-shimmer mb-2.5" />
                      <div className="flex justify-between">
                        <div className="h-3 w-12 rounded-md skeleton-shimmer" />
                        <div className="h-3 w-8 rounded-md skeleton-shimmer" />
                      </div>
                    </div>
                  ))}
                </div>
              ) : loadError ? (
                <div className="p-5 text-center">
                  <div className="w-12 h-12 rounded-xl bg-red-50 flex items-center justify-center mx-auto mb-3">
                    <svg className="w-6 h-6 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
                    </svg>
                  </div>
                  <p className="text-[13px] font-medium text-navy-900 mb-1">Connection Error</p>
                  <p className="text-[11px] text-surface-400 mb-4">{loadError}</p>
                  <button
                    onClick={loadStudyPlans}
                    className="inline-flex items-center gap-1.5 text-[12px] font-semibold text-navy-600 hover:text-navy-800 bg-navy-50 hover:bg-navy-100 px-3 py-1.5 rounded-lg transition-colors"
                  >
                    <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182" />
                    </svg>
                    Retry
                  </button>
                </div>
              ) : plans.length === 0 ? (
                <div className="p-8 text-center relative overflow-hidden">
                  {/* Decorative background orbs */}
                  <div className="absolute top-4 right-8 w-24 h-24 rounded-full bg-navy-100/30 blur-2xl" />
                  <div className="absolute bottom-4 left-6 w-20 h-20 rounded-full bg-amber-100/30 blur-2xl" />

                  <div className="relative z-10">
                    <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-navy-50 to-surface-100 border border-surface-200/60 flex items-center justify-center mx-auto mb-4 animate-gentle-float">
                      <BookIcon className="w-7 h-7 text-navy-300" />
                    </div>
                    <p className="text-[14px] font-semibold text-navy-900 mb-1">No study plans yet</p>
                    <p className="text-[12px] text-surface-400 mb-5 max-w-[200px] mx-auto leading-relaxed">Create your first AI-powered study plan to get started</p>
                    <button
                      onClick={() => setShowGenerateForm(true)}
                      className="inline-flex items-center gap-1.5 text-[12px] font-semibold text-white bg-navy-800 hover:bg-navy-900 px-4 py-2 rounded-lg transition-all shadow-sm"
                    >
                      <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
                      </svg>
                      Create Plan
                    </button>
                  </div>
                </div>
              ) : (
                <div className="p-2 space-y-1 max-h-[calc(100vh-280px)] overflow-y-auto">
                  {plans.map(plan => {
                    const isActive = currentPlan?.id === plan.id && !showGenerateForm
                    return (
                      <button
                        key={plan.id}
                        onClick={() => { setCurrentPlan(plan); setShowGenerateForm(false); setSidebarOpen(false) }}
                        className={`w-full text-left p-3.5 rounded-xl transition-all ${
                          isActive
                            ? 'bg-navy-800 text-white shadow-md border-l-[3px] border-l-white/60'
                            : 'bg-white hover:bg-surface-50 text-navy-900 border-l-[3px] border-l-transparent hover:border-l-navy-200'
                        }`}
                      >
                        <div className="flex items-start justify-between gap-2 mb-2">
                          <h4 className="text-[13px] font-semibold line-clamp-2 leading-snug flex-1">{plan.topic}</h4>
                          {plan.is_active && (
                            <span className={`flex-shrink-0 px-1.5 py-0.5 text-[10px] font-semibold rounded-md ${
                              isActive ? 'bg-white/20 text-white' : 'bg-emerald-50 text-emerald-600'
                            }`}>Active</span>
                          )}
                        </div>

                        <div className="mb-2">
                          <div className={`h-1.5 rounded-full overflow-hidden ${
                            isActive ? 'bg-white/20' : 'bg-surface-100'
                          }`}>
                            <div
                              className={`h-full rounded-full transition-all duration-500 ${
                                isActive ? 'bg-white' : 'bg-navy-600'
                              }`}
                              style={{ width: `${plan.completion_percentage || 0}%` }}
                            />
                          </div>
                        </div>

                        <div className={`flex items-center justify-between text-[11px] ${
                          isActive ? 'text-white/50' : 'text-surface-400'
                        }`}>
                          <span>{plan.duration_days} days</span>
                          <span>{Math.round(plan.completion_percentage || 0)}%</span>
                        </div>
                      </button>
                    )
                  })}
                </div>
              )}
              </div>
            </div>
          </div>

          {/* Content: Plan Details */}
          <div className="flex-1 min-w-0">
            {currentPlan && !showGenerateForm ? (
              <div className="rounded-2xl border border-surface-200/80 bg-white overflow-hidden">
                <div className="p-6 lg:p-8">
                  <StudyPlanDetails
                    plan={currentPlan}
                    onDayComplete={handleDayComplete}
                    onPlayVideo={setPlayingVideo}
                    onSubmitBeforeScore={handleBeforeScore}
                    onSubmitAfterScore={handleAfterScore}
                    onTakeQuiz={(plan) => {
                      setQuizPlanContext({ studyPlanId: plan.id, topic: plan.topic })
                      setQuizPhase('form')
                    }}
                  />
                </div>
              </div>
            ) : !showGenerateForm ? (
              <div className="rounded-2xl border border-surface-200/80 bg-white overflow-hidden relative">
                {/* Atmospheric decoration */}
                <div className="absolute top-12 right-16 w-40 h-40 rounded-full bg-navy-100/20 blur-3xl" />
                <div className="absolute bottom-8 left-12 w-32 h-32 rounded-full bg-amber-100/20 blur-3xl" />
                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-60 h-60 rounded-full bg-violet-50/20 blur-3xl" />

                <div className="py-24 text-center relative z-10">
                  {/* Stacked books illustration */}
                  <div className="relative w-20 h-20 mx-auto mb-6">
                    <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-16 h-3 rounded-full bg-surface-200/60" />
                    <div className="absolute bottom-2 left-1/2 -translate-x-[55%] w-12 h-8 rounded-lg bg-navy-100 border border-navy-200/40 rotate-[-6deg]" />
                    <div className="absolute bottom-4 left-1/2 -translate-x-[45%] w-12 h-8 rounded-lg bg-emerald-50 border border-emerald-200/40 rotate-[3deg]" />
                    <div className="absolute bottom-7 left-1/2 -translate-x-1/2 w-14 h-10 rounded-lg bg-white border border-surface-200 shadow-sm flex items-center justify-center animate-gentle-float">
                      <SparkleIcon className="w-5 h-5 text-navy-400" />
                    </div>
                  </div>

                  <h3 className="text-[17px] font-display font-bold text-navy-900 mb-2">Select a study plan</h3>
                  <p className="text-[13px] text-surface-400 max-w-[280px] mx-auto mb-6 leading-relaxed">
                    Choose a plan from the sidebar or create a new one to begin your learning journey
                  </p>
                  <button
                    onClick={() => setShowGenerateForm(true)}
                    className="btn-glow inline-flex items-center gap-2 bg-gradient-to-r from-navy-800 to-navy-900 hover:from-navy-900 hover:to-navy-950 text-white px-5 py-2.5 rounded-xl text-[13px] font-semibold transition-all shadow-sm"
                  >
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
                    </svg>
                    New Study Plan
                  </button>
                </div>
              </div>
            ) : null}
          </div>
        </section>
      </main>

      {/* ══════════ MODALS ══════════ */}
      {showChat && <SmartStudyChat onClose={() => setShowChat(false)} />}
      {showInsights && <SmartRecommendations onClose={() => setShowInsights(false)} user={user} />}
      {showAnalytics && <EffectivenessAnalytics onClose={() => setShowAnalytics(false)} />}

      {/* ── Quiz Modal Flow ── */}
      {quizPhase && (
        <div className="fixed inset-0 z-50 bg-navy-950/40 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-3xl max-h-[90vh] overflow-y-auto">
            {quizPhase === 'form' && (
              <QuizForm
                studyPlanId={quizPlanContext?.studyPlanId}
                studyPlanTopic={quizPlanContext?.topic}
                onQuizGenerated={(quiz) => { setActiveQuiz(quiz); setQuizPhase('playing') }}
                onCancel={() => setQuizPhase(null)}
              />
            )}
            {quizPhase === 'playing' && activeQuiz && (
              <QuizPlayer
                quiz={activeQuiz}
                onComplete={(attempt) => {
                  setQuizAttempt(attempt)
                  if (activeQuiz?.remaining_attempts != null) {
                    setActiveQuiz(prev => ({ ...prev, remaining_attempts: Math.max(0, prev.remaining_attempts - 1) }))
                  }
                  setQuizPhase('results')
                }}
                onCancel={() => setQuizPhase(null)}
              />
            )}
            {quizPhase === 'results' && quizAttempt && (
              <QuizResults
                attempt={quizAttempt}
                quiz={activeQuiz}
                onRetake={() => setQuizPhase('playing')}
                onCreateStudyPlan={async (weakTopic) => {
                  if (!activeQuiz?.id) return
                  try {
                    setQuizPhase(null)
                    setGenerating(true)
                    setShowGenerateForm(false)
                    const result = await createStudyPlanFromQuizGaps(activeQuiz.id)
                    if (result && !result.error) {
                      const freshPlans = await getStudyPlans(false)
                      setPlans(freshPlans)
                      const newPlan = freshPlans.find(p =>
                        p.id === (result.study_plan_id || result.id)
                      )
                      if (newPlan) setCurrentPlan(newPlan)
                      else if (freshPlans.length > 0) setCurrentPlan(freshPlans[0])
                    }
                  } catch (err) {
                    console.error('Failed to create study plan from quiz gaps:', err)
                    setLoadError('Failed to generate study plan from quiz gaps. Please try again.')
                    setGenerating(false)
                  } finally {
                    setGenerating(false)
                    setActiveQuiz(null)
                    setQuizAttempt(null)
                    setQuizPlanContext(null)
                  }
                }}
                onClose={() => { setQuizPhase(null); setActiveQuiz(null); setQuizAttempt(null) }}
              />
            )}
          </div>
        </div>
      )}
      {/* ── Generating Overlay (quiz→plan flow or background generation) ── */}
      {generating && !showGenerateForm && <GeneratingOverlay generatingStep={generatingStep} />}
      {playingVideo && (
        <YouTubePlayer
          videoUrl={playingVideo.url}
          title={playingVideo.title}
          onClose={() => setPlayingVideo(null)}
          autoplay={true}
        />
      )}
    </div>
  )
}
