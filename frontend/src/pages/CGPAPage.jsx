import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import CGPADashboard from '../components/CGPADashboard'
import WhatIfCalculator from '../components/WhatIfCalculator'
import NotificationBell from '../components/NotificationBell'
import { exportCGPApdf, exportCGPAxlsx } from '../services/api'

export default function CGPAPage() {
  const navigate = useNavigate()
  const { user } = useAuth()
  const [showWhatIf, setShowWhatIf] = useState(false)
  const [exporting, setExporting] = useState(null)
  const [toast, setToast] = useState(null)

  useEffect(() => {
    if (!toast) return
    const t = setTimeout(() => setToast(null), 5000)
    return () => clearTimeout(t)
  }, [toast])

  const handleExportPdf = async () => {
    setExporting('pdf')
    try {
      const response = await exportCGPApdf()

      // Extract filename from Content-Disposition header
      const disposition = response.headers['content-disposition']
      const filenameMatch = disposition?.match(/filename="(.+)"/)
      const filename = filenameMatch ? filenameMatch[1] : 'shadow-cgpa.pdf'

      // Create download
      const url = URL.createObjectURL(response.data)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      document.body.appendChild(a)
      a.click()
      a.remove()
      URL.revokeObjectURL(url)
    } catch (error) {
      console.error('Export PDF failed:', error)
      setToast({ message: 'Failed to export PDF. Please try again.', type: 'error' })
    } finally {
      setExporting(null)
    }
  }

  const handleExportXlsx = async () => {
    setExporting('xlsx')
    try {
      const response = await exportCGPAxlsx()

      const disposition = response.headers['content-disposition']
      const filenameMatch = disposition?.match(/filename="(.+)"/)
      const filename = filenameMatch ? filenameMatch[1] : 'shadow-cgpa.xlsx'

      const url = URL.createObjectURL(response.data)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      document.body.appendChild(a)
      a.click()
      a.remove()
      URL.revokeObjectURL(url)
    } catch (error) {
      console.error('Export Excel failed:', error)
      setToast({ message: 'Failed to export Excel file. Please try again.', type: 'error' })
    } finally {
      setExporting(null)
    }
  }

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
                { label: 'CGPA', path: '/cgpa', active: true },
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
          <div className="flex items-center gap-2">
            <NotificationBell />
            <button
              onClick={() => navigate('/profile')}
              className="flex items-center gap-1.5 px-2 py-1 rounded-lg hover:bg-surface-100 transition-colors group"
              title="View profile"
            >
              <div className="w-7 h-7 rounded-full bg-navy-100 flex items-center justify-center group-hover:bg-navy-200 transition-colors">
                <span className="text-[11px] font-bold text-navy-800">
                  {user?.full_name ? user.full_name.split(' ').map(n => n[0]).join('').slice(0, 2) : 'U'}
                </span>
              </div>
              <span className="hidden sm:inline text-[13px] font-medium text-surface-400 group-hover:text-navy-800 transition-colors">{user?.full_name?.split(' ')[0] || 'User'}</span>
            </button>
          </div>
        </div>
      </nav>

      {/* ══════════ HERO HEADER ══════════ */}
      <div className="border-b border-surface-200/60 bg-white hero-atmosphere">
        <div className="mx-auto max-w-[1360px] px-5 py-8 relative">
          <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4">
            <div>
              <div className="flex items-center gap-2.5 mb-2">
                <h1 className="font-display text-[28px] font-bold text-navy-900 tracking-tight">CGPA Analytics</h1>
                <span className="px-2 py-0.5 rounded-md bg-emerald-500/[0.08] border border-emerald-200/40 text-[10px] font-bold text-emerald-700 uppercase tracking-wider">5.0 Scale</span>
              </div>
              <p className="text-[13px] text-surface-400 mt-1">Track performance, predict outcomes, and plan your academic future</p>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={handleExportPdf}
                disabled={exporting}
                className="flex items-center gap-1.5 px-3 py-2.5 border border-surface-200 hover:border-surface-300 bg-white hover:bg-surface-50 text-navy-800 rounded-xl text-[13px] font-semibold transition-all disabled:opacity-50"
              >
                {exporting === 'pdf' ? (
                  <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg>
                ) : (
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2"><path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" /></svg>
                )}
                Export PDF
              </button>
              <button
                onClick={handleExportXlsx}
                disabled={exporting}
                className="flex items-center gap-1.5 px-3 py-2.5 border border-surface-200 hover:border-surface-300 bg-white hover:bg-surface-50 text-navy-800 rounded-xl text-[13px] font-semibold transition-all disabled:opacity-50"
              >
                {exporting === 'xlsx' ? (
                  <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg>
                ) : (
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2"><path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" /></svg>
                )}
                Export Excel
              </button>
              <button
                onClick={() => setShowWhatIf(true)}
                className="flex items-center gap-2 px-4 py-2.5 bg-navy-800 hover:bg-navy-900 text-white rounded-xl text-[13px] font-semibold transition-all shadow-sm"
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 15.75V18m-7.5-6.75h.008v.008H8.25v-.008Zm0 2.25h.008v.008H8.25V13.5Zm0 2.25h.008v.008H8.25v-.008Zm0 2.25h.008v.008H8.25V18Zm2.498-6.75h.007v.008h-.007v-.008Zm0 2.25h.007v.008h-.007V13.5Zm0 2.25h.007v.008h-.007v-.008Zm0 2.25h.007v.008h-.007V18Zm2.504-6.75h.008v.008h-.008v-.008Zm0 2.25h.008v.008h-.008V13.5Zm0 2.25h.008v.008h-.008v-.008Zm0 2.25h.008v.008h-.008V18Zm2.498-6.75h.008v.008h-.008v-.008Zm0 2.25h.008v.008h-.008V13.5ZM8.25 6h7.5v2.25h-7.5V6ZM12 2.25c-1.892 0-3.758.11-5.593.322C5.307 2.7 4.5 3.65 4.5 4.757V19.5a2.25 2.25 0 0 0 2.25 2.25h10.5a2.25 2.25 0 0 0 2.25-2.25V4.757c0-1.108-.806-2.057-1.907-2.185A48.507 48.507 0 0 0 12 2.25Z" />
                </svg>
                What-If Calculator
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* ══════════ CONTENT ══════════ */}
      <div className="mx-auto max-w-[1360px] px-5 py-6">
        {/* ── SmartStudy CTA when below target ── */}
        {user?.current_cgpa && user?.target_cgpa && user.current_cgpa < user.target_cgpa && (
          <div className="mb-6 flex items-center gap-3 rounded-xl border border-amber-200/60 bg-amber-50/50 px-5 py-4">
            <div className="w-9 h-9 rounded-lg bg-amber-100 flex items-center justify-center flex-shrink-0">
              <svg className="w-5 h-5 text-amber-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8">
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" />
              </svg>
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-[13px] font-semibold text-amber-900">
                Your CGPA ({user.current_cgpa.toFixed(2)}) is below your target ({user.target_cgpa.toFixed(2)})
              </p>
              <p className="text-[12px] text-amber-700/80 mt-0.5">Create an AI-powered study plan to get back on track.</p>
            </div>
            <button
              onClick={() => navigate('/smartstudy')}
              className="flex-shrink-0 flex items-center gap-1.5 px-4 py-2 bg-amber-600 hover:bg-amber-700 text-white rounded-lg text-[12px] font-semibold transition-colors"
            >
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z" />
              </svg>
              Study Plan
            </button>
          </div>
        )}
        <CGPADashboard />

        {/* ── PAU Grading Reference ── */}
        <div className="mt-8 rounded-2xl border border-surface-200/60 bg-white p-6 relative overflow-hidden hero-atmosphere">
          <h3 className="text-[14px] font-semibold text-navy-900 mb-4">PAU Grading Reference</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <p className="text-[11px] font-semibold uppercase tracking-wider text-surface-400 mb-2.5">Grading Scale</p>
              <div className="space-y-1.5">
                {[
                  { grade: 'A', point: '5.0', range: '70–100', cls: 'bg-emerald-500' },
                  { grade: 'B', point: '4.0', range: '60–69', cls: 'bg-blue-500' },
                  { grade: 'C', point: '3.0', range: '50–59', cls: 'bg-amber-500' },
                  { grade: 'D', point: '2.0', range: '45–49', cls: 'bg-orange-500' },
                  { grade: 'E', point: '1.0', range: '40–44', cls: 'bg-red-400' },
                  { grade: 'F', point: '0.0', range: '0–39', cls: 'bg-red-600' },
                ].map(g => (
                  <div key={g.grade} className="flex items-center gap-2.5">
                    <span className={`w-6 h-6 rounded-md ${g.cls} text-white text-[11px] font-bold flex items-center justify-center`}>{g.grade}</span>
                    <span className="text-[12px] text-navy-800 font-mono w-8">{g.point}</span>
                    <span className="text-[11px] text-surface-400">{g.range}</span>
                  </div>
                ))}
              </div>
            </div>
            <div>
              <p className="text-[11px] font-semibold uppercase tracking-wider text-surface-400 mb-2.5">Degree Classifications</p>
              <div className="space-y-1.5">
                {[
                  { name: 'First Class', range: '4.50 – 5.00', cls: 'border-emerald-300 bg-emerald-50 text-emerald-700' },
                  { name: 'Second Class Upper', range: '3.50 – 4.49', cls: 'border-blue-300 bg-blue-50 text-blue-700' },
                  { name: 'Second Class Lower', range: '2.40 – 3.49', cls: 'border-amber-300 bg-amber-50 text-amber-700' },
                  { name: 'Third Class', range: '1.50 – 2.39', cls: 'border-orange-300 bg-orange-50 text-orange-700' },
                  { name: 'Pass', range: '1.00 – 1.49', cls: 'border-red-200 bg-red-50 text-red-600' },
                ].map(c => (
                  <div key={c.name} className={`flex items-center justify-between px-3 py-1.5 rounded-lg border ${c.cls}`}>
                    <span className="text-[12px] font-semibold">{c.name}</span>
                    <span className="text-[11px] font-mono">{c.range}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ══════════ WHAT-IF MODAL ══════════ */}
      {showWhatIf && <WhatIfCalculator onClose={() => setShowWhatIf(false)} />}

      {/* ── Toast notification ── */}
      {toast && (
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-[60] animate-fade-up">
          <div className="flex items-center gap-2.5 px-4 py-3 rounded-xl shadow-lg border backdrop-blur-sm bg-red-50/95 border-red-200/80 text-red-700">
            <svg className="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
            </svg>
            <p className="text-[13px] font-medium">{toast.message}</p>
            <button onClick={() => setToast(null)} className="p-0.5 rounded-md hover:bg-black/5 transition-colors ml-1">
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
