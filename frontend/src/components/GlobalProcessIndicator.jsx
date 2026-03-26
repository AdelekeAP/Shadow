import { useSmartStudy } from '../contexts/SmartStudyContext'
import { useNavigate, useLocation } from 'react-router-dom'

/**
 * GlobalProcessIndicator — shows a floating pill when a study plan
 * is generating in the background (user navigated away from SmartStudy).
 * Clicking it navigates back to SmartStudy.
 */
export default function GlobalProcessIndicator() {
  const { generating } = useSmartStudy()
  const location = useLocation()
  const navigate = useNavigate()

  // Only show when generating AND not on SmartStudy page (it has its own overlay)
  if (!generating || location.pathname === '/smartstudy') return null

  return (
    <button
      onClick={() => navigate('/smartstudy')}
      className="fixed bottom-6 right-6 z-50 flex items-center gap-2.5 bg-navy-900 text-white pl-3.5 pr-4 py-2.5 rounded-2xl shadow-lg shadow-navy-900/30 hover:bg-navy-800 transition-all group animate-fade-up-0"
      title="Study plan generating — click to view"
    >
      {/* Pulsing dot */}
      <span className="relative flex h-2.5 w-2.5">
        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
        <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-400" />
      </span>

      <div className="flex flex-col items-start">
        <span className="text-[12px] font-semibold leading-tight">Generating Study Plan</span>
        <span className="text-[10px] text-white/50 leading-tight">Tap to view progress</span>
      </div>

      {/* Arrow */}
      <svg className="w-3.5 h-3.5 text-white/40 group-hover:text-white/70 group-hover:translate-x-0.5 transition-all" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
        <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
      </svg>
    </button>
  )
}
