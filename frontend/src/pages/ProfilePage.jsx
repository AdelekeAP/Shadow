import { useState, useEffect, useMemo, useRef } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import {
  changePassword,
  updateUserPreferences,
  fetchCurrentUser,
} from '../services/api'
import { useAuth } from '../contexts/AuthContext'
import NotificationBell from '../components/NotificationBell'

/* ─── CGPA classification helper ─── */
const classify = (cgpa) => {
  if (cgpa >= 4.50) return { label: 'First Class', color: 'text-emerald-400', bg: 'bg-emerald-400/10', border: 'border-emerald-400/20' }
  if (cgpa >= 3.50) return { label: '2nd Class Upper', color: 'text-blue-400', bg: 'bg-blue-400/10', border: 'border-blue-400/20' }
  if (cgpa >= 2.40) return { label: '2nd Class Lower', color: 'text-amber-400', bg: 'bg-amber-400/10', border: 'border-amber-400/20' }
  if (cgpa >= 1.50) return { label: 'Third Class', color: 'text-orange-400', bg: 'bg-orange-400/10', border: 'border-orange-400/20' }
  return { label: 'Unclassified', color: 'text-surface-400', bg: 'bg-surface-400/10', border: 'border-surface-400/20' }
}

/* ─── Password strength calculator ─── */
const getPasswordStrength = (pw) => {
  if (!pw) return { score: 0, label: '', color: 'bg-surface-200' }
  let score = 0
  if (pw.length >= 8) score++
  if (/[a-z]/.test(pw)) score++
  if (/[A-Z]/.test(pw)) score++
  if (/[0-9]/.test(pw)) score++
  if (/[^a-zA-Z0-9]/.test(pw)) score++
  if (score <= 1) return { score: 1, label: 'Weak', color: 'bg-red-500' }
  if (score <= 2) return { score: 2, label: 'Fair', color: 'bg-orange-500' }
  if (score <= 3) return { score: 3, label: 'Good', color: 'bg-amber-500' }
  if (score <= 4) return { score: 4, label: 'Strong', color: 'bg-emerald-500' }
  return { score: 5, label: 'Excellent', color: 'bg-emerald-600' }
}

/* ─── CGPA scale classification labels ─── */
const SCALE_MARKS = [
  { value: 0, label: '' },
  { value: 1.5, label: 'Third' },
  { value: 2.4, label: '2:2' },
  { value: 3.5, label: '2:1' },
  { value: 4.5, label: '1st' },
  { value: 5.0, label: '' },
]

/* ─── Learning style SVG icons ─── */
const VisualIcon = ({ active }) => (
  <svg width="32" height="32" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
    <circle cx="16" cy="16" r="5" stroke={active ? '#1e3a8a' : '#9ba2b5'} strokeWidth="1.5" fill={active ? 'rgba(30,58,138,0.08)' : 'none'} />
    <circle cx="16" cy="16" r="2" fill={active ? '#1e3a8a' : '#9ba2b5'} />
    <path d="M3 16C3 16 8 8 16 8C24 8 29 16 29 16C29 16 24 24 16 24C8 24 3 16 3 16Z" stroke={active ? '#1e3a8a' : '#9ba2b5'} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" fill="none" />
    <line x1="16" y1="3" x2="16" y2="6" stroke={active ? '#1e3a8a' : '#d1d5e0'} strokeWidth="1" strokeLinecap="round" />
    <line x1="16" y1="26" x2="16" y2="29" stroke={active ? '#1e3a8a' : '#d1d5e0'} strokeWidth="1" strokeLinecap="round" />
    <line x1="5.5" y1="7.5" x2="7.5" y2="9.5" stroke={active ? '#1e3a8a' : '#d1d5e0'} strokeWidth="1" strokeLinecap="round" />
    <line x1="24.5" y1="22.5" x2="26.5" y2="24.5" stroke={active ? '#1e3a8a' : '#d1d5e0'} strokeWidth="1" strokeLinecap="round" />
    <line x1="26.5" y1="7.5" x2="24.5" y2="9.5" stroke={active ? '#1e3a8a' : '#d1d5e0'} strokeWidth="1" strokeLinecap="round" />
    <line x1="5.5" y1="24.5" x2="7.5" y2="22.5" stroke={active ? '#1e3a8a' : '#d1d5e0'} strokeWidth="1" strokeLinecap="round" />
  </svg>
)

const AuditoryIcon = ({ active }) => (
  <svg width="32" height="32" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M7 13C7 13 7 10 10 10L10 22C7 22 7 19 7 19" stroke={active ? '#1e3a8a' : '#9ba2b5'} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    <rect x="10" y="10" width="3" height="12" rx="0.5" fill={active ? 'rgba(30,58,138,0.12)' : 'rgba(155,162,181,0.1)'} stroke={active ? '#1e3a8a' : '#9ba2b5'} strokeWidth="1.5" />
    <path d="M13 12L19 8V24L13 20" stroke={active ? '#1e3a8a' : '#9ba2b5'} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" fill={active ? 'rgba(30,58,138,0.06)' : 'none'} />
    <path d="M22 12C23.5 13.5 23.5 18.5 22 20" stroke={active ? '#1e3a8a' : '#d1d5e0'} strokeWidth="1.5" strokeLinecap="round" />
    <path d="M25 9.5C27.5 12 27.5 20 25 22.5" stroke={active ? '#1e3a8a' : '#d1d5e0'} strokeWidth="1.5" strokeLinecap="round" />
  </svg>
)

const ReadingIcon = ({ active }) => (
  <svg width="32" height="32" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M16 8C16 8 13 5 7 5V24C13 24 16 26 16 26" stroke={active ? '#1e3a8a' : '#9ba2b5'} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" fill={active ? 'rgba(30,58,138,0.05)' : 'none'} />
    <path d="M16 8C16 8 19 5 25 5V24C19 24 16 26 16 26" stroke={active ? '#1e3a8a' : '#9ba2b5'} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" fill={active ? 'rgba(30,58,138,0.05)' : 'none'} />
    <line x1="16" y1="8" x2="16" y2="26" stroke={active ? '#1e3a8a' : '#d1d5e0'} strokeWidth="1" />
    <line x1="10" y1="10" x2="13" y2="10" stroke={active ? '#1e3a8a' : '#d1d5e0'} strokeWidth="1" strokeLinecap="round" />
    <line x1="10" y1="13" x2="13" y2="13" stroke={active ? '#1e3a8a' : '#d1d5e0'} strokeWidth="1" strokeLinecap="round" />
    <line x1="10" y1="16" x2="13" y2="16" stroke={active ? '#1e3a8a' : '#d1d5e0'} strokeWidth="1" strokeLinecap="round" />
    <line x1="19" y1="10" x2="22" y2="10" stroke={active ? '#1e3a8a' : '#d1d5e0'} strokeWidth="1" strokeLinecap="round" />
    <line x1="19" y1="13" x2="22" y2="13" stroke={active ? '#1e3a8a' : '#d1d5e0'} strokeWidth="1" strokeLinecap="round" />
    <line x1="19" y1="16" x2="22" y2="16" stroke={active ? '#1e3a8a' : '#d1d5e0'} strokeWidth="1" strokeLinecap="round" />
  </svg>
)

const KinestheticIcon = ({ active }) => (
  <svg width="32" height="32" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
    <circle cx="16" cy="16" r="8" stroke={active ? '#1e3a8a' : '#9ba2b5'} strokeWidth="1.5" fill={active ? 'rgba(30,58,138,0.04)' : 'none'} />
    <path d="M13 14L16 11L19 14" stroke={active ? '#1e3a8a' : '#9ba2b5'} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    <path d="M12 18C12 18 13.5 20 16 20C18.5 20 20 18 20 18" stroke={active ? '#1e3a8a' : '#9ba2b5'} strokeWidth="1.5" strokeLinecap="round" />
    <circle cx="16" cy="16" r="1.5" fill={active ? '#1e3a8a' : '#9ba2b5'} />
    <line x1="16" y1="4" x2="16" y2="7" stroke={active ? '#1e3a8a' : '#d1d5e0'} strokeWidth="1.5" strokeLinecap="round" />
    <line x1="16" y1="25" x2="16" y2="28" stroke={active ? '#1e3a8a' : '#d1d5e0'} strokeWidth="1.5" strokeLinecap="round" />
    <line x1="4" y1="16" x2="7" y2="16" stroke={active ? '#1e3a8a' : '#d1d5e0'} strokeWidth="1.5" strokeLinecap="round" />
    <line x1="25" y1="16" x2="28" y2="16" stroke={active ? '#1e3a8a' : '#d1d5e0'} strokeWidth="1.5" strokeLinecap="round" />
  </svg>
)

const LEARNING_STYLES = [
  { value: 'visual', label: 'Visual', Icon: VisualIcon, desc: 'Diagrams, charts, videos' },
  { value: 'auditory', label: 'Auditory', Icon: AuditoryIcon, desc: 'Lectures, podcasts, discussion' },
  { value: 'reading', label: 'Reading', Icon: ReadingIcon, desc: 'Textbooks, articles, notes' },
  { value: 'kinesthetic', label: 'Kinesthetic', Icon: KinestheticIcon, desc: 'Practice, hands-on projects' },
]

/* ─── Section tab config ─── */
const SECTIONS = [
  {
    id: 'profile',
    label: 'Profile',
    icon: (
      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
        <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" />
      </svg>
    ),
  },
  {
    id: 'security',
    label: 'Security',
    icon: (
      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
        <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
      </svg>
    ),
  },
  {
    id: 'preferences',
    label: 'Preferences',
    icon: (
      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
        <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 6h9.75M10.5 6a1.5 1.5 0 11-3 0m3 0a1.5 1.5 0 10-3 0M3.75 6H7.5m3 12h9.75m-9.75 0a1.5 1.5 0 01-3 0m3 0a1.5 1.5 0 00-3 0m-3.75 0H7.5m9-6h3.75m-3.75 0a1.5 1.5 0 01-3 0m3 0a1.5 1.5 0 00-3 0m-9.75 0h9.75" />
      </svg>
    ),
  },
]

/* ═══════════════════════════════════════════════
   Profile Page
   ═══════════════════════════════════════════════ */
function ProfilePage() {
  const navigate = useNavigate()
  const location = useLocation()
  const { user: authUser, logout } = useAuth()
  const [user, setUser] = useState(null)
  const [menuOpen, setMenuOpen] = useState(false)
  const [activeSection, setActiveSection] = useState('profile')

  /* Change password state */
  const [oldPassword, setOldPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [pwLoading, setPwLoading] = useState(false)
  const [pwMessage, setPwMessage] = useState(null)
  const [showOldPw, setShowOldPw] = useState(false)
  const [showNewPw, setShowNewPw] = useState(false)
  const [showConfirmPw, setShowConfirmPw] = useState(false)

  const logoutTimerRef = useRef(null)

  /* Preferences state */
  const [selectedStyle, setSelectedStyle] = useState(null)
  const [targetCGPA, setTargetCGPA] = useState('')
  const [prefLoading, setPrefLoading] = useState(false)
  const [prefMessage, setPrefMessage] = useState(null)

  useEffect(() => {
    const loadUser = async () => {
      try {
        const freshUser = await fetchCurrentUser()
        setUser(freshUser)
        setSelectedStyle(freshUser.learning_style || null)
        setTargetCGPA(freshUser.target_cgpa?.toString() || '')
      } catch {
        setUser(authUser)
      }
    }
    loadUser()
  }, [])

  useEffect(() => {
    const hash = location.hash.replace('#', '')
    if (['profile', 'security', 'preferences'].includes(hash)) {
      setActiveSection(hash)
    }
  }, [location.hash])

  useEffect(() => {
    return () => {
      if (logoutTimerRef.current) clearTimeout(logoutTimerRef.current)
    }
  }, [])

  const handleLogout = () => logout()

  const handleChangePassword = async (e) => {
    e.preventDefault()
    setPwMessage(null)
    if (newPassword !== confirmPassword) {
      setPwMessage({ type: 'error', text: 'New passwords do not match.' })
      return
    }
    setPwLoading(true)
    try {
      await changePassword(oldPassword, newPassword)
      setPwMessage({ type: 'success', text: 'Password changed. Logging you out...' })
      setOldPassword(''); setNewPassword(''); setConfirmPassword('')
      logoutTimerRef.current = setTimeout(() => logout(), 2000)
    } catch (err) {
      setPwMessage({ type: 'error', text: err.detail || 'Failed to change password.' })
    } finally { setPwLoading(false) }
  }

  const handleSavePreferences = async () => {
    setPrefLoading(true)
    setPrefMessage(null)
    try {
      const payload = {}
      if (selectedStyle) payload.learning_style = selectedStyle
      if (targetCGPA) payload.target_cgpa = parseFloat(targetCGPA)
      await updateUserPreferences(payload)
      setPrefMessage({ type: 'success', text: 'Preferences saved.' })
      const freshUser = await fetchCurrentUser()
      setUser(freshUser)
    } catch (err) {
      setPrefMessage({ type: 'error', text: err.detail || 'Failed to save preferences.' })
    } finally { setPrefLoading(false) }
  }

  const initials = (user?.full_name || 'U').split(' ').filter(n => n.length > 0).map(n => n[0]).join('').slice(0, 2) || 'U'
  const cgpa = user?.current_cgpa || 0
  const classification = classify(cgpa)
  const pwStrength = useMemo(() => getPasswordStrength(newPassword), [newPassword])

  /* CGPA slider percentage for the visual indicator */
  const cgpaSliderPct = targetCGPA ? Math.min((parseFloat(targetCGPA) / 5.0) * 100, 100) : 0
  const targetClassification = targetCGPA ? classify(parseFloat(targetCGPA)) : null

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
                { label: 'SmartStudy', path: '/smartstudy' },
              ].map(link => (
                <button key={link.path} onClick={() => navigate(link.path)}
                  className="px-3 py-1.5 rounded-lg text-[13px] font-medium transition-colors text-surface-400 hover:text-navy-800 hover:bg-surface-100">
                  {link.label}
                </button>
              ))}
            </div>
          </div>
          <div className="flex items-center gap-2">
            <NotificationBell />
            <div className="hidden md:flex items-center gap-2">
              <div className="w-7 h-7 rounded-full bg-navy-800 flex items-center justify-center ring-2 ring-navy-200">
                <span className="text-[11px] font-bold text-white">{initials}</span>
              </div>
              <span className="text-[13px] font-semibold text-navy-800">{user?.full_name?.split(' ')[0] || 'User'}</span>
            </div>
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
              {['Dashboard', 'Courses', 'CGPA', 'Library', 'SmartStudy'].map(label => (
                <button key={label} onClick={() => { navigate(`/${label.toLowerCase()}`); setMenuOpen(false) }}
                  className="block w-full text-left px-3 py-2 rounded-lg text-[14px] font-medium text-surface-400 hover:bg-surface-100">
                  {label}
                </button>
              ))}
              <div className="border-t border-surface-200 pt-2 mt-2">
                <button onClick={handleLogout} className="block w-full text-left px-3 py-2 rounded-lg text-[14px] font-medium text-red-500 hover:bg-red-50">
                  Sign out
                </button>
              </div>
            </div>
          </div>
        )}
      </nav>

      {/* ══════════ HERO HEADER ══════════ */}
      <div className="relative overflow-hidden bg-gradient-to-br from-navy-950 via-navy-900 to-navy-800 animate-fade-up">
        {/* Geometric grid overlay */}
        <div className="absolute inset-0 opacity-[0.04]" style={{
          backgroundImage: `linear-gradient(rgba(255,255,255,0.5) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.5) 1px, transparent 1px)`,
          backgroundSize: '40px 40px',
        }} />
        {/* Gradient orbs */}
        <div className="absolute -top-20 -right-20 w-80 h-80 rounded-full opacity-20" style={{
          background: 'radial-gradient(circle, rgba(30,58,138,0.6) 0%, transparent 70%)',
        }} />
        <div className="absolute -bottom-16 left-[15%] w-64 h-64 rounded-full opacity-15" style={{
          background: 'radial-gradient(circle, rgba(245,183,49,0.4) 0%, transparent 70%)',
        }} />
        {/* Grain texture */}
        <div className="absolute inset-0 opacity-[0.03] pointer-events-none" style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E")`,
        }} />

        <div className="relative mx-auto max-w-[1360px] px-5 py-10 sm:py-14">
          <div className="flex flex-col sm:flex-row items-center sm:items-end gap-6 sm:gap-8">
            {/* Avatar with gradient ring */}
            <div className="relative flex-shrink-0">
              <div className="w-24 h-24 sm:w-28 sm:h-28 rounded-full flex items-center justify-center"
                style={{
                  background: 'linear-gradient(135deg, #f5b731 0%, #1e3a8a 50%, #172554 100%)',
                  padding: '3px',
                }}>
                <div className="w-full h-full rounded-full bg-navy-900 flex items-center justify-center">
                  <span className="text-2xl sm:text-3xl font-bold text-white font-display tracking-wide">{initials}</span>
                </div>
              </div>
              {/* Verified / unverified badge */}
              <div className="absolute -bottom-1 -right-1">
                {user?.email_verified ? (
                  <div className="w-7 h-7 rounded-full bg-emerald-500 flex items-center justify-center ring-2 ring-navy-900" title="Email verified">
                    <svg className="w-3.5 h-3.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                    </svg>
                  </div>
                ) : (
                  <div className="w-7 h-7 rounded-full bg-amber-500 flex items-center justify-center ring-2 ring-navy-900" title="Email not verified">
                    <svg className="w-3.5 h-3.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
                    </svg>
                  </div>
                )}
              </div>
            </div>

            {/* Name + stats */}
            <div className="flex-1 text-center sm:text-left pb-1">
              <h1 className="font-display text-2xl sm:text-3xl font-semibold text-white tracking-tight leading-tight">
                {user?.full_name || 'Student'}
              </h1>
              <p className="text-[13px] text-white/40 mt-1 font-medium">{user?.email}</p>

              {/* Stat pills */}
              <div className="flex flex-wrap items-center justify-center sm:justify-start gap-2 mt-4">
                {/* CGPA pill */}
                <div className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-white/[0.08] border border-white/[0.08] backdrop-blur-sm">
                  <span className="text-[11px] font-semibold uppercase tracking-wider text-white/40">CGPA</span>
                  <span className="font-mono text-[13px] font-bold text-white">{cgpa.toFixed(2)}</span>
                </div>
                {/* Classification pill */}
                <div className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full border backdrop-blur-sm ${classification.bg} ${classification.border}`}>
                  <span className={`text-[12px] font-semibold ${classification.color}`}>{classification.label}</span>
                </div>
                {/* Credits pill */}
                <div className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-white/[0.08] border border-white/[0.08] backdrop-blur-sm">
                  <span className="text-[11px] font-semibold uppercase tracking-wider text-white/40">Credits</span>
                  <span className="font-mono text-[13px] font-bold text-white">{user?.total_credits_completed || 0}</span>
                </div>
                {/* Entry level pill */}
                {user?.entry_level && (
                  <div className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-white/[0.08] border border-white/[0.08] backdrop-blur-sm">
                    <span className="text-[11px] font-semibold uppercase tracking-wider text-white/40">Level</span>
                    <span className="text-[12px] font-semibold text-white">{user.entry_level}</span>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ══════════ TABS ══════════ */}
      <div className="sticky top-14 z-30 bg-white/80 backdrop-blur-xl border-b border-surface-200/80">
        <div className="mx-auto max-w-[1360px] px-5">
          <div className="flex items-center gap-1 overflow-x-auto scrollbar-hide -mb-px" role="tablist" aria-label="Profile sections">
            {SECTIONS.map((section) => {
              const isActive = activeSection === section.id
              return (
                <button
                  key={section.id}
                  role="tab"
                  aria-selected={isActive}
                  aria-controls={`tabpanel-${section.id}`}
                  id={`tab-${section.id}`}
                  onClick={() => setActiveSection(section.id)}
                  className={`relative flex items-center gap-2 px-4 py-3 text-[13px] font-semibold whitespace-nowrap transition-colors ${
                    isActive
                      ? 'text-navy-800'
                      : 'text-surface-400 hover:text-navy-700'
                  }`}
                >
                  {section.icon}
                  {section.label}
                  {/* Active indicator bar */}
                  {isActive && (
                    <span className="absolute bottom-0 left-2 right-2 h-[2px] bg-navy-800 rounded-full" style={{
                      animation: 'fadeIn 0.2s ease-out',
                    }} />
                  )}
                </button>
              )
            })}
          </div>
        </div>
      </div>

      {/* ══════════ CONTENT ══════════ */}
      <main className="mx-auto max-w-[1360px] px-5 py-8">

        {/* ── Profile Section ── */}
        {activeSection === 'profile' && (
          <div className="space-y-6 animate-fade-up" role="tabpanel" id="tabpanel-profile" aria-labelledby="tab-profile">
            {/* Personal Information */}
            <div>
              <div className="flex items-center gap-2 mb-4">
                <svg className="w-4 h-4 text-navy-800" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" />
                </svg>
                <h3 className="text-[13px] font-bold uppercase tracking-wider text-navy-800">Personal</h3>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {/* Full Name */}
                <div className="rounded-xl border border-surface-200/80 bg-white p-4 pl-5 border-l-[3px] border-l-navy-800/20">
                  <p className="text-[11px] font-semibold uppercase tracking-wider text-surface-400 mb-1">Full Name</p>
                  <p className="text-[14px] font-semibold text-navy-900">{user?.full_name || '\u2014'}</p>
                </div>
                {/* Email with verification badge */}
                <div className="rounded-xl border border-surface-200/80 bg-white p-4 pl-5 border-l-[3px] border-l-navy-800/20">
                  <p className="text-[11px] font-semibold uppercase tracking-wider text-surface-400 mb-1">Email</p>
                  <div className="flex items-center gap-2">
                    <p className="text-[14px] font-semibold text-navy-900 truncate">{user?.email || '\u2014'}</p>
                    {user?.email_verified ? (
                      <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-md bg-emerald-50 border border-emerald-200 flex-shrink-0">
                        <svg className="w-3 h-3 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5">
                          <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                        </svg>
                        <span className="text-[10px] font-semibold text-emerald-700">Verified</span>
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-md bg-amber-50 border border-amber-200 flex-shrink-0">
                        <svg className="w-3 h-3 text-amber-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5">
                          <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
                        </svg>
                        <span className="text-[10px] font-semibold text-amber-700">Unverified</span>
                      </span>
                    )}
                  </div>
                </div>
                {/* University ID */}
                <div className="rounded-xl border border-surface-200/80 bg-white p-4 pl-5 border-l-[3px] border-l-navy-800/20">
                  <p className="text-[11px] font-semibold uppercase tracking-wider text-surface-400 mb-1">University ID</p>
                  <p className="text-[14px] font-semibold text-navy-900 font-mono">{user?.university_id || '\u2014'}</p>
                </div>
                {/* Account Created */}
                <div className="rounded-xl border border-surface-200/80 bg-white p-4 pl-5 border-l-[3px] border-l-navy-800/20">
                  <p className="text-[11px] font-semibold uppercase tracking-wider text-surface-400 mb-1">Account Created</p>
                  <p className="text-[14px] font-semibold text-navy-900">
                    {user?.created_at ? new Date(user.created_at).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' }) : '\u2014'}
                  </p>
                </div>
              </div>
            </div>

            {/* Academic Information */}
            <div>
              <div className="flex items-center gap-2 mb-4">
                <svg className="w-4 h-4 text-navy-800" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M4.26 10.147a60.436 60.436 0 00-.491 6.347A48.627 48.627 0 0112 20.904a48.627 48.627 0 018.232-4.41 60.46 60.46 0 00-.491-6.347m-15.482 0a50.57 50.57 0 00-2.658-.813A59.905 59.905 0 0112 3.493a59.902 59.902 0 0110.399 5.84c-.896.248-1.783.52-2.658.814m-15.482 0A50.697 50.697 0 0112 13.489a50.702 50.702 0 017.74-3.342" />
                </svg>
                <h3 className="text-[13px] font-bold uppercase tracking-wider text-navy-800">Academic</h3>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {/* Entry Level */}
                <div className="rounded-xl border border-surface-200/80 bg-white p-4 pl-5 border-l-[3px] border-l-gold-400/40">
                  <p className="text-[11px] font-semibold uppercase tracking-wider text-surface-400 mb-1">Entry Level</p>
                  <p className="text-[14px] font-semibold text-navy-900">{user?.entry_level || '\u2014'}</p>
                </div>
                {/* Current CGPA */}
                <div className="rounded-xl border border-surface-200/80 bg-white p-4 pl-5 border-l-[3px] border-l-gold-400/40">
                  <p className="text-[11px] font-semibold uppercase tracking-wider text-surface-400 mb-1">Current CGPA</p>
                  <p className="text-[14px] font-semibold text-navy-900 font-mono">
                    {cgpa.toFixed(2)} <span className="text-surface-400 font-sans text-[12px] font-medium">/ 5.00</span>
                  </p>
                </div>
                {/* Credits */}
                <div className="rounded-xl border border-surface-200/80 bg-white p-4 pl-5 border-l-[3px] border-l-gold-400/40">
                  <p className="text-[11px] font-semibold uppercase tracking-wider text-surface-400 mb-1">Credits Completed</p>
                  <p className="text-[14px] font-semibold text-navy-900 font-mono">{user?.total_credits_completed || 0}</p>
                </div>
                {/* Last Login */}
                <div className="rounded-xl border border-surface-200/80 bg-white p-4 pl-5 border-l-[3px] border-l-gold-400/40">
                  <p className="text-[11px] font-semibold uppercase tracking-wider text-surface-400 mb-1">Last Login</p>
                  <p className="text-[14px] font-semibold text-navy-900">
                    {user?.last_login ? new Date(user.last_login).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' }) : '\u2014'}
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ── Security Section ── */}
        {activeSection === 'security' && (
          <div className="animate-fade-up" role="tabpanel" id="tabpanel-security" aria-labelledby="tab-security">
            <div className="rounded-2xl border border-surface-200/80 bg-white p-6 sm:p-8 max-w-xl">
              {/* Header with shield icon */}
              <div className="flex items-center gap-3 mb-1.5">
                <div className="w-10 h-10 rounded-xl bg-navy-800/[0.06] flex items-center justify-center">
                  <svg className="w-5 h-5 text-navy-800" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
                  </svg>
                </div>
                <div>
                  <h3 className="text-[16px] font-bold text-navy-900">Change Password</h3>
                  <p className="text-[13px] text-surface-400">You will be logged out after a successful change.</p>
                </div>
              </div>

              <div className="mt-6">
                <form onSubmit={handleChangePassword} className="space-y-5">
                  {/* Current Password */}
                  <div>
                    <label className="block text-[12px] font-semibold text-surface-400 uppercase tracking-wider mb-2">Current Password</label>
                    <div className="relative">
                      <input
                        type={showOldPw ? 'text' : 'password'}
                        value={oldPassword}
                        onChange={(e) => setOldPassword(e.target.value)}
                        required
                        className="w-full px-4 py-3 rounded-xl border border-surface-200 bg-surface-50 text-[14px] text-navy-900 placeholder:text-surface-300 focus:outline-none focus:ring-2 focus:ring-navy-200 focus:border-navy-400 focus:bg-white transition-all pr-11"
                        placeholder="Enter current password"
                      />
                      <button type="button" onClick={() => setShowOldPw(!showOldPw)}
                        aria-label={showOldPw ? 'Hide current password' : 'Show current password'}
                        className="absolute right-3 top-1/2 -translate-y-1/2 p-1 rounded-md text-surface-400 hover:text-navy-700 transition-colors">
                        {showOldPw ? (
                          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
                            <path strokeLinecap="round" strokeLinejoin="round" d="M3.98 8.223A10.477 10.477 0 001.934 12C3.226 16.338 7.244 19.5 12 19.5c.993 0 1.953-.138 2.863-.395M6.228 6.228A10.45 10.45 0 0112 4.5c4.756 0 8.773 3.162 10.065 7.498a10.523 10.523 0 01-4.293 5.774M6.228 6.228L3 3m3.228 3.228l3.65 3.65m7.894 7.894L21 21m-3.228-3.228l-3.65-3.65m0 0a3 3 0 10-4.243-4.243m4.242 4.242L9.88 9.88" />
                          </svg>
                        ) : (
                          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
                            <path strokeLinecap="round" strokeLinejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z" />
                            <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                          </svg>
                        )}
                      </button>
                    </div>
                  </div>

                  {/* New Password */}
                  <div>
                    <label className="block text-[12px] font-semibold text-surface-400 uppercase tracking-wider mb-2">New Password</label>
                    <div className="relative">
                      <input
                        type={showNewPw ? 'text' : 'password'}
                        value={newPassword}
                        onChange={(e) => setNewPassword(e.target.value)}
                        required
                        className="w-full px-4 py-3 rounded-xl border border-surface-200 bg-surface-50 text-[14px] text-navy-900 placeholder:text-surface-300 focus:outline-none focus:ring-2 focus:ring-navy-200 focus:border-navy-400 focus:bg-white transition-all pr-11"
                        placeholder="Min 8 chars, upper + lower + number"
                      />
                      <button type="button" onClick={() => setShowNewPw(!showNewPw)}
                        aria-label={showNewPw ? 'Hide new password' : 'Show new password'}
                        className="absolute right-3 top-1/2 -translate-y-1/2 p-1 rounded-md text-surface-400 hover:text-navy-700 transition-colors">
                        {showNewPw ? (
                          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
                            <path strokeLinecap="round" strokeLinejoin="round" d="M3.98 8.223A10.477 10.477 0 001.934 12C3.226 16.338 7.244 19.5 12 19.5c.993 0 1.953-.138 2.863-.395M6.228 6.228A10.45 10.45 0 0112 4.5c4.756 0 8.773 3.162 10.065 7.498a10.523 10.523 0 01-4.293 5.774M6.228 6.228L3 3m3.228 3.228l3.65 3.65m7.894 7.894L21 21m-3.228-3.228l-3.65-3.65m0 0a3 3 0 10-4.243-4.243m4.242 4.242L9.88 9.88" />
                          </svg>
                        ) : (
                          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
                            <path strokeLinecap="round" strokeLinejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z" />
                            <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                          </svg>
                        )}
                      </button>
                    </div>
                    {/* Password strength indicator */}
                    {newPassword && (
                      <div className="mt-2.5">
                        <div className="flex items-center gap-2">
                          <div className="flex-1 h-1.5 bg-surface-100 rounded-full overflow-hidden">
                            <div
                              className={`h-full rounded-full transition-all duration-300 ${pwStrength.color}`}
                              style={{ width: `${(pwStrength.score / 5) * 100}%` }}
                            />
                          </div>
                          <span className={`text-[11px] font-semibold ${
                            pwStrength.score <= 1 ? 'text-red-500' :
                            pwStrength.score <= 2 ? 'text-orange-500' :
                            pwStrength.score <= 3 ? 'text-amber-500' :
                            'text-emerald-600'
                          }`}>
                            {pwStrength.label}
                          </span>
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Confirm New Password */}
                  <div>
                    <label className="block text-[12px] font-semibold text-surface-400 uppercase tracking-wider mb-2">Confirm New Password</label>
                    <div className="relative">
                      <input
                        type={showConfirmPw ? 'text' : 'password'}
                        value={confirmPassword}
                        onChange={(e) => setConfirmPassword(e.target.value)}
                        required
                        className={`w-full px-4 py-3 rounded-xl border bg-surface-50 text-[14px] text-navy-900 placeholder:text-surface-300 focus:outline-none focus:ring-2 focus:ring-navy-200 focus:border-navy-400 focus:bg-white transition-all pr-11 ${
                          confirmPassword && confirmPassword !== newPassword
                            ? 'border-red-300 focus:ring-red-200 focus:border-red-400'
                            : confirmPassword && confirmPassword === newPassword
                            ? 'border-emerald-300 focus:ring-emerald-200 focus:border-emerald-400'
                            : 'border-surface-200'
                        }`}
                        placeholder="Re-enter new password"
                      />
                      <button type="button" onClick={() => setShowConfirmPw(!showConfirmPw)}
                        aria-label={showConfirmPw ? 'Hide confirm password' : 'Show confirm password'}
                        className="absolute right-3 top-1/2 -translate-y-1/2 p-1 rounded-md text-surface-400 hover:text-navy-700 transition-colors">
                        {showConfirmPw ? (
                          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
                            <path strokeLinecap="round" strokeLinejoin="round" d="M3.98 8.223A10.477 10.477 0 001.934 12C3.226 16.338 7.244 19.5 12 19.5c.993 0 1.953-.138 2.863-.395M6.228 6.228A10.45 10.45 0 0112 4.5c4.756 0 8.773 3.162 10.065 7.498a10.523 10.523 0 01-4.293 5.774M6.228 6.228L3 3m3.228 3.228l3.65 3.65m7.894 7.894L21 21m-3.228-3.228l-3.65-3.65m0 0a3 3 0 10-4.243-4.243m4.242 4.242L9.88 9.88" />
                          </svg>
                        ) : (
                          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
                            <path strokeLinecap="round" strokeLinejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z" />
                            <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                          </svg>
                        )}
                      </button>
                    </div>
                    {confirmPassword && confirmPassword !== newPassword && (
                      <p className="text-[11px] text-red-500 font-medium mt-1.5">Passwords do not match</p>
                    )}
                  </div>

                  {/* Message */}
                  {pwMessage && (
                    <div className={`flex items-center gap-2.5 p-3.5 rounded-xl text-[13px] font-medium ${
                      pwMessage.type === 'success'
                        ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                        : 'bg-red-50 text-red-700 border border-red-200'
                    }`}>
                      {pwMessage.type === 'success' ? (
                        <svg className="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                          <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                      ) : (
                        <svg className="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                          <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
                        </svg>
                      )}
                      {pwMessage.text}
                    </div>
                  )}

                  {/* Submit */}
                  <button type="submit" disabled={pwLoading || !oldPassword || !newPassword || !confirmPassword}
                    className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-navy-800 text-white text-[13px] font-semibold hover:bg-navy-900 transition-all disabled:opacity-40 disabled:cursor-not-allowed shadow-sm hover:shadow-md">
                    {pwLoading ? (
                      <>
                        <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                        </svg>
                        Changing...
                      </>
                    ) : (
                      <>
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
                          <path strokeLinecap="round" strokeLinejoin="round" d="M16.5 10.5V6.75a4.5 4.5 0 10-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H6.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z" />
                        </svg>
                        Change Password
                      </>
                    )}
                  </button>
                </form>
              </div>
            </div>
          </div>
        )}

        {/* ── Preferences Section ── */}
        {activeSection === 'preferences' && (
          <div className="space-y-6 animate-fade-up" role="tabpanel" id="tabpanel-preferences" aria-labelledby="tab-preferences">

            {/* Learning Style */}
            <div className="rounded-2xl border border-surface-200/80 bg-white p-6 sm:p-8">
              <div className="flex items-center gap-3 mb-1.5">
                <div className="w-10 h-10 rounded-xl bg-navy-800/[0.06] flex items-center justify-center">
                  <svg className="w-5 h-5 text-navy-800" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 18v-5.25m0 0a6.01 6.01 0 001.5-.189m-1.5.189a6.01 6.01 0 01-1.5-.189m3.75 7.478a12.06 12.06 0 01-4.5 0m3.75 2.383a14.406 14.406 0 01-3 0M14.25 18v-.192c0-.983.658-1.823 1.508-2.316a7.5 7.5 0 10-7.517 0c.85.493 1.509 1.333 1.509 2.316V18" />
                  </svg>
                </div>
                <div>
                  <h3 className="text-[16px] font-bold text-navy-900">Learning Style</h3>
                  <p className="text-[13px] text-surface-400">SmartStudy uses this to personalize your study plans. You can override per topic.</p>
                </div>
              </div>

              <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mt-6">
                {LEARNING_STYLES.map(style => {
                  const isSelected = selectedStyle === style.value
                  return (
                    <button
                      key={style.value}
                      onClick={() => setSelectedStyle(style.value)}
                      className={`card-lift relative p-5 rounded-xl border text-left transition-all group ${
                        isSelected
                          ? 'border-navy-300 bg-gradient-to-br from-navy-50 to-navy-100/50 ring-2 ring-navy-200/80 shadow-sm'
                          : 'border-surface-200/80 bg-white hover:border-surface-300 hover:bg-surface-50/50'
                      }`}
                    >
                      {/* Selected check mark */}
                      {isSelected && (
                        <div className="absolute top-3 right-3 w-5 h-5 rounded-full bg-navy-800 flex items-center justify-center">
                          <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="3">
                            <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                          </svg>
                        </div>
                      )}
                      <div className="mb-3">
                        <style.Icon active={isSelected} />
                      </div>
                      <p className={`text-[14px] font-semibold ${isSelected ? 'text-navy-800' : 'text-navy-900'}`}>
                        {style.label}
                      </p>
                      <p className="text-[11px] text-surface-400 mt-0.5 leading-relaxed">{style.desc}</p>
                    </button>
                  )
                })}
              </div>
            </div>

            {/* Target CGPA */}
            <div className="rounded-2xl border border-surface-200/80 bg-white p-6 sm:p-8">
              <div className="flex items-center gap-3 mb-1.5">
                <div className="w-10 h-10 rounded-xl bg-navy-800/[0.06] flex items-center justify-center">
                  <svg className="w-5 h-5 text-navy-800" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
                  </svg>
                </div>
                <div>
                  <h3 className="text-[16px] font-bold text-navy-900">Target CGPA</h3>
                  <p className="text-[13px] text-surface-400">Your academic goal on the 5.0 PAU scale.</p>
                </div>
              </div>

              <div className="mt-6 max-w-lg">
                {/* Number input + classification display */}
                <div className="flex items-center gap-4 mb-5">
                  <div className="relative">
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      max="5.0"
                      value={targetCGPA}
                      onChange={(e) => {
                        const v = e.target.value
                        if (v === '' || (parseFloat(v) >= 0 && parseFloat(v) <= 5.0)) {
                          setTargetCGPA(v)
                        }
                      }}
                      className="w-[140px] px-4 py-3 rounded-xl border border-surface-200 bg-surface-50 text-[16px] font-mono font-semibold text-navy-900 placeholder:text-surface-300 focus:outline-none focus:ring-2 focus:ring-navy-200 focus:border-navy-400 focus:bg-white transition-all"
                      placeholder="4.50"
                    />
                    <span className="absolute right-3 top-1/2 -translate-y-1/2 text-[12px] text-surface-400 font-medium pointer-events-none">/ 5.0</span>
                  </div>
                  {targetClassification && targetCGPA && (
                    <span className={`inline-flex items-center px-3 py-1.5 rounded-full text-[12px] font-semibold ${targetClassification.bg} ${targetClassification.color} ${targetClassification.border} border`}>
                      {targetClassification.label}
                    </span>
                  )}
                  {targetCGPA && (parseFloat(targetCGPA) < 0 || parseFloat(targetCGPA) > 5.0 || isNaN(parseFloat(targetCGPA))) && (
                    <span className="text-[11px] text-red-500 font-medium">Must be 0.00 – 5.00</span>
                  )}
                </div>

                {/* Visual scale bar */}
                <div className="relative">
                  {/* Track */}
                  <div className="h-2 bg-surface-100 rounded-full overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all duration-500 ease-out"
                      style={{
                        width: `${cgpaSliderPct}%`,
                        background: 'linear-gradient(90deg, #DC2626 0%, #D97706 30%, #f5b731 48%, #2563EB 70%, #059669 90%)',
                      }}
                    />
                  </div>

                  {/* Thumb indicator */}
                  {targetCGPA && (
                    <div
                      className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 w-4 h-4 rounded-full bg-white border-2 border-navy-800 shadow-md transition-all duration-500 ease-out"
                      style={{ left: `${cgpaSliderPct}%` }}
                    />
                  )}

                  {/* Scale classification labels */}
                  <div className="relative mt-3 h-5">
                    {SCALE_MARKS.filter(m => m.label).map((mark) => (
                      <div
                        key={mark.value}
                        className="absolute -translate-x-1/2 flex flex-col items-center"
                        style={{ left: `${(mark.value / 5.0) * 100}%` }}
                      >
                        <div className="w-px h-2 bg-surface-300 mb-0.5" />
                        <span className="text-[10px] font-semibold text-surface-400 whitespace-nowrap">{mark.label}</span>
                      </div>
                    ))}
                    {/* 0 and 5.0 end labels */}
                    <div className="absolute left-0 flex flex-col items-center" style={{ transform: 'translateX(0)' }}>
                      <div className="w-px h-2 bg-surface-300 mb-0.5" />
                      <span className="text-[10px] font-medium text-surface-300 font-mono">0.0</span>
                    </div>
                    <div className="absolute right-0 flex flex-col items-center" style={{ transform: 'translateX(0)' }}>
                      <div className="w-px h-2 bg-surface-300 mb-0.5" />
                      <span className="text-[10px] font-medium text-surface-300 font-mono">5.0</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Message */}
            {prefMessage && (
              <div className={`flex items-center gap-2.5 p-3.5 rounded-xl text-[13px] font-medium ${
                prefMessage.type === 'success'
                  ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                  : 'bg-red-50 text-red-700 border border-red-200'
              }`}>
                {prefMessage.type === 'success' ? (
                  <svg className="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                ) : (
                  <svg className="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
                  </svg>
                )}
                {prefMessage.text}
              </div>
            )}

            {/* Save button */}
            <button onClick={handleSavePreferences} disabled={prefLoading}
              className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-navy-800 text-white text-[13px] font-semibold hover:bg-navy-900 transition-all disabled:opacity-40 disabled:cursor-not-allowed shadow-sm hover:shadow-md">
              {prefLoading ? (
                <>
                  <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  Saving...
                </>
              ) : (
                <>
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                  </svg>
                  Save Preferences
                </>
              )}
            </button>
          </div>
        )}

        {/* ══════════ DANGER ZONE ══════════ */}
        <div className="mt-16 pt-8 border-t border-surface-200/60 animate-fade-up-3">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 max-w-xl">
            <div>
              <h4 className="text-[13px] font-semibold text-surface-400">Sign Out</h4>
              <p className="text-[12px] text-surface-300 mt-0.5">End your current session on this device.</p>
            </div>
            <button
              onClick={handleLogout}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl border border-red-200 text-[13px] font-semibold text-red-500 hover:bg-red-50 hover:border-red-300 transition-all flex-shrink-0"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
                <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 9V5.25A2.25 2.25 0 0013.5 3h-6a2.25 2.25 0 00-2.25 2.25v13.5A2.25 2.25 0 007.5 21h6a2.25 2.25 0 002.25-2.25V15m3 0l3-3m0 0l-3-3m3 3H9" />
              </svg>
              Sign out
            </button>
          </div>
        </div>

      </main>
    </div>
  )
}

export default ProfilePage
