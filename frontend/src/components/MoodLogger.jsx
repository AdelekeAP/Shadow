import { useState, useEffect, useRef } from 'react'
import api from '../services/api'

/* ─── Mood options ─── */
const moods = [
  { value: 'focused',     emoji: '🎯', label: 'Focused',     tint: 'bg-blue-500/[0.06]',   ring: 'ring-blue-400/40',   dot: 'bg-blue-500' },
  { value: 'motivated',   emoji: '💪', label: 'Motivated',   tint: 'bg-emerald-500/[0.06]', ring: 'ring-emerald-400/40', dot: 'bg-emerald-500' },
  { value: 'calm',        emoji: '😌', label: 'Calm',        tint: 'bg-teal-500/[0.06]',   ring: 'ring-teal-400/40',   dot: 'bg-teal-500' },
  { value: 'confident',   emoji: '😎', label: 'Confident',   tint: 'bg-indigo-500/[0.06]', ring: 'ring-indigo-400/40', dot: 'bg-indigo-500' },
  { value: 'tired',       emoji: '😴', label: 'Tired',       tint: 'bg-surface-300/[0.12]', ring: 'ring-surface-300/40', dot: 'bg-surface-400' },
  { value: 'stressed',    emoji: '😰', label: 'Stressed',    tint: 'bg-orange-500/[0.06]', ring: 'ring-orange-400/40', dot: 'bg-orange-500' },
  { value: 'anxious',     emoji: '😟', label: 'Anxious',     tint: 'bg-amber-500/[0.06]',  ring: 'ring-amber-400/40',  dot: 'bg-amber-500' },
  { value: 'overwhelmed', emoji: '😵', label: 'Overwhelmed', tint: 'bg-red-500/[0.06]',    ring: 'ring-red-400/40',    dot: 'bg-red-500' },
]

/* ─── Energy gradient segments ─── */
const energySegments = [
  { value: 1, label: 'Very Low', fill: 'bg-red-400' },
  { value: 2, label: 'Low',      fill: 'bg-orange-400' },
  { value: 3, label: 'Medium',   fill: 'bg-amber-400' },
  { value: 4, label: 'High',     fill: 'bg-emerald-400' },
  { value: 5, label: 'Peak',     fill: 'bg-blue-400' },
]

export default function MoodLogger({ onMoodLogged, onClose }) {
  const [formData, setFormData] = useState({ mood_type: '', energy_level: 3, note: '' })
  const [loading, setLoading] = useState(false)
  const [feedback, setFeedback] = useState(null)       // inline success/insight
  const [mismatch, setMismatch] = useState(null)        // AI mismatch
  const [sentimentFeedback, setSentimentFeedback] = useState(null)
  const backdropRef = useRef(null)
  const [entering, setEntering] = useState(false)

  useEffect(() => { requestAnimationFrame(() => setEntering(true)) }, [])

  const close = () => { setEntering(false); setTimeout(onClose, 200) }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!formData.mood_type) return
    setLoading(true)
    try {
      const r = await api.post('/api/v1/mood/log-mood', formData)
      if (r.data.success) {
        // Sentiment
        if (r.data.sentiment_analysis) {
          setSentimentFeedback({
            label: r.data.sentiment_analysis.primary_emotion || r.data.sentiment_analysis.label,
            confidence: r.data.sentiment_analysis.confidence,
          })
        }

        // Mismatch
        if (r.data.mismatch_detected?.detected) {
          setMismatch({
            type: r.data.mismatch_detected.type,
            message: r.data.mismatch_detected.message,
            moodCategory: r.data.mismatch_detected.mood_category,
            noteSentiment: r.data.mismatch_detected.note_sentiment,
          })
        } else {
          // Success — show inline feedback then auto-close
          let insight = ''
          if (formData.energy_level <= 2) insight = 'Low energy detected — we\'ll prioritize lighter tasks for you.'
          else if (formData.mood_type === 'stressed' || formData.mood_type === 'overwhelmed') insight = 'Feeling stressed? Quick wins will be prioritized.'
          else if (formData.mood_type === 'focused' || formData.mood_type === 'motivated') insight = 'Great energy — this is a good time for challenging tasks.'

          setFeedback({ mood: formData.mood_type, insight })
          setTimeout(() => { onMoodLogged?.(r.data.mood_log); close() }, 2200)
        }
      }
    } catch (e) {
      console.error('Mood log error:', e)
      setFeedback({ error: true })
      setTimeout(() => setFeedback(null), 3000)
    } finally {
      setLoading(false)
    }
  }

  const handleMismatchKeep = () => {
    setMismatch(null)
    setFormData({ mood_type: '', energy_level: 3, note: '' })
    setFeedback({ mood: formData.mood_type, insight: 'It\'s okay to feel complex emotions.' })
    setTimeout(() => { onMoodLogged?.(null); close() }, 2000)
  }

  const selectedMood = moods.find(m => m.value === formData.mood_type)
  const selectedEnergy = energySegments.find(e => e.value === formData.energy_level)

  /* ─── Success state ─── */
  if (feedback && !feedback.error) {
    const m = moods.find(x => x.value === feedback.mood)
    return (
      <div className="fixed inset-0 bg-navy-950/40 backdrop-blur-sm flex items-center justify-center z-50 p-4">
        <div className="bg-white rounded-2xl shadow-2xl max-w-sm w-full p-8 text-center animate-scale-in">
          <div className="w-16 h-16 rounded-2xl bg-emerald-50 flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8">
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <p className="text-[11px] font-semibold uppercase tracking-wider text-emerald-500 mb-1">Mood logged</p>
          <p className="text-3xl mb-2">{m?.emoji || '😊'}</p>
          <p className="text-[15px] font-bold text-navy-900 capitalize mb-1">{feedback.mood}</p>
          {feedback.insight && (
            <p className="text-[12px] text-surface-400 leading-relaxed mt-2 max-w-[260px] mx-auto">{feedback.insight}</p>
          )}
          {sentimentFeedback && (
            <div className="mt-3 inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-navy-800/[0.04]">
              <svg className="w-3 h-3 text-navy-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z" />
              </svg>
              <span className="text-[10px] font-medium text-navy-600">
                AI: {sentimentFeedback.label.toLowerCase()} ({Math.round(sentimentFeedback.confidence * 100)}%)
              </span>
            </div>
          )}
        </div>
      </div>
    )
  }

  return (
    <div
      ref={backdropRef}
      onClick={(e) => e.target === backdropRef.current && close()}
      className={`fixed inset-0 bg-navy-950/40 backdrop-blur-sm flex items-center justify-center z-50 p-4 transition-opacity duration-200 ${
        entering ? 'opacity-100' : 'opacity-0'
      }`}
    >
      <div className={`bg-white rounded-2xl shadow-2xl max-w-md w-full overflow-hidden transition-all duration-300 ${
        entering ? 'scale-100 translate-y-0 opacity-100' : 'scale-95 translate-y-4 opacity-0'
      }`}>

        {/* ── Header ── */}
        <div className="px-6 pt-6 pb-0 flex items-start justify-between">
          <div>
            <h2 className="font-display text-[20px] font-bold text-navy-900 tracking-tight">How are you feeling?</h2>
            <p className="text-[12px] text-surface-400 mt-0.5">Check in so Shadow can adapt your priorities</p>
          </div>
          <button
            onClick={close}
            className="p-1.5 rounded-lg text-surface-300 hover:text-surface-400 hover:bg-surface-100 transition-all -mt-1 -mr-1"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* ── Mismatch Warning ── */}
        {mismatch && (
          <div className="mx-6 mt-4 p-4 rounded-xl bg-amber-500/[0.05] border border-amber-200/60">
            <div className="flex items-start gap-3">
              <div className="w-8 h-8 rounded-lg bg-amber-50 flex items-center justify-center flex-shrink-0 mt-0.5">
                <svg className="w-4 h-4 text-amber-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m0-10.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
                </svg>
              </div>
              <div className="flex-1">
                <h4 className="text-[13px] font-bold text-navy-900 mb-1">AI noticed something</h4>
                <p className="text-[12px] text-surface-400 leading-relaxed mb-3">{mismatch.message}</p>
                <div className="flex items-center gap-2 mb-3">
                  <span className={`px-2 py-0.5 rounded-md text-[10px] font-semibold border ${
                    mismatch.moodCategory === 'negative' ? 'bg-red-50 text-red-600 border-red-100' : 'bg-emerald-50 text-emerald-600 border-emerald-100'
                  }`}>Mood: {mismatch.moodCategory}</span>
                  <span className={`px-2 py-0.5 rounded-md text-[10px] font-semibold border ${
                    mismatch.noteSentiment === 'NEGATIVE' ? 'bg-red-50 text-red-600 border-red-100' : 'bg-emerald-50 text-emerald-600 border-emerald-100'
                  }`}>Note: {mismatch.noteSentiment?.toLowerCase()}</span>
                </div>
                <div className="flex gap-2">
                  <button onClick={handleMismatchKeep} className="flex-1 px-3 py-2 bg-navy-800 text-white text-[12px] font-semibold rounded-lg hover:bg-navy-900 transition-colors">
                    Keep my response
                  </button>
                  <button onClick={() => setMismatch(null)} className="flex-1 px-3 py-2 border border-surface-200 text-navy-700 text-[12px] font-semibold rounded-lg hover:bg-surface-50 transition-colors">
                    Reconsider
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ── Error toast ── */}
        {feedback?.error && (
          <div className="mx-6 mt-4 px-4 py-2.5 rounded-xl bg-red-50 border border-red-100 flex items-center gap-2">
            <svg className="w-4 h-4 text-red-400 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
            </svg>
            <span className="text-[12px] font-medium text-red-600">Failed to log mood. Try again.</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="p-6 space-y-5">

          {/* ── Mood Grid ── */}
          <div>
            <label className="text-[12px] font-semibold text-navy-800 uppercase tracking-wider mb-2.5 block">Select mood</label>
            <div className="grid grid-cols-4 gap-2">
              {moods.map((m) => {
                const sel = formData.mood_type === m.value
                return (
                  <button
                    key={m.value}
                    type="button"
                    onClick={() => setFormData({ ...formData, mood_type: m.value })}
                    className={`relative flex flex-col items-center gap-1 py-3 px-1 rounded-xl transition-all duration-200 ${
                      sel
                        ? `${m.tint} ring-2 ${m.ring} scale-[1.04]`
                        : 'bg-surface-50 hover:bg-surface-100 ring-1 ring-surface-200/60 hover:ring-surface-300/60'
                    }`}
                  >
                    <span className="text-[22px] leading-none">{m.emoji}</span>
                    <span className={`text-[10px] font-semibold leading-tight ${sel ? 'text-navy-800' : 'text-surface-400'}`}>
                      {m.label}
                    </span>
                    {sel && <div className={`absolute -bottom-0.5 left-1/2 -translate-x-1/2 w-1 h-1 rounded-full ${m.dot}`} />}
                  </button>
                )
              })}
            </div>
          </div>

          {/* ── Energy Level ── */}
          <div>
            <div className="flex items-center justify-between mb-2.5">
              <label className="text-[12px] font-semibold text-navy-800 uppercase tracking-wider">Energy</label>
              <span className="text-[11px] font-medium text-surface-400">{selectedEnergy?.label}</span>
            </div>
            <div className="flex gap-1.5">
              {energySegments.map((seg) => {
                const active = seg.value <= formData.energy_level
                const isExact = seg.value === formData.energy_level
                return (
                  <button
                    key={seg.value}
                    type="button"
                    onClick={() => setFormData({ ...formData, energy_level: seg.value })}
                    className={`flex-1 h-8 rounded-lg transition-all duration-200 relative group ${
                      active
                        ? `${seg.fill} ${isExact ? 'ring-2 ring-navy-800/20 scale-y-110' : 'opacity-70'}`
                        : 'bg-surface-100 hover:bg-surface-200'
                    }`}
                    title={seg.label}
                  >
                    {isExact && (
                      <span className="absolute -top-0.5 left-1/2 -translate-x-1/2 w-1.5 h-1.5 rounded-full bg-navy-800" />
                    )}
                  </button>
                )
              })}
            </div>
            <div className="flex justify-between mt-1.5 px-0.5">
              <span className="text-[9px] text-surface-300 font-medium">Very Low</span>
              <span className="text-[9px] text-surface-300 font-medium">Peak</span>
            </div>
          </div>

          {/* ── Note ── */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-[12px] font-semibold text-navy-800 uppercase tracking-wider">Note <span className="normal-case tracking-normal font-normal text-surface-300">(optional)</span></label>
              <div className="flex items-center gap-1">
                <svg className="w-3 h-3 text-navy-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z" />
                </svg>
                <span className="text-[10px] font-medium text-navy-500">AI sentiment analysis</span>
              </div>
            </div>
            <textarea
              value={formData.note}
              onChange={(e) => setFormData({ ...formData, note: e.target.value })}
              placeholder="What's on your mind?"
              className="w-full px-4 py-3 bg-surface-50 border border-surface-200/80 rounded-xl text-[13px] text-navy-900 placeholder:text-surface-300 focus:border-navy-300 focus:ring-2 focus:ring-navy-100 focus:bg-white transition-all resize-none"
              rows="3"
              maxLength="500"
            />
            <div className="flex items-center justify-between mt-1">
              <span className="text-[10px] text-surface-300">{formData.note.length > 0 && 'AI will analyze sentiment'}</span>
              <span className="text-[10px] font-mono text-surface-300">{formData.note.length}/500</span>
            </div>
          </div>

          {/* ── Actions ── */}
          <div className="flex gap-3 pt-1">
            <button
              type="button"
              onClick={close}
              className="flex-1 px-5 py-2.5 border border-surface-200 text-navy-700 rounded-xl text-[13px] font-semibold hover:bg-surface-50 transition-all"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading || !formData.mood_type}
              className="flex-1 px-5 py-2.5 bg-navy-800 hover:bg-navy-900 text-white rounded-xl text-[13px] font-semibold transition-all disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {loading ? (
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : (
                <>
                  {selectedMood && <span className="text-base leading-none">{selectedMood.emoji}</span>}
                  Log Mood
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
