import { useState, useEffect } from 'react'
import api from '../services/api'

/* ─── Urgency config ─── */
const urgencyConfig = {
  critical: {
    accent: 'from-red-500 to-rose-500',
    dot: 'bg-red-500',
    bg: 'bg-red-500/[0.04]',
    border: 'border-red-200/60',
    badge: 'bg-red-50 text-red-600 border-red-100',
    label: 'Needs attention',
    cta: 'bg-red-600 hover:bg-red-700 text-white shadow-sm shadow-red-200/50',
    pulse: true,
    icon: (
      <svg className="w-5 h-5 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8">
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
      </svg>
    ),
  },
  high: {
    accent: 'from-amber-500 to-orange-500',
    dot: 'bg-amber-500',
    bg: 'bg-amber-500/[0.03]',
    border: 'border-amber-200/60',
    badge: 'bg-amber-50 text-amber-600 border-amber-100',
    label: 'Heads up',
    cta: 'bg-amber-600 hover:bg-amber-700 text-white shadow-sm shadow-amber-200/50',
    pulse: false,
    icon: (
      <svg className="w-5 h-5 text-amber-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8">
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m0-10.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
      </svg>
    ),
  },
  medium: {
    accent: 'from-sky-500 to-blue-500',
    dot: 'bg-sky-500',
    bg: 'bg-sky-500/[0.03]',
    border: 'border-sky-200/60',
    badge: 'bg-sky-50 text-sky-600 border-sky-100',
    label: 'Suggestion',
    cta: 'bg-navy-800 hover:bg-navy-900 text-white shadow-sm shadow-navy-200/50',
    pulse: false,
    icon: (
      <svg className="w-5 h-5 text-sky-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8">
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 18v-5.25m0 0a6.01 6.01 0 001.5-.189m-1.5.189a6.01 6.01 0 01-1.5-.189m3.75 7.478a12.06 12.06 0 01-4.5 0m3.75 2.383a14.406 14.406 0 01-3 0M14.25 18v-.192c0-.983.658-1.823 1.508-2.316a7.5 7.5 0 10-7.517 0c.85.493 1.509 1.333 1.509 2.316V18" />
      </svg>
    ),
  },
  low: {
    accent: 'from-emerald-500 to-teal-500',
    dot: 'bg-emerald-500',
    bg: 'bg-emerald-500/[0.03]',
    border: 'border-emerald-200/60',
    badge: 'bg-emerald-50 text-emerald-600 border-emerald-100',
    label: 'Tip',
    cta: 'bg-navy-800 hover:bg-navy-900 text-white shadow-sm shadow-navy-200/50',
    pulse: false,
    icon: (
      <svg className="w-5 h-5 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8">
        <path strokeLinecap="round" strokeLinejoin="round" d="M4.26 10.147a60.436 60.436 0 00-.491 6.347A48.627 48.627 0 0112 20.904a48.627 48.627 0 018.232-4.41 60.46 60.46 0 00-.491-6.347m-15.482 0a50.57 50.57 0 00-2.658-.813A59.905 59.905 0 0112 3.493a59.902 59.902 0 0110.399 5.84c-.896.248-1.783.52-2.658.814m-15.482 0A50.697 50.697 0 0112 13.489a50.702 50.702 0 017.74-3.342" />
      </svg>
    ),
  },
  none: {
    accent: 'from-surface-300 to-surface-400',
    dot: 'bg-surface-300',
    bg: 'bg-surface-50',
    border: 'border-surface-200/80',
    badge: 'bg-surface-100 text-surface-400 border-surface-200',
    label: 'Info',
    cta: 'bg-navy-800 hover:bg-navy-900 text-white',
    pulse: false,
    icon: (
      <svg className="w-5 h-5 text-surface-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8">
        <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z" />
      </svg>
    ),
  },
}

export default function SmartStudyTriggerBanner({ onOpenSmartStudy }) {
  const [triggerData, setTriggerData] = useState(null)
  const [isVisible, setIsVisible] = useState(true)
  const [isDismissed, setIsDismissed] = useState(false)
  const [showAll, setShowAll] = useState(false)

  useEffect(() => { loadTriggers() }, [])

  const loadTriggers = async () => {
    try {
      const r = await api.get('/api/v1/smartstudy/triggers')
      setTriggerData(r.data)
      if (sessionStorage.getItem('smartstudy_dismissed')) setIsDismissed(true)
    } catch (e) {
      console.error('Error loading SmartStudy triggers:', e)
    }
  }

  const handleDismiss = () => {
    setIsVisible(false)
    setIsDismissed(true)
    sessionStorage.setItem('smartstudy_dismissed', 'true')
  }

  const handleOpenSmartStudy = (suggestedPrompt) => {
    onOpenSmartStudy?.(suggestedPrompt)
    setIsVisible(false)
  }

  if (!triggerData || !triggerData.should_trigger || isDismissed || !isVisible) return null

  const { urgency, primary_trigger, triggers, trigger_count } = triggerData
  const cfg = urgencyConfig[urgency] || urgencyConfig.none

  return (
    <div className={`relative rounded-2xl border ${cfg.border} ${cfg.bg} overflow-hidden mb-5 animate-fade-up`}>
      {/* Left accent bar */}
      <div className={`absolute left-0 top-0 bottom-0 w-1 bg-gradient-to-b ${cfg.accent}`} />

      {/* Pulse glow for critical */}
      {cfg.pulse && (
        <div className="absolute inset-0 rounded-2xl animate-pulse opacity-[0.03] bg-red-500" />
      )}

      <div className="relative px-5 py-4">
        <div className="flex items-start gap-3.5">
          {/* Icon */}
          <div className="flex-shrink-0 mt-0.5">
            <div className="w-9 h-9 rounded-xl bg-white flex items-center justify-center shadow-sm border border-surface-100">
              {cfg.icon}
            </div>
          </div>

          {/* Content */}
          <div className="flex-1 min-w-0">
            {/* Title row */}
            <div className="flex items-start gap-2 mb-1">
              <h3 className="text-[14px] font-bold text-navy-900 leading-snug">
                {primary_trigger?.title || 'SmartStudy Recommendation'}
              </h3>
              <span className={`flex-shrink-0 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider rounded-md border ${cfg.badge}`}>
                {cfg.label}
              </span>
            </div>

            {/* Message */}
            <p className="text-[12px] text-surface-400 leading-relaxed mb-3">
              {primary_trigger?.message || 'Get personalized help with your academics.'}
            </p>

            {/* Multiple triggers expandable */}
            {trigger_count > 1 && (
              <div className="mb-3">
                <button
                  onClick={() => setShowAll(!showAll)}
                  className="flex items-center gap-1.5 text-[11px] font-semibold text-navy-600 hover:text-navy-800 transition-colors"
                >
                  <svg className={`w-3 h-3 transition-transform duration-200 ${showAll ? 'rotate-90' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
                  </svg>
                  {trigger_count - 1} more area{trigger_count > 2 ? 's' : ''} flagged
                </button>

                {showAll && (
                  <div className="mt-2 pl-1 space-y-1.5">
                    {triggers.slice(1).map((t, i) => (
                      <div
                        key={i}
                        onClick={() => handleOpenSmartStudy(t.suggested_prompt)}
                        className="flex items-center gap-2 p-2 rounded-lg hover:bg-white/60 cursor-pointer transition-colors group"
                      >
                        <span className={`w-1.5 h-1.5 rounded-full ${cfg.dot} flex-shrink-0`} />
                        <span className="text-[12px] font-medium text-navy-800 group-hover:text-navy-900">{t.title}</span>
                        <svg className="w-3 h-3 text-surface-300 group-hover:text-navy-500 ml-auto opacity-0 group-hover:opacity-100 transition-all" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                          <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
                        </svg>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* CTA */}
            <button
              onClick={() => handleOpenSmartStudy(primary_trigger?.suggested_prompt)}
              className={`inline-flex items-center gap-2 px-4 py-2 rounded-lg text-[12px] font-semibold transition-all duration-200 ${cfg.cta}`}
            >
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z" />
              </svg>
              Get AI Help
            </button>
          </div>

          {/* Dismiss */}
          <button
            onClick={handleDismiss}
            className="flex-shrink-0 p-1 rounded-md text-surface-300 hover:text-surface-400 hover:bg-surface-100 transition-all"
            aria-label="Dismiss"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  )
}
