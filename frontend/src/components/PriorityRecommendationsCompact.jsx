import { useState, useEffect } from 'react';
import api from '../services/api';

/* ─── urgency config ─── */
const urgency = (score) => {
  if (score >= 8) return {
    dot: 'bg-red-500', ring: 'ring-red-500/20', tint: 'bg-red-500/[0.04]',
    badge: 'bg-red-50 text-red-600 border-red-100', label: 'Critical',
    bar: 'from-red-500 to-rose-400',
  }
  if (score >= 6) return {
    dot: 'bg-amber-500', ring: 'ring-amber-500/20', tint: 'bg-amber-500/[0.03]',
    badge: 'bg-amber-50 text-amber-600 border-amber-100', label: 'High',
    bar: 'from-amber-500 to-orange-400',
  }
  return {
    dot: 'bg-sky-500', ring: 'ring-sky-500/20', tint: 'bg-sky-500/[0.03]',
    badge: 'bg-sky-50 text-sky-600 border-sky-100', label: 'Normal',
    bar: 'from-sky-500 to-blue-400',
  }
}

const relativeDue = (d) => {
  if (!d) return null
  const diff = Math.ceil((new Date(d) - new Date()) / 864e5)
  if (diff < 0) return { text: `${Math.abs(diff)}d overdue`, cls: 'text-red-500 font-semibold' }
  if (diff === 0) return { text: 'Today', cls: 'text-amber-600 font-semibold' }
  if (diff === 1) return { text: 'Tomorrow', cls: 'text-amber-500' }
  return { text: `${diff}d left`, cls: 'text-surface-400' }
}

export default function PriorityRecommendationsCompact({ onTaskClick }) {
  const [recs, setRecs] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => { fetch() }, [])

  const fetch = async () => {
    try {
      setLoading(true)
      const r = await api.get('/api/v1/recommendations/priority-tasks?limit=3')
      if (r.data.success) setRecs(r.data.recommendations.slice(0, 3))
    } catch { setError(true) }
    finally { setLoading(false) }
  }

  /* ── loading skeleton ── */
  if (loading) return (
    <div className="rounded-2xl border border-surface-200/80 bg-white p-5">
      <div className="animate-pulse space-y-4">
        <div className="h-4 w-32 bg-surface-100 rounded-lg" />
        {[0,1,2].map(i => (
          <div key={i} className="flex items-center gap-3">
            <div className="w-7 h-7 rounded-lg bg-surface-100" />
            <div className="flex-1 space-y-2">
              <div className="h-3.5 bg-surface-100 rounded w-3/4" />
              <div className="h-2.5 bg-surface-100 rounded w-1/2" />
            </div>
          </div>
        ))}
      </div>
    </div>
  )

  if (error) return (
    <div className="rounded-2xl border border-surface-200/80 bg-white p-5">
      <p className="text-[13px] text-red-500">Failed to load priorities</p>
    </div>
  )

  if (!recs.length) return (
    <div className="rounded-2xl border border-surface-200/80 bg-white p-6">
      <div className="text-center py-6">
        <div className="w-12 h-12 rounded-2xl bg-emerald-50 flex items-center justify-center mx-auto mb-3">
          <svg className="w-6 h-6 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <p className="text-[14px] font-semibold text-navy-900">All caught up</p>
        <p className="text-[12px] text-surface-400 mt-0.5">No pending tasks to prioritize</p>
      </div>
    </div>
  )

  return (
    <div className="rounded-2xl border border-surface-200/80 bg-white overflow-hidden">
      {/* Header */}
      <div className="px-5 pt-5 pb-3 flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-xl bg-navy-800 flex items-center justify-center">
            <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
              <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z" />
            </svg>
          </div>
          <div>
            <h2 className="text-[15px] font-bold text-navy-900 leading-tight">Focus Next</h2>
            <p className="text-[11px] text-surface-400">Top {recs.length} AI-ranked priorities</p>
          </div>
        </div>
      </div>

      {/* Recommendation rows */}
      <div className="px-3 pb-3">
        {recs.map((rec, i) => {
          const u = urgency(rec.priority_score)
          const due = relativeDue(rec.due_date)
          const pct = Math.round((rec.priority_score / 10) * 100)

          return (
            <div
              key={rec.task_id}
              className={`group relative rounded-xl p-3.5 mb-1.5 last:mb-0 transition-all duration-200 hover:bg-surface-50 ${rec.is_overdue ? u.tint : ''}`}
              style={{ animationDelay: `${i * 60}ms` }}
            >
              <div className="flex items-start gap-3">
                {/* Rank */}
                <div className="flex-shrink-0 mt-0.5">
                  <div className={`w-7 h-7 rounded-lg bg-surface-100 flex items-center justify-center ring-2 ${u.ring} transition-all group-hover:ring-4`}>
                    <span className="font-mono text-[13px] font-bold text-navy-800">{i + 1}</span>
                  </div>
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  {/* Title row */}
                  <div className="flex items-start justify-between gap-2 mb-1.5">
                    <h3 className="text-[13px] font-semibold text-navy-900 leading-snug line-clamp-2">{rec.title}</h3>
                    <span className={`flex-shrink-0 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider rounded-md border ${u.badge}`}>
                      {u.label}
                    </span>
                  </div>

                  {/* Meta line */}
                  <div className="flex items-center gap-1.5 flex-wrap mb-2.5">
                    <span className="px-1.5 py-0.5 text-[10px] font-semibold rounded bg-navy-800/[0.06] text-navy-700">
                      {rec.course_code}
                    </span>
                    <span className="text-surface-300">·</span>
                    <span className="text-[11px] text-surface-400">{rec.task_type}</span>
                    <span className="text-surface-300">·</span>
                    <span className="text-[11px] text-surface-400">{rec.weight}mk</span>
                    {due && (
                      <>
                        <span className="text-surface-300">·</span>
                        <span className={`text-[11px] ${due.cls}`}>{due.text}</span>
                      </>
                    )}
                  </div>

                  {/* Priority bar + CTA */}
                  <div className="flex items-center gap-2.5">
                    <div className="flex-1 flex items-center gap-2">
                      <div className="flex-1 h-1.5 bg-surface-100 rounded-full overflow-hidden">
                        <div
                          className={`h-full rounded-full bg-gradient-to-r ${u.bar} transition-all duration-700`}
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                      <span className="font-mono text-[11px] font-semibold text-surface-400 w-8 text-right">{pct}%</span>
                    </div>
                    <button
                      onClick={() => onTaskClick?.(rec.task_id)}
                      className="flex-shrink-0 px-3 py-1 bg-navy-800 text-white text-[11px] font-semibold rounded-lg hover:bg-navy-900 transition-colors opacity-0 group-hover:opacity-100 translate-x-1 group-hover:translate-x-0 transition-all duration-200"
                    >
                      Focus
                    </button>
                  </div>

                  {/* Overdue alert */}
                  {rec.is_overdue && (
                    <div className="mt-2 flex items-center gap-1.5 px-2 py-1 rounded-md bg-red-50 border border-red-100">
                      <svg className="w-3 h-3 text-red-400 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M8.485 2.495c.673-1.167 2.357-1.167 3.03 0l6.28 10.875c.673 1.167-.17 2.625-1.516 2.625H3.72c-1.347 0-2.189-1.458-1.515-2.625L8.485 2.495zM10 5a.75.75 0 01.75.75v3.5a.75.75 0 01-1.5 0v-3.5A.75.75 0 0110 5zm0 9a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd" />
                      </svg>
                      <p className="text-[10px] font-semibold text-red-600">Overdue — complete ASAP</p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
