import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { getEnrolledCourses, getTasks, getTaskStats, updateEnrollment, resendVerification } from '../services/api'
import { useAuth } from '../contexts/AuthContext'
import TaskList from '../components/TaskList'
import AddTaskModal from '../components/AddTaskModal'
import PriorityRecommendationsCompact from '../components/PriorityRecommendationsCompact'
import MoodLogger from '../components/MoodLogger'
import CourseCarousel from '../components/CourseCarousel'
import SmartStudyChat from '../components/SmartStudyChat'
import SmartStudyTriggerBanner from '../components/SmartStudyTriggerBanner'
import EditCourseScoresModal from '../components/EditCourseScoresModal'
import NotificationBell from '../components/NotificationBell'
import OnboardingWalkthrough from '../components/OnboardingWalkthrough'

/* ─── helpers ─── */
const greetByTime = () => {
  const h = new Date().getHours()
  if (h < 12) return 'Good morning'
  if (h < 17) return 'Good afternoon'
  return 'Good evening'
}

const classify = (cgpa) => {
  if (cgpa >= 4.50) return { label: 'First Class', cls: 'text-emerald-400' }
  if (cgpa >= 3.50) return { label: 'Second Class Upper', cls: 'text-blue-400' }
  if (cgpa >= 2.40) return { label: 'Second Class Lower', cls: 'text-amber-400' }
  if (cgpa >= 1.50) return { label: 'Third Class', cls: 'text-orange-400' }
  return { label: 'Below Threshold', cls: 'text-red-400' }
}

const heroMessage = (current, target) => {
  if (!target || !current) return { title: 'Set your target', sub: 'Update your profile to track progress' }
  const pct = (current / target) * 100
  if (pct >= 100) return { title: 'Target achieved', sub: 'You\'ve reached your goal — aim higher?' }
  if (pct >= 90) return { title: 'Almost there', sub: `${(target - current).toFixed(2)} points to your target` }
  if (pct >= 75) return { title: 'Strong momentum', sub: `${(target - current).toFixed(2)} points to go — keep it up` }
  if (pct >= 50) return { title: 'Building steady', sub: `Close the ${(target - current).toFixed(2)}-point gap this semester` }
  return { title: 'Every point counts', sub: `${(target - current).toFixed(2)} points to your target — start with your next task` }
}

/* ─── Stat tile ─── */
function StatTile({ label, value, sub, accent = 'navy', delay = 0 }) {
  const colors = {
    navy:    'from-navy-800/5 to-navy-800/[0.02] border-navy-200/60 text-navy-900',
    emerald: 'from-emerald-600/5 to-emerald-600/[0.02] border-emerald-200/60 text-emerald-700',
    amber:   'from-amber-500/5 to-amber-500/[0.02] border-amber-200/60 text-amber-700',
    red:     'from-red-500/5 to-red-500/[0.02] border-red-200/60 text-red-600',
  }
  const cls = colors[accent] || colors.navy
  const anim = `animate-fade-up-${delay}`

  return (
    <div className={`${anim} card-lift rounded-2xl border bg-gradient-to-br ${cls} p-5`}>
      <p className="text-[11px] font-semibold uppercase tracking-wider text-surface-400 mb-1">{label}</p>
      <p className={`font-display text-3xl font-semibold leading-none ${cls.split(' ').pop()}`}>{value}</p>
      {sub && <p className="text-xs text-surface-400 mt-1.5">{sub}</p>}
    </div>
  )
}

/* ─── CGPA Ring (redesigned with dual-track) ─── */
function CGPARing({ current, target, max = 5.0 }) {
  const [offset, setOffset] = useState(314.16)
  const pct = max > 0 ? Math.min((current / max) * 100, 100) : 0
  const targetPct = max > 0 ? Math.min((target / max) * 100, 100) : 0
  const targetOffset = 314.16 - (pct * 314.16 / 100)
  const targetRingOffset = 314.16 - (targetPct * 314.16 / 100)
  const color = pct / targetPct >= 0.9 ? '#10b981' : pct / targetPct >= 0.75 ? '#f59e0b' : '#ef4444'

  useEffect(() => {
    const id = requestAnimationFrame(() => requestAnimationFrame(() => setOffset(targetOffset)))
    return () => cancelAnimationFrame(id)
  }, [targetOffset])

  return (
    <div className="relative w-[160px] h-[160px] flex-shrink-0 hidden sm:block">
      <svg viewBox="0 0 120 120" className="w-full h-full -rotate-90">
        {/* Background track */}
        <circle cx="60" cy="60" r="50" fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="10" />
        {/* Target ghost ring */}
        <circle
          cx="60" cy="60" r="50" fill="none"
          stroke="rgba(255,255,255,0.08)" strokeWidth="10" strokeLinecap="round"
          strokeDasharray="314.16"
          strokeDashoffset={targetRingOffset}
        />
        {/* Current progress */}
        <circle
          cx="60" cy="60" r="50" fill="none"
          stroke={color} strokeWidth="10" strokeLinecap="round"
          strokeDasharray="314.16"
          strokeDashoffset={offset}
          style={{ transition: 'stroke-dashoffset 1.4s cubic-bezier(0.4, 0, 0.2, 1)', filter: `drop-shadow(0 0 6px ${color}40)` }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="font-display text-[2.25rem] font-bold text-white leading-none tracking-tight">{current.toFixed(2)}</span>
        <span className="text-[10px] text-white/30 mt-1 font-medium tracking-wider uppercase">of {max.toFixed(1)}</span>
      </div>
    </div>
  )
}

/* ═══════════════════════════════════════════════
   Dashboard Page
   ═══════════════════════════════════════════════ */
function DashboardPage() {
  const navigate = useNavigate()
  const { user, logout } = useAuth()
  const [enrolledCourses, setEnrolledCourses] = useState([])
  const [tasks, setTasks] = useState([])
  const [taskStats, setTaskStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [showAddTaskModal, setShowAddTaskModal] = useState(false)
  const [menuOpen, setMenuOpen] = useState(false)
  const [showMoodLogger, setShowMoodLogger] = useState(false)
  const [todayMood, setTodayMood] = useState(null)
  const [showSmartStudy, setShowSmartStudy] = useState(false)
  const [editingCourse, setEditingCourse] = useState(null)
  const [showCourseMenu, setShowCourseMenu] = useState(null)
  const [showCommandPalette, setShowCommandPalette] = useState(false)

  const [loadError, setLoadError] = useState(null)
  const [verifyDismissed, setVerifyDismissed] = useState(false)
  const [resending, setResending] = useState(false)
  const [verifyFeedback, setVerifyFeedback] = useState(null)

  useEffect(() => {
    loadAll()
  }, [])

  const loadAll = async () => {
    setLoading(true)
    setLoadError(null)
    try {
      // Parallel API calls — 3 requests at once instead of sequential
      const [courses, taskList, stats] = await Promise.all([
        getEnrolledCourses().catch(() => []),
        getTasks().catch(() => []),
        getTaskStats().catch(() => null),
      ])
      setEnrolledCourses(courses)
      setTasks(taskList)
      setTaskStats(stats)
    } catch (e) {
      console.error('Dashboard load error:', e)
      setLoadError('Failed to load dashboard data. Please refresh.')
    } finally {
      setLoading(false)
    }
  }
  const loadEnrolledCourses = async () => {
    try { setEnrolledCourses(await getEnrolledCourses()) }
    catch (e) { console.error('Error loading courses:', e) }
  }
  const loadTasks = async () => {
    try { setTasks(await getTasks()) } catch (e) { console.error(e) }
  }
  const loadTaskStats = async () => {
    try { setTaskStats(await getTaskStats()) } catch (e) { console.error(e) }
  }
  const handleTaskCreated = () => { loadTasks(); loadTaskStats(); loadEnrolledCourses() }
  const handlePriorityTaskClick = (taskId) => {
    const el = document.getElementById('task-section')
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'start' })
      setTimeout(() => {
        const t = document.querySelector(`[data-task-id="${taskId}"]`)
        if (t) { t.classList.add('ring-2', 'ring-navy-500/50'); setTimeout(() => t.classList.remove('ring-2', 'ring-navy-500/50'), 2000) }
      }, 500)
    }
  }
  const handleLogout = () => logout()
  const handleUpdateCourseScores = async (id, data) => {
    try { await updateEnrollment(id, data); await loadEnrolledCourses(); setEditingCourse(null) }
    catch (e) { console.error(e); throw e }
  }

  const totalCredits = enrolledCourses.reduce((s, e) => s + (Number(e.course?.credits) || 0), 0)
  const averageCA = enrolledCourses.length > 0
    ? enrolledCourses.reduce((s, e) => s + (Number(e.ca_score) || 0), 0) / enrolledCourses.length : 0

  /* ─── Quick-action commands ─── */
  const commands = [
    { icon: '📚', label: 'SmartStudy', action: () => navigate('/smartstudy') },
    { icon: '💭', label: 'Log Mood', action: () => setShowMoodLogger(true) },
  ]

  return (
    <div className="min-h-screen bg-surface-50">

      {/* ══════════ ONBOARDING ══════════ */}
      <OnboardingWalkthrough userName={user?.full_name} />

      {/* ══════════ NAV ══════════ */}
      <nav className="sticky top-0 z-40 border-b border-surface-200/80 bg-white/80 backdrop-blur-xl">
        <div className="mx-auto flex h-14 max-w-[1360px] items-center justify-between px-5">
          {/* Left: brand */}
          <div className="flex items-center gap-6">
            <button onClick={() => navigate('/dashboard')} className="flex items-center gap-2 group">
              <div className="w-7 h-7 rounded-lg bg-navy-800 flex items-center justify-center">
                <span className="text-white font-display text-sm font-bold">S</span>
              </div>
              <span className="text-[15px] font-bold text-navy-900 group-hover:text-navy-700 transition-colors">Shadow</span>
            </button>

            {/* Desktop links */}
            <div className="hidden md:flex items-center gap-1">
              {[
                { label: 'Dashboard', path: '/dashboard', active: true },
                { label: 'Courses', path: '/courses' },
                { label: 'CGPA', path: '/cgpa' },
                { label: 'Library', path: '/library' },
                { label: 'SmartStudy', path: '/smartstudy' },
              ].map(link => (
                <button
                  key={link.path}
                  onClick={() => navigate(link.path)}
                  className={`px-3 py-1.5 rounded-lg text-[13px] font-medium transition-colors ${
                    link.active
                      ? 'bg-navy-800/[0.06] text-navy-800'
                      : 'text-surface-400 hover:text-navy-800 hover:bg-surface-100'
                  }`}
                >
                  {link.label}
                </button>
              ))}
            </div>
          </div>

          {/* Right: actions */}
          <div className="flex items-center gap-2">
            {/* SmartStudy AI — main CTA */}
            <button
              onClick={() => setShowSmartStudy(true)}
              className="hidden sm:flex items-center gap-1.5 bg-navy-800 text-white px-3.5 py-1.5 rounded-lg text-[13px] font-semibold hover:bg-navy-900 transition-colors shadow-sm"
            >
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z" />
              </svg>
              SmartStudy
            </button>

            {/* Quick-actions dropdown */}
            <div className="relative">
              <button
                onClick={() => setShowCommandPalette(!showCommandPalette)}
                className="hidden sm:flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-[13px] font-medium text-surface-400 hover:text-navy-800 hover:bg-surface-100 transition-colors border border-surface-200"
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6A2.25 2.25 0 016 3.75h2.25A2.25 2.25 0 0110.5 6v2.25a2.25 2.25 0 01-2.25 2.25H6a2.25 2.25 0 01-2.25-2.25V6zM3.75 15.75A2.25 2.25 0 016 13.5h2.25a2.25 2.25 0 012.25 2.25V18a2.25 2.25 0 01-2.25 2.25H6A2.25 2.25 0 013.75 18v-2.25zM13.5 6a2.25 2.25 0 012.25-2.25H18A2.25 2.25 0 0120.25 6v2.25A2.25 2.25 0 0118 10.5h-2.25a2.25 2.25 0 01-2.25-2.25V6zM13.5 15.75a2.25 2.25 0 012.25-2.25H18a2.25 2.25 0 012.25 2.25V18A2.25 2.25 0 0118 20.25h-2.25A2.25 2.25 0 0113.5 18v-2.25z" />
                </svg>
                More
              </button>
              {showCommandPalette && (
                <>
                  <div className="fixed inset-0 z-40" onClick={() => setShowCommandPalette(false)} />
                  <div className="absolute right-0 top-full mt-2 w-48 bg-white rounded-xl shadow-xl border border-surface-200 p-1.5 z-50 animate-fade-in">
                    {commands.map(cmd => (
                      <button
                        key={cmd.label}
                        onClick={() => { cmd.action(); setShowCommandPalette(false) }}
                        className="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-[13px] font-medium text-surface-400 hover:text-navy-800 hover:bg-surface-100 transition-colors text-left"
                      >
                        <span className="text-base">{cmd.icon}</span>
                        {cmd.label}
                      </button>
                    ))}
                  </div>
                </>
              )}
            </div>

            <div className="w-px h-5 bg-surface-200 hidden sm:block" />
            <NotificationBell />
            <button
              onClick={() => navigate('/profile')}
              className="hidden md:flex items-center gap-2 px-2 py-1 rounded-lg hover:bg-surface-100 transition-colors group"
              title="View profile"
            >
              <div className="w-7 h-7 rounded-full bg-navy-100 flex items-center justify-center group-hover:bg-navy-200 transition-colors">
                <span className="text-[11px] font-bold text-navy-800">
                  {(user?.full_name || 'U').split(' ').map(n => n[0]).join('').slice(0, 2)}
                </span>
              </div>
              <span className="text-[13px] font-medium text-surface-400 group-hover:text-navy-800 transition-colors">{user?.full_name?.split(' ')[0] || 'User'}</span>
            </button>

            {/* Mobile burger */}
            <button onClick={() => setMenuOpen(!menuOpen)} aria-label="Toggle navigation menu" aria-expanded={menuOpen} className="md:hidden p-1.5 rounded-lg hover:bg-surface-100">
              <svg className="w-5 h-5 text-surface-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                {menuOpen
                  ? <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                  : <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h16" />}
              </svg>
            </button>
          </div>
        </div>

        {/* Mobile menu */}
        {menuOpen && (
          <div className="md:hidden border-t border-surface-200 bg-white animate-fade-in">
            <div className="px-4 py-3 space-y-1">
              {[
                { label: 'Dashboard', action: () => navigate('/dashboard') },
                { label: 'Courses', action: () => navigate('/courses') },
                { label: 'CGPA', action: () => navigate('/cgpa') },
                { label: 'Library', action: () => navigate('/library') },
                { label: 'SmartStudy', action: () => navigate('/smartstudy') },
              ].map(item => (
                <button
                  key={item.label}
                  onClick={() => { item.action(); setMenuOpen(false) }}
                  className="block w-full text-left px-3 py-2 rounded-lg text-[14px] font-medium text-surface-400 hover:bg-surface-100"
                >
                  {item.label}
                </button>
              ))}
              <div className="border-t border-surface-200 pt-2 mt-2 space-y-1">
                <button
                  onClick={() => { setShowSmartStudy(true); setMenuOpen(false) }}
                  className="block w-full text-left px-3 py-2 rounded-lg text-[14px] font-semibold bg-navy-800 text-white"
                >
                  SmartStudy AI
                </button>
                {commands.map(cmd => (
                  <button
                    key={cmd.label}
                    onClick={() => { cmd.action(); setMenuOpen(false) }}
                    className="block w-full text-left px-3 py-2 rounded-lg text-[14px] font-medium text-surface-400 hover:bg-surface-100"
                  >
                    {cmd.icon} {cmd.label}
                  </button>
                ))}
              </div>
              <div className="border-t border-surface-200 pt-2 mt-2">
                <p className="px-3 py-1 text-[12px] text-surface-400">{user?.full_name}</p>
                <button onClick={() => { navigate('/profile'); setMenuOpen(false) }} className="block w-full text-left px-3 py-2 rounded-lg text-[14px] font-medium text-surface-400 hover:bg-surface-100">
                  Profile & Settings
                </button>
                <button onClick={handleLogout} className="block w-full text-left px-3 py-2 rounded-lg text-[14px] font-medium text-red-500 hover:bg-red-50">
                  Sign out
                </button>
              </div>
            </div>
          </div>
        )}
      </nav>

      {/* ══════════ MAIN ══════════ */}
      <main className="mx-auto max-w-[1360px] px-5 py-6">

        {/* Email verification — branded, non-blocking */}
        {user && user.email_verified === false && user.email_delivery_enabled && !verifyDismissed && (
          <div className="mb-5 rounded-2xl border border-navy-200/40 overflow-hidden animate-fade-up" role="alert" style={{ background: 'linear-gradient(135deg, #f0f4ff 0%, #f8f9fb 50%, #fff9eb 100%)' }}>
            <div className="flex items-start gap-4 p-4 sm:p-5">
              {/* Icon container */}
              <div className="w-10 h-10 rounded-xl bg-navy-800/[0.07] flex items-center justify-center flex-shrink-0 mt-0.5">
                <svg className="w-5 h-5 text-navy-800" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M21.75 6.75v10.5a2.25 2.25 0 01-2.25 2.25h-15a2.25 2.25 0 01-2.25-2.25V6.75m19.5 0A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25m19.5 0v.243a2.25 2.25 0 01-1.07 1.916l-7.5 4.615a2.25 2.25 0 01-2.36 0L3.32 8.91a2.25 2.25 0 01-1.07-1.916V6.75" />
                </svg>
              </div>
              {/* Content */}
              <div className="flex-1 min-w-0">
                <h4 className="text-[14px] font-semibold text-navy-900 mb-0.5">Verify your email</h4>
                <p className="text-[12px] text-surface-400 leading-relaxed mb-3">
                  Confirm your email address to secure your Shadow account and enable password recovery.
                </p>
                <div className="flex items-center gap-3">
                  <button
                    onClick={async () => {
                      setResending(true)
                      setVerifyFeedback(null)
                      try { await resendVerification(); setVerifyFeedback({ type: 'success', text: 'Verification email sent! Check your inbox.' }) }
                      catch { setVerifyFeedback({ type: 'error', text: 'Could not send. Try again later.' }) }
                      finally { setResending(false) }
                    }}
                    disabled={resending}
                    className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-navy-800 text-white text-[12px] font-semibold hover:bg-navy-900 transition-all disabled:opacity-50 shadow-sm"
                  >
                    {resending ? (
                      <>
                        <svg className="w-3.5 h-3.5 animate-spin" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg>
                        Sending...
                      </>
                    ) : (
                      <>
                        <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                          <path strokeLinecap="round" strokeLinejoin="round" d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5" />
                        </svg>
                        Send verification email
                      </>
                    )}
                  </button>
                  {verifyFeedback && (
                    <span aria-live="polite" className={`text-[11px] font-medium ${verifyFeedback.type === 'success' ? 'text-emerald-600' : 'text-red-500'}`}>
                      {verifyFeedback.text}
                    </span>
                  )}
                </div>
              </div>
              {/* Dismiss */}
              <button onClick={() => setVerifyDismissed(true)} className="text-surface-300 hover:text-surface-400 transition-colors flex-shrink-0 p-1 rounded-lg hover:bg-surface-100" aria-label="Dismiss verification banner">
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>
        )}

        {/* Error banner */}
        {loadError && (
          <div className="mb-4 p-4 rounded-xl border border-red-200 bg-red-50 flex items-center justify-between">
            <p className="text-[13px] text-red-700 font-medium">{loadError}</p>
            <button onClick={loadAll} className="text-[12px] font-semibold text-red-600 hover:text-red-800 px-3 py-1 rounded-lg hover:bg-red-100 transition-colors">
              Retry
            </button>
          </div>
        )}

        {/* SmartStudy AI Trigger Banner */}
        <SmartStudyTriggerBanner onOpenSmartStudy={() => setShowSmartStudy(true)} />

        {/* ─── Hero: CGPA + Stats bento ─── */}
        <section className="bento-grid mb-6 animate-fade-up">
          {/* CGPA Card */}
          {(() => {
            const cgpa = user?.current_cgpa || 0
            const target = user?.target_cgpa || 4.5
            const msg = heroMessage(cgpa, target)
            const cls = classify(cgpa)
            const pctOfTarget = target > 0 ? Math.min((cgpa / target) * 100, 100) : 0
            const gap = Math.max(target - cgpa, 0)

            return (
              <div className="bento-span-8 relative overflow-hidden rounded-2xl p-6 grain">
                {/* Layered background */}
                <div className="absolute inset-0 bg-gradient-to-br from-[#0c1425] via-navy-900 to-[#0e1628]" />
                {/* Geometric grid overlay */}
                <div className="absolute inset-0 opacity-[0.025]" style={{
                  backgroundImage: 'linear-gradient(rgba(255,255,255,0.15) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.15) 1px, transparent 1px)',
                  backgroundSize: '40px 40px',
                }} />
                {/* Radial glow at top-right */}
                <div className="absolute -top-24 -right-24 w-80 h-80 rounded-full" style={{ background: 'radial-gradient(circle, rgba(30,58,138,0.2) 0%, transparent 70%)' }} />
                {/* Accent glow matching progress color */}
                <div className="absolute bottom-0 left-1/4 w-64 h-32 rounded-full blur-[80px]" style={{
                  background: pctOfTarget >= 90 ? 'rgba(16,185,129,0.08)' : pctOfTarget >= 75 ? 'rgba(245,158,11,0.08)' : 'rgba(239,68,68,0.06)'
                }} />

                <div className="relative z-10 flex items-center gap-8">
                  <CGPARing current={cgpa} target={target} />

                  <div className="flex-1 min-w-0">
                    {/* Greeting + classification */}
                    <div className="flex items-center gap-2 mb-1">
                      <p className="text-white/40 text-[12px] font-medium">{greetByTime()}, {user?.full_name?.split(' ')[0] || 'Student'}</p>
                      <span className="text-white/15">·</span>
                      <span className={`text-[11px] font-semibold ${cls.cls}`}>{cls.label}</span>
                    </div>

                    {/* Dynamic title */}
                    <h1 className="font-display text-[1.6rem] sm:text-[1.85rem] font-bold text-white leading-tight mb-1">
                      {msg.title}
                    </h1>
                    <p className="text-[13px] text-white/40 mb-4">{msg.sub}</p>

                    {/* CGPA gap bar */}
                    <div className="mb-4 max-w-sm">
                      <div className="flex items-center justify-between mb-1.5">
                        <span className="font-mono text-[12px] font-bold text-white">{cgpa.toFixed(2)}</span>
                        <span className="font-mono text-[12px] font-bold text-gold-400">{target.toFixed(2)}</span>
                      </div>
                      <div className="relative h-2 bg-white/[0.06] rounded-full overflow-hidden">
                        {/* Target marker */}
                        <div className="absolute right-0 top-0 bottom-0 w-[3px] bg-gold-400/40 rounded-full" />
                        {/* Current fill */}
                        <div
                          className="h-full rounded-full transition-all duration-1000 ease-out"
                          style={{
                            width: `${pctOfTarget}%`,
                            background: pctOfTarget >= 90
                              ? 'linear-gradient(90deg, #10b981, #34d399)'
                              : pctOfTarget >= 75
                              ? 'linear-gradient(90deg, #f59e0b, #fbbf24)'
                              : 'linear-gradient(90deg, #ef4444, #f87171)',
                          }}
                        />
                      </div>
                      <div className="flex items-center justify-between mt-1">
                        <span className="text-[10px] text-white/25 uppercase tracking-wider">Current</span>
                        <span className="text-[10px] text-white/25 uppercase tracking-wider">Target</span>
                      </div>
                    </div>

                    {/* Stats row */}
                    <div className="flex flex-wrap gap-5">
                      {[
                        { label: 'Current', value: cgpa.toFixed(2), color: 'text-white' },
                        { label: 'Target', value: target.toFixed(2), color: 'text-gold-400' },
                        { label: 'Gap', value: gap.toFixed(2), color: gap === 0 ? 'text-emerald-400' : 'text-white/70' },
                        { label: 'Credits', value: user?.total_credits_completed || 0, color: 'text-white' },
                      ].map(s => (
                        <div key={s.label}>
                          <p className="text-[9px] uppercase tracking-[0.1em] text-white/25 mb-0.5">{s.label}</p>
                          <p className={`font-mono text-lg font-bold ${s.color} leading-none`}>{s.value}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            )
          })()}

          {/* Stat tiles (right column) */}
          <div className="bento-span-4 grid grid-cols-2 gap-3">
            <StatTile label="Courses" value={enrolledCourses.length} sub={`${totalCredits} credits`} accent="navy" delay={1} />
            <StatTile
              label="Avg CA"
              value={`${averageCA.toFixed(1)}`}
              sub="out of 35"
              accent="amber"
              delay={2}
            />
            <StatTile
              label="Tasks Done"
              value={taskStats?.completed_tasks ?? '—'}
              sub={taskStats ? `of ${taskStats.total_tasks}` : ''}
              accent="emerald"
              delay={3}
            />
            {/* Mood tile */}
            <button
              onClick={() => setShowMoodLogger(true)}
              className={`animate-fade-up-4 card-lift rounded-2xl border p-5 text-left transition-all group relative overflow-hidden ${
                todayMood
                  ? 'bg-white border-surface-200/80'
                  : 'bg-gradient-to-br from-navy-800 to-navy-900 border-navy-700/60'
              }`}
            >
              {todayMood ? (
                <>
                  <div className="flex items-center justify-between mb-1.5">
                    <p className="text-[11px] font-semibold uppercase tracking-wider text-surface-400">Mood</p>
                    <span className="text-[10px] font-medium text-navy-500 opacity-0 group-hover:opacity-100 transition-opacity">update</span>
                  </div>
                  <p className="text-[28px] leading-none mb-1">
                    {todayMood.mood_type === 'focused' ? '🎯' :
                     todayMood.mood_type === 'motivated' ? '💪' :
                     todayMood.mood_type === 'calm' ? '😌' :
                     todayMood.mood_type === 'confident' ? '😎' :
                     todayMood.mood_type === 'tired' ? '😴' :
                     todayMood.mood_type === 'stressed' ? '😰' :
                     todayMood.mood_type === 'anxious' ? '😟' :
                     todayMood.mood_type === 'overwhelmed' ? '😵' : '😊'}
                  </p>
                  <p className="text-[13px] font-bold text-navy-900 capitalize">{todayMood.mood_type}</p>
                  {todayMood.energy_level && (
                    <div className="flex gap-0.5 mt-2">
                      {[1,2,3,4,5].map(i => (
                        <div key={i} className={`h-1 flex-1 rounded-full ${i <= todayMood.energy_level ? 'bg-navy-800/30' : 'bg-surface-100'}`} />
                      ))}
                    </div>
                  )}
                </>
              ) : (
                <>
                  {/* Subtle grid texture */}
                  <div className="absolute inset-0 opacity-[0.04]" style={{
                    backgroundImage: 'radial-gradient(circle, rgba(255,255,255,0.8) 1px, transparent 1px)',
                    backgroundSize: '16px 16px',
                  }} />
                  {/* Breathing glow */}
                  <div className="absolute -bottom-4 -right-4 w-20 h-20 bg-blue-400/15 rounded-full blur-xl animate-pulse" />

                  <div className="relative z-10">
                    <p className="text-[11px] font-semibold uppercase tracking-wider text-white/40 mb-2">Mood</p>
                    <div className="w-9 h-9 rounded-xl bg-white/10 flex items-center justify-center mb-2 ring-1 ring-white/[0.08]">
                      <svg className="w-[18px] h-[18px] text-white/70" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M15.182 15.182a4.5 4.5 0 01-6.364 0M21 12a9 9 0 11-18 0 9 9 0 0118 0zM9.75 9.75c0 .414-.168.75-.375.75S9 10.164 9 9.75 9.168 9 9.375 9s.375.336.375.75zm-.375 0h.008v.015h-.008V9.75zm5.625 0c0 .414-.168.75-.375.75s-.375-.336-.375-.75.168-.75.375-.75.375.336.375.75zm-.375 0h.008v.015h-.008V9.75z" />
                      </svg>
                    </div>
                    <p className="text-[13px] font-bold text-white leading-tight">How are you?</p>
                    <p className="text-[10px] text-white/40 mt-0.5">Tap to check in</p>
                  </div>
                </>
              )}
            </button>
          </div>
        </section>

        {/* ─── Course Carousel ─── */}
        {enrolledCourses.length > 0 && (
          <section className="mb-6 animate-fade-up-2">
            <CourseCarousel
              enrolledCourses={enrolledCourses}
              onCourseClick={(enrollment) => setShowCourseMenu(enrollment)}
            />
          </section>
        )}

        {/* ─── Task Overview bar ─── */}
        {taskStats && (
          <section className="mb-6 animate-fade-up-3">
            <div className="rounded-2xl border border-surface-200/80 bg-white p-5">
              <div className="flex flex-wrap items-center gap-8">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-navy-800/[0.06] flex items-center justify-center">
                    <svg className="w-5 h-5 text-navy-700" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 12h16.5m-16.5 3.75h16.5M3.75 19.5h16.5M5.625 4.5h12.75a1.875 1.875 0 010 3.75H5.625a1.875 1.875 0 010-3.75z" />
                    </svg>
                  </div>
                  <div>
                    <p className="text-[11px] font-semibold uppercase tracking-wider text-surface-400">Task Overview</p>
                    <p className="text-sm font-semibold text-navy-900">
                      {taskStats.completion_rate.toFixed(0)}% complete
                      <span className="font-normal text-surface-400"> — {taskStats.completed_tasks}/{taskStats.total_tasks} tasks</span>
                    </p>
                  </div>
                </div>

                {/* Mini progress bar */}
                <div className="flex-1 min-w-[120px] max-w-xs">
                  <div className="h-2 bg-surface-100 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-navy-700 to-navy-500 rounded-full transition-all duration-700"
                      style={{ width: `${taskStats.completion_rate}%` }}
                    />
                  </div>
                </div>

                <div className="flex items-center gap-6 text-sm">
                  <div className="flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-amber-400" />
                    <span className="text-surface-400">{taskStats.pending_tasks} pending</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-red-400" />
                    <span className="text-surface-400">{taskStats.overdue_tasks} overdue</span>
                  </div>
                  <div>
                    <span className="text-surface-400">CA earned: </span>
                    <span className="font-semibold text-navy-900">{taskStats.total_ca_earned.toFixed(1)}</span>
                    <span className="text-surface-400">/{taskStats.total_ca_available.toFixed(1)}</span>
                  </div>
                </div>
              </div>
            </div>
          </section>
        )}

        {/* ─── Priority + Tasks bento ─── */}
        <section className="bento-grid mb-6">
          {/* Priority Recommendations */}
          <div className="bento-span-5 animate-fade-up-4">
            <PriorityRecommendationsCompact onTaskClick={handlePriorityTaskClick} />
          </div>

          {/* Tasks */}
          <div id="task-section" className="bento-span-7 animate-fade-up-5">
            <div className="rounded-2xl border border-surface-200/80 bg-white overflow-hidden">
              <div className="flex justify-between items-center px-5 py-4 border-b border-surface-100">
                <h3 className="text-[15px] font-bold text-navy-900">My Tasks</h3>
                <button
                  onClick={() => setShowAddTaskModal(true)}
                  disabled={enrolledCourses.length === 0}
                  className="flex items-center gap-1.5 bg-navy-800 text-white px-3 py-1.5 rounded-lg text-[13px] font-semibold hover:bg-navy-900 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
                  </svg>
                  Add Task
                </button>
              </div>

              <div className="p-5">
                {enrolledCourses.length === 0 ? (
                  <div className="py-12 text-center">
                    <p className="text-surface-400 text-sm mb-3">Enroll in courses to start adding tasks</p>
                    <button
                      onClick={() => navigate('/courses')}
                      className="bg-navy-800 text-white px-5 py-2 rounded-lg text-[13px] font-semibold hover:bg-navy-900 transition-colors"
                    >
                      Browse Courses
                    </button>
                  </div>
                ) : (
                  <TaskList tasks={tasks} onUpdate={handleTaskCreated} showCompleted={true} enrolledCourses={enrolledCourses} />
                )}
              </div>
            </div>
          </div>
        </section>
      </main>

      {/* ══════════ MODALS ══════════ */}
      <AddTaskModal isOpen={showAddTaskModal} onClose={() => setShowAddTaskModal(false)} onTaskCreated={handleTaskCreated} enrolledCourses={enrolledCourses} />
      {showMoodLogger && <MoodLogger onMoodLogged={(mood) => { setTodayMood(mood); setShowMoodLogger(false) }} onClose={() => setShowMoodLogger(false)} />}
      {showSmartStudy && <SmartStudyChat onClose={() => setShowSmartStudy(false)} />}


      {/* Course Action Menu */}
      {showCourseMenu && (
        <div className="fixed inset-0 bg-navy-950/40 backdrop-blur-sm flex items-center justify-center z-50 p-4" onClick={() => setShowCourseMenu(null)}>
          <div className="bg-white rounded-2xl shadow-2xl max-w-xs w-full overflow-hidden animate-scale-in" onClick={e => e.stopPropagation()}>
            {/* Course header */}
            <div className="px-5 pt-5 pb-4 border-b border-surface-100">
              <h3 className="text-[16px] font-bold text-navy-900 leading-tight">{showCourseMenu.course?.code}</h3>
              <p className="text-[12px] text-surface-400 mt-0.5">{showCourseMenu.course?.title}</p>
            </div>
            {/* Actions */}
            <div className="p-2">
              <button
                onClick={() => { setShowCourseMenu(null); setShowAddTaskModal(true) }}
                className="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-[13px] font-semibold text-navy-800 hover:bg-surface-50 transition-colors"
              >
                <div className="w-8 h-8 rounded-lg bg-navy-800 flex items-center justify-center flex-shrink-0">
                  <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
                  </svg>
                </div>
                <div className="text-left">
                  <p>Add Task</p>
                  <p className="text-[10px] text-surface-400 font-normal">Create a new assignment or test</p>
                </div>
              </button>
              <button
                onClick={() => { setEditingCourse(showCourseMenu); setShowCourseMenu(null) }}
                className="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-[13px] font-semibold text-navy-800 hover:bg-surface-50 transition-colors"
              >
                <div className="w-8 h-8 rounded-lg bg-surface-100 flex items-center justify-center flex-shrink-0">
                  <svg className="w-4 h-4 text-navy-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931z" />
                  </svg>
                </div>
                <div className="text-left">
                  <p>Update Scores</p>
                  <p className="text-[10px] text-surface-400 font-normal">Edit CA, participation, or exam</p>
                </div>
              </button>
            </div>
            {/* Cancel */}
            <div className="px-5 py-3 border-t border-surface-100">
              <button onClick={() => setShowCourseMenu(null)} className="w-full py-1.5 text-[12px] font-medium text-surface-400 hover:text-navy-800 transition-colors">
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      <EditCourseScoresModal isOpen={!!editingCourse} onClose={() => setEditingCourse(null)} enrollment={editingCourse} onUpdate={handleUpdateCourseScores} />
    </div>
  )
}

export default DashboardPage
