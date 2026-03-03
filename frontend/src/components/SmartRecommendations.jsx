/**
 * Smart Recommendations — "Intelligence Brief" design
 * Personalized AI insights rendered as a premium editorial report
 */
import { useState, useEffect } from 'react'
import {
  getEffectivenessSummary,
  getEffectivenessByLearningStyle,
  getMoodEffectivenessCorrelation,
  getTopicEffectiveness,
  updateUserPreferences,
  createTask
} from '../services/api'

/* ── Compact SVG icon kit (16×16 for cards) ── */
const icons = {
  eye: <svg className="w-[18px] h-[18px]" fill="none" stroke="currentColor" strokeWidth={1.6} viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z" /><path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /></svg>,
  headphone: <svg className="w-[18px] h-[18px]" fill="none" stroke="currentColor" strokeWidth={1.6} viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M19.114 5.636a9 9 0 010 12.728M16.463 8.288a5.25 5.25 0 010 7.424M6.75 8.25l4.72-4.72a.75.75 0 011.28.53v15.88a.75.75 0 01-1.28.53l-4.72-4.72H4.51c-.88 0-1.704-.507-1.938-1.354A9.01 9.01 0 012.25 12c0-.83.112-1.633.322-2.396C2.806 8.756 3.63 8.25 4.51 8.25H6.75z" /></svg>,
  book: <svg className="w-[18px] h-[18px]" fill="none" stroke="currentColor" strokeWidth={1.6} viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 016-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0018 18a8.967 8.967 0 00-6 2.292m0-14.25v14.25" /></svg>,
  hand: <svg className="w-[18px] h-[18px]" fill="none" stroke="currentColor" strokeWidth={1.6} viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M10.05 4.575a1.575 1.575 0 10-3.15 0v3m3.15-3v-1.5a1.575 1.575 0 013.15 0v1.5m-3.15 0l-.075 5.925m3.075-5.925a1.575 1.575 0 013.15 0v1.5m0 0v3.375c0 .621.504 1.125 1.125 1.125h.426c.795 0 1.467.573 1.596 1.36l.386 2.317c.134.802-.273 1.59-1.001 1.938A13.77 13.77 0 0112 21a13.77 13.77 0 01-5.632-1.189 1.655 1.655 0 01-1.001-1.938l.386-2.317c.129-.787.801-1.36 1.596-1.36h.426c.621 0 1.125-.504 1.125-1.125V7.575" /></svg>,
  bulb: <svg className="w-[18px] h-[18px]" fill="none" stroke="currentColor" strokeWidth={1.6} viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M12 18v-5.25m0 0a6.01 6.01 0 001.5-.189m-1.5.189a6.01 6.01 0 01-1.5-.189m3.75 7.478a12.06 12.06 0 01-4.5 0m3.75 2.383a14.406 14.406 0 01-3 0M14.25 18v-.192c0-.983.658-1.823 1.508-2.316a7.5 7.5 0 10-7.517 0c.85.493 1.509 1.333 1.509 2.316V18" /></svg>,
  target: <svg className="w-[18px] h-[18px]" fill="none" stroke="currentColor" strokeWidth={1.6} viewBox="0 0 24 24"><circle cx="12" cy="12" r="9" /><circle cx="12" cy="12" r="5" /><circle cx="12" cy="12" r="1" fill="currentColor" /></svg>,
  alert: <svg className="w-[18px] h-[18px]" fill="none" stroke="currentColor" strokeWidth={1.6} viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" /></svg>,
  trophy: <svg className="w-[18px] h-[18px]" fill="none" stroke="currentColor" strokeWidth={1.6} viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M16.5 18.75h-9m9 0a3 3 0 013 3h-15a3 3 0 013-3m9 0v-4.5A3.375 3.375 0 0019.875 10.875H21A2.25 2.25 0 0023.25 8.625v-1.5A2.25 2.25 0 0021 4.875h-1.125A3.375 3.375 0 0016.5 1.5h-9A3.375 3.375 0 004.125 4.875H3A2.25 2.25 0 00.75 7.125v1.5A2.25 2.25 0 003 10.875h1.125A3.375 3.375 0 007.5 14.25v4.5" /></svg>,
  bolt: <svg className="w-[18px] h-[18px]" fill="none" stroke="currentColor" strokeWidth={1.6} viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z" /></svg>,
  flame: <svg className="w-[18px] h-[18px]" fill="none" stroke="currentColor" strokeWidth={1.6} viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M15.362 5.214A8.252 8.252 0 0112 21 8.25 8.25 0 016.038 7.048 8.287 8.287 0 009 9.6a8.983 8.983 0 013.361-6.867 8.21 8.21 0 003 2.48z" /></svg>,
  grad: <svg className="w-[18px] h-[18px]" fill="none" stroke="currentColor" strokeWidth={1.6} viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M4.26 10.147a60.436 60.436 0 00-.491 6.347A48.627 48.627 0 0112 20.904a48.627 48.627 0 018.232-4.41 60.46 60.46 0 00-.491-6.347m-15.482 0a50.57 50.57 0 00-2.658-.813A59.905 59.905 0 0112 3.493a59.902 59.902 0 0110.399 5.84c-.896.248-1.783.52-2.658.814m-15.482 0A50.697 50.697 0 0112 13.489a50.702 50.702 0 017.74-3.342M6.75 15a.75.75 0 100-1.5.75.75 0 000 1.5zm0 0v-3.675A55.378 55.378 0 0112 8.443m-7.007 11.55A5.981 5.981 0 006.75 15.75v-1.5" /></svg>,
  check: <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={2.5} viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" /></svg>,
  arrow: <svg className="w-3 h-3" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M13 7l5 5m0 0l-5 5m5-5H6" /></svg>,
}

function pickIcon(rec) {
  const styleKey = rec.actionData?.preferred_learning_style
  const map = {
    learning_style: { visual: 'eye', audio: 'headphone', reading: 'book', kinesthetic: 'hand' },
  }
  if (rec.type === 'learning_style' && styleKey && map.learning_style[styleKey]) return icons[map.learning_style[styleKey]]
  const typeMap = { tip: 'bulb', mood: rec.id?.includes('avoid') ? 'alert' : 'target', engagement: 'target', achievement: 'trophy', focus: 'target', motivation: 'flame', topic: 'book', goal: 'grad' }
  return icons[typeMap[rec.type]] || icons.bulb
}

/* ── Priority visual config ── */
const prioConfig = {
  high: {
    accent: 'border-l-amber-400',
    iconBg: 'bg-amber-500/10',
    iconFg: 'text-amber-600',
    tag: 'bg-amber-500 text-white',
    cardBg: 'bg-gradient-to-r from-amber-50/60 via-white to-white',
  },
  medium: {
    accent: 'border-l-navy-300',
    iconBg: 'bg-navy-800/[0.05]',
    iconFg: 'text-navy-700',
    tag: null,
    cardBg: 'bg-white',
  },
  low: {
    accent: 'border-l-emerald-300',
    iconBg: 'bg-emerald-500/[0.08]',
    iconFg: 'text-emerald-600',
    tag: null,
    cardBg: 'bg-gradient-to-r from-emerald-50/40 via-white to-white',
  },
}

/* ═══════════════════════════════════════
   SmartRecommendations
   ═══════════════════════════════════════ */
export default function SmartRecommendations({ onClose, user }) {
  const [loading, setLoading] = useState(true)
  const [recommendations, setRecommendations] = useState([])
  const [approvedActions, setApprovedActions] = useState([])
  const [processingId, setProcessingId] = useState(null)
  const [entering, setEntering] = useState(true)
  const [dismissedIds, setDismissedIds] = useState([])
  const [snoozedItems, setSnoozedItems] = useState(() => {
    // Load persisted 24h snoozes from localStorage
    try {
      const stored = JSON.parse(localStorage.getItem('shadow_snoozed_recs') || '{}')
      const now = Date.now()
      // Clean up expired snoozes
      const valid = {}
      for (const [id, expiry] of Object.entries(stored)) {
        if (expiry > now) valid[id] = expiry
      }
      if (Object.keys(valid).length !== Object.keys(stored).length) {
        localStorage.setItem('shadow_snoozed_recs', JSON.stringify(valid))
      }
      return valid
    } catch { return {} }
  })
  const [snoozeMenuId, setSnoozeMenuId] = useState(null)
  const [snoozeToast, setSnoozeToast] = useState(null)

  useEffect(() => {
    generateRecommendations()
    requestAnimationFrame(() => requestAnimationFrame(() => setEntering(false)))
  }, [])

  useEffect(() => {
    const handleKeyDown = (e) => { if (e.key === 'Escape') onClose() }
    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [])

  /* ─── Data generation (unchanged logic) ─── */
  const generateRecommendations = async () => {
    setLoading(true)
    try {
      const [summary, styleData, moodData, topicData] = await Promise.all([
        getEffectivenessSummary(),
        getEffectivenessByLearningStyle(),
        getMoodEffectivenessCorrelation(),
        getTopicEffectiveness()
      ])

      const recs = []

      if (styleData?.by_learning_style && Object.keys(styleData.by_learning_style).length > 0) {
        const styles = Object.entries(styleData.by_learning_style)
        const bestStyle = styles.sort((a, b) => b[1].avg_completion - a[1].avg_completion)[0]
        const worstStyle = styles.sort((a, b) => a[1].avg_completion - b[1].avg_completion)[0]

        if (bestStyle && bestStyle[1].avg_completion > 50) {
          recs.push({
            id: 'learning_style_best', type: 'learning_style', priority: 'high',
            title: `You learn best with ${fmt(bestStyle[0])} content`,
            description: `Your ${bestStyle[1].avg_completion}% completion rate shows ${fmt(bestStyle[0])} resources work best for you.`,
            action: `Set ${fmt(bestStyle[0])} as preferred`, actionData: { preferred_learning_style: bestStyle[0] },
            impact: 'Prioritizes this content type in future study plans'
          })
        }
        if (worstStyle && worstStyle[1].avg_completion < 30 && worstStyle[0] !== bestStyle?.[0]) {
          recs.push({
            id: 'learning_style_improve', type: 'tip', priority: 'medium',
            title: `Consider alternatives for ${fmt(worstStyle[0])} content`,
            description: `${worstStyle[1].avg_completion}% completion with ${fmt(worstStyle[0])} materials suggests they may not suit you.`,
            action: 'Acknowledge', actionData: null,
            impact: 'We\'ll reduce these resource types in future plans'
          })
        }
      }

      if (moodData?.effectiveness_by_mood && Object.keys(moodData.effectiveness_by_mood).length > 0) {
        const moods = Object.entries(moodData.effectiveness_by_mood)
        const bestMood = moods.sort((a, b) => b[1].avg_improvement - a[1].avg_improvement)[0]
        const worstMood = moods.sort((a, b) => a[1].avg_improvement - b[1].avg_improvement)[0]

        if (bestMood && bestMood[1].avg_improvement > 5) {
          recs.push({
            id: 'mood_optimal', type: 'mood', priority: 'high',
            title: `${bestMood[1].avg_improvement}% better when ${bestMood[0]}`,
            description: `Schedule important sessions when feeling ${bestMood[0]} for maximum effectiveness.`,
            action: 'Create mood-based reminder', actionData: { create_mood_trigger: bestMood[0] },
            impact: 'We\'ll suggest studying when you log this mood'
          })
        }
        if (worstMood && worstMood[1].avg_improvement < -5) {
          recs.push({
            id: 'mood_avoid', type: 'mood', priority: 'medium',
            title: `Avoid heavy study when ${worstMood[0]}`,
            description: `Performance drops ${Math.abs(worstMood[1].avg_improvement)}% when ${worstMood[0]}. Consider lighter tasks or breaks.`,
            action: 'Acknowledge', actionData: null,
            impact: 'We\'ll suggest breaks instead of intense study'
          })
        }
      }

      if (summary?.engagement) {
        const { engagement_rate: er = 0, resources_completed: rc = 0, total_resources: tr = 0 } = summary.engagement
        if (er < 50 && tr > 5) {
          recs.push({
            id: 'engagement_low', type: 'engagement', priority: 'high',
            title: 'Resource engagement could improve',
            description: `You've engaged with ${er}% of study resources. Smaller goals may help.`,
            action: 'Use smaller chunks', actionData: { study_chunk_size: 'small' },
            impact: 'Shorter, more focused sessions in future plans'
          })
        }
        if (rc > 10 && er > 70) {
          recs.push({
            id: 'engagement_great', type: 'achievement', priority: 'low',
            title: 'Excellent engagement — you\'re on track',
            description: `${rc} resources completed with ${er}% engagement. Outstanding work.`,
            action: 'Acknowledge', actionData: null, impact: null
          })
        }
      }

      if (summary?.summary) {
        const { total_study_plans: tp = 0, active_study_plans: ap = 0, completed_study_plans: cp = 0 } = summary.summary
        if (ap > 3) {
          recs.push({
            id: 'too_many_plans', type: 'focus', priority: 'high',
            title: 'Focus on fewer plans at once',
            description: `${ap} active plans is a lot. Research shows 1–2 topics yields better retention.`,
            action: 'Help me prioritize', actionData: { prioritize_plans: true },
            impact: 'We\'ll help you focus on the most important topics'
          })
        }
        if (tp > 0 && cp === 0) {
          recs.push({
            id: 'no_completions', type: 'motivation', priority: 'medium',
            title: 'Complete your first study plan!',
            description: `${tp} plans created but none finished. Start small and build momentum.`,
            action: 'Show easiest plan', actionData: { show_easiest_plan: true },
            impact: 'We\'ll highlight your quickest-to-complete plan'
          })
        }
      }

      if (topicData?.topics?.length > 0) {
        const low = topicData.topics.filter(t => t.avg_completion < 30)
        const high = topicData.topics.filter(t => t.avg_completion > 70)
        if (low.length > 0) {
          recs.push({
            id: `topic_struggle_${low[0].topic}`, type: 'topic', priority: 'medium',
            title: `Need help with ${low[0].topic}?`,
            description: `${low[0].avg_completion}% completion — would you like different resources?`,
            action: 'Find alternatives', actionData: { regenerate_resources: low[0].topic },
            impact: 'We\'ll find new videos and articles for you'
          })
        }
        if (high.length > 0) {
          recs.push({
            id: `topic_mastery_${high[0].topic}`, type: 'achievement', priority: 'low',
            title: `Great progress on ${high[0].topic}!`,
            description: `${high[0].avg_completion}% completion — consider marking as mastered.`,
            action: 'Mark as mastered', actionData: { mark_mastered: high[0].topic },
            impact: 'Removes from active study queue'
          })
        }
      }

      if (user?.target_cgpa && user?.current_cgpa) {
        const gap = user.target_cgpa - user.current_cgpa
        if (gap > 0.5) {
          recs.push({
            id: 'cgpa_gap', type: 'goal', priority: 'high',
            title: `${gap.toFixed(2)} points to target CGPA`,
            description: `Improve ${gap.toFixed(2)} points to reach ${user.target_cgpa.toFixed(2)}. Let's plan.`,
            action: 'Create improvement plan', actionData: { create_improvement_plan: true },
            impact: 'We\'ll identify courses where you can gain the most'
          })
        }
      }

      const order = { high: 0, medium: 1, low: 2 }
      recs.sort((a, b) => order[a.priority] - order[b.priority])
      setRecommendations(recs)
    } catch (err) { console.error('Error generating recommendations:', err) }
    finally { setLoading(false) }
  }

  const handleApprove = async (rec) => {
    setProcessingId(rec.id)
    try {
      if (rec.actionData?.preferred_learning_style) {
        await updateUserPreferences({ preferred_learning_style: rec.actionData.preferred_learning_style })
      }
      setApprovedActions(prev => [...prev, rec.id])
      setTimeout(() => setRecommendations(prev => prev.filter(r => r.id !== rec.id)), 600)
    } catch (err) { console.error('Error applying recommendation:', err) }
    finally { setProcessingId(null) }
  }

  const dismissRec = (id) => {
    setDismissedIds(prev => [...prev, id])
  }
  const snoozeRec = (id, duration) => {
    const expiry = duration === 'session' ? Infinity : Date.now() + 24 * 60 * 60 * 1000
    setSnoozedItems(prev => {
      const next = { ...prev, [id]: expiry }
      if (duration !== 'session') {
        localStorage.setItem('shadow_snoozed_recs', JSON.stringify(
          Object.fromEntries(Object.entries(next).filter(([, v]) => v !== Infinity))
        ))
      }
      return next
    })
    setSnoozeMenuId(null)
    setSnoozeToast(id)
    setTimeout(() => setSnoozeToast(null), 2000)
  }
  const handleClose = () => { setEntering(true); setTimeout(onClose, 220) }

  const visibleRecs = recommendations.filter(r => !dismissedIds.includes(r.id) && !snoozedItems[r.id])
  const snoozedCount = Object.keys(snoozedItems).filter(id => recommendations.some(r => r.id === id)).length
  const dismissedCount = dismissedIds.length
  const highCount = visibleRecs.filter(r => r.priority === 'high').length

  /* ─── Loading state ─── */
  if (loading) {
    return (
      <div className="fixed inset-0 bg-navy-950/40 backdrop-blur-sm flex items-center justify-center z-50 p-4">
        <div className="bg-white rounded-2xl p-10 text-center shadow-2xl max-w-xs w-full">
          {/* Pulsing concentric rings */}
          <div className="relative w-16 h-16 mx-auto mb-5">
            <div className="absolute inset-0 rounded-full border-2 border-navy-200 animate-ping opacity-20" />
            <div className="absolute inset-2 rounded-full border-2 border-navy-300 animate-ping opacity-30" style={{ animationDelay: '0.3s' }} />
            <div className="absolute inset-4 rounded-full border-2 border-navy-400 animate-ping opacity-40" style={{ animationDelay: '0.6s' }} />
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="w-6 h-6 rounded-full bg-navy-800 animate-pulse" />
            </div>
          </div>
          <p className="font-display text-[15px] font-semibold text-navy-900 mb-1">Analyzing patterns</p>
          <p className="text-[12px] text-surface-400">Cross-referencing your learning data...</p>
        </div>
      </div>
    )
  }

  return (
    <div role="dialog" aria-modal="true" aria-label="Smart Recommendations" className={`fixed inset-0 bg-navy-950/50 backdrop-blur-md flex items-center justify-center z-50 p-4 overflow-y-auto transition-opacity duration-250 ${entering ? 'opacity-0' : 'opacity-100'}`}>
      <div className={`bg-white rounded-[20px] shadow-2xl max-w-2xl w-full max-h-[92vh] overflow-hidden flex flex-col transition-all duration-350 ${entering ? 'scale-[0.96] opacity-0 translate-y-3' : 'scale-100 opacity-100 translate-y-0'}`}>

        {/* ═══ Hero header — dark editorial ═══ */}
        <div className="relative overflow-hidden flex-shrink-0">
          {/* Dark gradient base */}
          <div className="absolute inset-0 bg-gradient-to-br from-[#0b1526] via-navy-900 to-[#0d1a2e]" />
          {/* Constellation dots */}
          <div className="absolute inset-0 opacity-[0.06]" style={{
            backgroundImage: 'radial-gradient(circle, rgba(255,255,255,0.9) 1px, transparent 1px)',
            backgroundSize: '24px 24px',
          }} />
          {/* Top-right radial glow */}
          <div className="absolute -top-12 -right-12 w-48 h-48 rounded-full" style={{ background: 'radial-gradient(circle, rgba(59,130,246,0.12) 0%, transparent 70%)' }} />
          {/* Bottom-left warm glow (if high-priority items exist) */}
          {highCount > 0 && (
            <div className="absolute -bottom-8 -left-8 w-40 h-40 rounded-full" style={{ background: 'radial-gradient(circle, rgba(245,158,11,0.10) 0%, transparent 70%)' }} />
          )}

          <div className="relative z-10 px-7 pt-7 pb-5">
            <div className="flex items-start justify-between mb-4">
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <div className="w-6 h-6 rounded-md bg-white/10 flex items-center justify-center">
                    <svg className="w-3.5 h-3.5 text-blue-300" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z" />
                    </svg>
                  </div>
                  <span className="text-[10px] font-semibold uppercase tracking-[0.15em] text-white/30">Intelligence Brief</span>
                </div>
                <h2 className="font-display text-[22px] font-bold text-white leading-tight tracking-tight">Smart Insights</h2>
                <p className="text-[12px] text-white/35 mt-1">Personalized recommendations from your learning data</p>
              </div>
              <button
                onClick={handleClose}
                className="p-2 rounded-xl hover:bg-white/10 transition-colors text-white/30 hover:text-white/60 -mt-1 -mr-1"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Summary pills */}
            <div className="flex items-center gap-2">
              <span className="px-2.5 py-1 rounded-lg bg-white/[0.07] text-[11px] font-semibold text-white/50">
                {visibleRecs.length} insight{visibleRecs.length !== 1 ? 's' : ''}
              </span>
              {highCount > 0 && (
                <span className="px-2.5 py-1 rounded-lg bg-amber-500/20 text-[11px] font-semibold text-amber-300 flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse" />
                  {highCount} important
                </span>
              )}
            </div>
          </div>
        </div>

        {/* ═══ Content — recommendation cards ═══ */}
        <div className="flex-1 overflow-y-auto">
          {visibleRecs.length === 0 ? (
            /* ── Empty state ── */
            <div className="py-20 px-8 text-center">
              <div className="relative w-20 h-20 mx-auto mb-6">
                {/* Soft concentric rings */}
                <div className="absolute inset-0 rounded-full border border-surface-200/60" />
                <div className="absolute inset-3 rounded-full border border-surface-200/40" />
                <div className="absolute inset-6 rounded-full border border-surface-200/20" />
                <div className="absolute inset-0 flex items-center justify-center">
                  <svg className="w-7 h-7 text-surface-300" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
              </div>
              <h3 className="font-display text-[17px] font-semibold text-navy-900 mb-1.5">All clear</h3>
              <p className="text-[13px] text-surface-400 max-w-[260px] mx-auto leading-relaxed">
                No new recommendations right now. Keep studying and check back later.
              </p>
            </div>
          ) : (
            <div className="p-5 space-y-2.5">
              {(dismissedCount > 0 || snoozedCount > 0) && (
                <div className="flex items-center gap-2 mb-1">
                  {dismissedCount > 0 && (
                    <span className="text-[11px] text-surface-400 bg-surface-100 px-2.5 py-1 rounded-lg">
                      {dismissedCount} dismissed
                    </span>
                  )}
                  {snoozedCount > 0 && (
                    <span className="text-[11px] text-surface-400 bg-amber-50 border border-amber-200/60 px-2.5 py-1 rounded-lg">
                      {snoozedCount} snoozed
                    </span>
                  )}
                  <button
                    onClick={() => { setDismissedIds([]); setSnoozedItems({}) }}
                    className="text-[11px] text-navy-600 hover:text-navy-800 font-medium transition-colors"
                  >
                    Show all
                  </button>
                </div>
              )}
              {visibleRecs.map((rec, idx) => {
                const approved = approvedActions.includes(rec.id)
                const processing = processingId === rec.id
                const p = prioConfig[rec.priority] || prioConfig.medium

                return (
                  <div
                    key={rec.id}
                    className={`group relative rounded-xl border-l-[3px] transition-all duration-400 ${p.accent} ${
                      approved ? 'opacity-40 scale-[0.98]' : 'hover:shadow-md'
                    }`}
                    style={{ animationDelay: `${idx * 70}ms` }}
                  >
                    <div className={`${p.cardBg} rounded-r-xl border border-l-0 border-surface-200/70 px-5 py-4`}>
                      <div className="flex items-start gap-3.5">
                        {/* Index number + icon */}
                        <div className="flex-shrink-0 flex flex-col items-center gap-1.5">
                          <span className="font-mono text-[10px] font-bold text-surface-300/80 leading-none">{String(idx + 1).padStart(2, '0')}</span>
                          <div className={`w-9 h-9 rounded-lg ${p.iconBg} flex items-center justify-center ${p.iconFg}`}>
                            {pickIcon(rec)}
                          </div>
                        </div>

                        {/* Body */}
                        <div className="flex-1 min-w-0">
                          <div className="flex items-start justify-between gap-2 mb-1">
                            <h3 className="text-[14px] font-semibold text-navy-900 leading-snug">{rec.title}</h3>
                            <div className="flex items-center gap-1.5 flex-shrink-0">
                              {p.tag && (
                                <span className={`text-[9px] font-bold uppercase tracking-[0.08em] px-2 py-[3px] rounded-md ${p.tag}`}>
                                  Important
                                </span>
                              )}
                              <div className="relative">
                                <button
                                  onClick={() => setSnoozeMenuId(snoozeMenuId === rec.id ? null : rec.id)}
                                  className="p-1 rounded-lg text-surface-300 hover:text-surface-400 hover:bg-surface-100 transition-all"
                                  aria-label="Dismiss or snooze"
                                >
                                  <svg className="w-[14px] h-[14px]" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.75a.75.75 0 110-1.5.75.75 0 010 1.5zM12 12.75a.75.75 0 110-1.5.75.75 0 010 1.5zM12 18.75a.75.75 0 110-1.5.75.75 0 010 1.5z" />
                                  </svg>
                                </button>
                                {snoozeMenuId === rec.id && (
                                  <div className="absolute right-0 top-full mt-1 w-40 bg-white rounded-lg border border-surface-200 shadow-lg z-10 py-1">
                                    <button
                                      onClick={() => { dismissRec(rec.id); setSnoozeMenuId(null) }}
                                      className="w-full text-left px-3 py-2 text-[12px] text-navy-800 hover:bg-surface-50 transition-colors"
                                    >Dismiss</button>
                                    <button
                                      onClick={() => snoozeRec(rec.id, '24h')}
                                      className="w-full text-left px-3 py-2 text-[12px] text-navy-800 hover:bg-surface-50 transition-colors"
                                    >Snooze 24h</button>
                                    <button
                                      onClick={() => snoozeRec(rec.id, 'session')}
                                      className="w-full text-left px-3 py-2 text-[12px] text-navy-800 hover:bg-surface-50 transition-colors"
                                    >Snooze this session</button>
                                  </div>
                                )}
                              </div>
                            </div>
                          </div>
                          <p className="text-[13px] text-surface-400 leading-relaxed mb-2.5">{rec.description}</p>

                          {rec.impact && (
                            <p className="text-[11px] text-surface-300 mb-3 flex items-center gap-1.5 font-medium">
                              {icons.arrow}
                              <span>{rec.impact}</span>
                            </p>
                          )}

                          {/* Actions */}
                          <div className="flex items-center gap-2.5">
                            <button
                              onClick={() => handleApprove(rec)}
                              disabled={processing || approved}
                              className={`px-3.5 py-[7px] rounded-lg text-[12px] font-semibold transition-all flex items-center gap-1.5 ${
                                approved
                                  ? 'bg-emerald-500 text-white'
                                  : processing
                                  ? 'bg-surface-100 text-surface-400 cursor-wait'
                                  : 'bg-navy-800 text-white hover:bg-navy-900 active:scale-[0.97] shadow-sm shadow-navy-900/10'
                              }`}
                            >
                              {approved ? (
                                <>{icons.check} Applied</>
                              ) : processing ? (
                                <><div className="w-3 h-3 border-[1.5px] border-surface-400 border-t-transparent rounded-full animate-spin" /> Applying...</>
                              ) : (
                                <>{icons.check} {rec.action}</>
                              )}
                            </button>
                            <button
                              onClick={() => snoozeRec(rec.id, 'session')}
                              className="px-2.5 py-[7px] text-[12px] font-medium text-surface-300 hover:text-navy-700 hover:bg-surface-50 rounded-lg transition-colors"
                            >
                              Not now
                            </button>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>

        {/* Snooze toast */}
        {snoozeToast && (
          <div className="absolute bottom-16 left-1/2 -translate-x-1/2 px-4 py-2 bg-navy-800 text-white text-[12px] font-semibold rounded-lg shadow-lg animate-fade-in z-20">
            Snoozed — will reappear later
          </div>
        )}

        {/* ═══ Footer ═══ */}
        <div className="flex-shrink-0 px-6 py-3.5 border-t border-surface-100 bg-surface-50/30 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
              <span className="text-[11px] text-surface-400 font-medium">AI-generated from your activity</span>
            </div>
          </div>
          <button
            onClick={handleClose}
            className="px-4 py-1.5 bg-navy-800 text-white rounded-lg hover:bg-navy-900 transition-colors text-[12px] font-semibold"
          >
            Done
          </button>
        </div>
      </div>
    </div>
  )
}

function fmt(s) { return s.charAt(0).toUpperCase() + s.slice(1) }
