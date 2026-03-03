/**
 * Effectiveness Analytics Dashboard
 * Shows SmartStudy intervention effectiveness with charts and metrics
 */
import { useState, useEffect } from 'react'
import { VictoryPie, VictoryChart, VictoryBar, VictoryAxis, VictoryTheme, VictoryLine, VictoryArea } from 'victory'
import {
  getEffectivenessSummary,
  getEffectivenessByLearningStyle,
  getEffectivenessOverTime,
  getMoodEffectivenessCorrelation,
  getTopicEffectiveness,
  getStatisticalAnalysis
} from '../services/api'

/* ── Color palette ── */
const COLORS = {
  primary: '#1e3a8a',
  secondary: '#3b82f6',
  success: '#10b981',
  warning: '#f59e0b',
  danger: '#ef4444',
  purple: '#8b5cf6',
  pink: '#ec4899'
}

const LEARNING_STYLE_COLORS = {
  visual: '#8b5cf6',
  audio: '#3b82f6',
  reading: '#10b981',
  kinesthetic: '#f59e0b'
}

const RESOURCE_TYPE_COLORS = {
  youtube_video: '#ef4444',
  documentation: '#3b82f6',
  article: '#10b981',
  practice: '#f59e0b',
  interactive: '#8b5cf6',
  reddit_post: '#ec4899'
}

/* ── SVG tab icons ── */
const TabIcons = {
  overview: (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
    </svg>
  ),
  learning: (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 18v-5.25m0 0a6.01 6.01 0 001.5-.189m-1.5.189a6.01 6.01 0 01-1.5-.189m3.75 7.478a12.06 12.06 0 01-4.5 0m3.75 2.383a14.406 14.406 0 01-3 0M14.25 18v-.192c0-.983.658-1.823 1.508-2.316a7.5 7.5 0 10-7.517 0c.85.493 1.509 1.333 1.509 2.316V18" />
    </svg>
  ),
  trends: (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M2.25 18L9 11.25l4.306 4.307a11.95 11.95 0 015.814-5.519l2.74-1.22m0 0l-5.94-2.28m5.94 2.28l-2.28 5.941" />
    </svg>
  ),
  mood: (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15.182 15.182a4.5 4.5 0 01-6.364 0M21 12a9 9 0 11-18 0 9 9 0 0118 0zM9.75 9.75c0 .414-.168.75-.375.75S9 10.164 9 9.75 9.168 9 9.375 9s.375.336.375.75zm-.375 0h.008v.015h-.008V9.75zm5.625 0c0 .414-.168.75-.375.75s-.375-.336-.375-.75.168-.75.375-.75.375.336.375.75zm-.375 0h.008v.015h-.008V9.75z" />
    </svg>
  ),
  research: (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0112 15a9.065 9.065 0 00-6.23.693L5 14.5m14.8.8l1.402 5.235c.292 1.092-.757 2.075-1.871 1.822L18 21.89a9 9 0 01-12 0l-1.331.467c-1.114.253-2.163-.73-1.87-1.822L4.2 15.3" />
    </svg>
  )
}

/* ── Learning style SVG icons ── */
const StyleIcons = {
  visual: (
    <svg className="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z" />
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
    </svg>
  ),
  audio: (
    <svg className="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19.114 5.636a9 9 0 010 12.728M16.463 8.288a5.25 5.25 0 010 7.424M6.75 8.25l4.72-4.72a.75.75 0 011.28.53v15.88a.75.75 0 01-1.28.53l-4.72-4.72H4.51c-.88 0-1.704-.507-1.938-1.354A9.01 9.01 0 012.25 12c0-.83.112-1.633.322-2.396C2.806 8.756 3.63 8.25 4.51 8.25H6.75z" />
    </svg>
  ),
  reading: (
    <svg className="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 016-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0018 18a8.967 8.967 0 00-6 2.292m0-14.25v14.25" />
    </svg>
  ),
  kinesthetic: (
    <svg className="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M10.05 4.575a1.575 1.575 0 10-3.15 0v3m3.15-3v-1.5a1.575 1.575 0 013.15 0v1.5m-3.15 0l-.075 5.925m3.075-5.925a1.575 1.575 0 013.15 0v1.5m0 0v3.375c0 .621.504 1.125 1.125 1.125h.426c.795 0 1.467.573 1.596 1.36l.386 2.317c.134.802-.273 1.59-1.001 1.938A13.77 13.77 0 0112 21a13.77 13.77 0 01-5.632-1.189 1.655 1.655 0 01-1.001-1.938l.386-2.317c.129-.787.801-1.36 1.596-1.36h.426c.621 0 1.125-.504 1.125-1.125V7.575" />
    </svg>
  )
}

/* ── Mood SVG icons ── */
function getMoodSvg(mood) {
  const base = "w-5 h-5"
  switch (mood) {
    case 'focused':
      return <svg className={base} fill="none" stroke="currentColor" viewBox="0 0 24 24"><circle cx="12" cy="12" r="9" strokeWidth={1.5} /><circle cx="12" cy="12" r="5" strokeWidth={1.5} /><circle cx="12" cy="12" r="1" fill="currentColor" /></svg>
    case 'motivated':
      return <svg className={base} fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15.362 5.214A8.252 8.252 0 0112 21 8.25 8.25 0 016.038 7.048 8.287 8.287 0 009 9.6a8.983 8.983 0 013.361-6.867 8.21 8.21 0 003 2.48z" /></svg>
    case 'tired':
      return <svg className={base} fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21.752 15.002A9.718 9.718 0 0118 15.75c-5.385 0-9.75-4.365-9.75-9.75 0-1.33.266-2.597.748-3.752A9.753 9.753 0 003 11.25C3 16.635 7.365 21 12.75 21a9.753 9.753 0 009.002-5.998z" /></svg>
    case 'stressed':
    case 'anxious':
      return <svg className={base} fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" /></svg>
    case 'confident':
      return <svg className={base} fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z" /></svg>
    default:
      return <svg className={base} fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15.182 15.182a4.5 4.5 0 01-6.364 0M21 12a9 9 0 11-18 0 9 9 0 0118 0zM9.75 9.75c0 .414-.168.75-.375.75S9 10.164 9 9.75 9.168 9 9.375 9s.375.336.375.75zm-.375 0h.008v.015h-.008V9.75zm5.625 0c0 .414-.168.75-.375.75s-.375-.336-.375-.75.168-.75.375-.75.375.336.375.75zm-.375 0h.008v.015h-.008V9.75z" /></svg>
  }
}

export default function EffectivenessAnalytics({ onClose }) {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [activeTab, setActiveTab] = useState('overview')
  const [entering, setEntering] = useState(true)
  const [selectedDays, setSelectedDays] = useState(30)

  const [summary, setSummary] = useState(null)
  const [learningStyleData, setLearningStyleData] = useState(null)
  const [timeData, setTimeData] = useState(null)
  const [moodData, setMoodData] = useState(null)
  const [topicData, setTopicData] = useState(null)
  const [statsData, setStatsData] = useState(null)

  useEffect(() => {
    loadAllData()
    requestAnimationFrame(() => requestAnimationFrame(() => setEntering(false)))
  }, [])

  useEffect(() => {
    const handleKeyDown = (e) => { if (e.key === 'Escape') handleClose() }
    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [])

  const loadAllData = async () => {
    setLoading(true)
    setError(null)

    try {
      const [summaryRes, styleRes, timeRes, moodRes, topicRes] = await Promise.all([
        getEffectivenessSummary(),
        getEffectivenessByLearningStyle(),
        getEffectivenessOverTime(selectedDays),
        getMoodEffectivenessCorrelation(),
        getTopicEffectiveness()
      ])

      setSummary(summaryRes)
      setLearningStyleData(styleRes)
      setTimeData(timeRes)
      setMoodData(moodRes)
      setTopicData(topicRes)

      try {
        const statsRes = await getStatisticalAnalysis()
        setStatsData(statsRes)
      } catch (statsErr) {
        console.error('Error loading statistical analysis:', statsErr)
      }
    } catch (err) {
      console.error('Error loading analytics:', err)
      setError('Failed to load analytics data')
    } finally {
      setLoading(false)
    }
  }

  const loadTimeData = async (days) => {
    try {
      const timeRes = await getEffectivenessOverTime(days)
      setTimeData(timeRes)
    } catch (err) { console.error('Error loading time data:', err) }
  }

  const handleDaysChange = (days) => {
    setSelectedDays(days)
    loadTimeData(days)
  }

  const handleClose = () => {
    setEntering(true)
    setTimeout(onClose, 200)
  }

  const exportCSV = () => {
    if (!statsData) return
    const rows = [['Metric', 'Value']]
    rows.push(['Sample Size', statsData.sample_size])
    if (statsData.descriptive_statistics) {
      const ds = statsData.descriptive_statistics
      rows.push(['Mean Improvement', ds.mean_improvement])
      rows.push(['Median Improvement', ds.median_improvement])
      rows.push(['Std Deviation', ds.std_improvement])
      rows.push(['Min Improvement', ds.min_improvement])
      rows.push(['Max Improvement', ds.max_improvement])
    }
    if (statsData.inferential_statistics) {
      const is = statsData.inferential_statistics
      rows.push(['t-statistic', is.t_statistic])
      rows.push(['p-value', is.p_value])
      rows.push(['Cohen\'s d', is.cohens_d])
      rows.push(['Effect Size', is.effect_size_interpretation])
      rows.push(['95% CI Lower', is.confidence_interval_95?.lower])
      rows.push(['95% CI Upper', is.confidence_interval_95?.upper])
      rows.push(['Significant', is.is_statistically_significant ? 'Yes' : 'No'])
    }
    if (statsData.paired_scores) {
      rows.push([])
      rows.push(['Topic', 'Before Score', 'After Score', 'Improvement'])
      statsData.paired_scores.forEach(s => {
        rows.push([s.topic, s.before_score || s.before, s.after_score || s.after, s.improvement])
      })
    }
    const csv = rows.map(r => r.map(v => `"${String(v ?? '').replace(/"/g, '""')}"`).join(',')).join('\n')
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `shadow-analytics-${new Date().toISOString().slice(0, 10)}.csv`
    a.click()
    URL.revokeObjectURL(url)
  }

  if (loading) {
    return (
      <div className="fixed inset-0 bg-navy-950/40 backdrop-blur-sm flex items-center justify-center z-50 p-4">
        <div className="bg-white rounded-2xl p-8 text-center shadow-xl">
          <div className="animate-spin rounded-full h-10 w-10 border-2 border-navy-800 border-t-transparent mx-auto"></div>
          <p className="text-surface-400 mt-4 font-sans text-sm">Loading analytics...</p>
        </div>
      </div>
    )
  }

  const tabs = [
    { id: 'overview', label: 'Overview' },
    { id: 'learning', label: 'Learning Styles' },
    { id: 'trends', label: 'Trends' },
    { id: 'mood', label: 'Mood Impact' },
    { id: 'research', label: 'Research' }
  ]

  return (
    <div role="dialog" aria-modal="true" aria-label="Effectiveness Analytics" className={`fixed inset-0 bg-navy-950/40 backdrop-blur-sm flex items-center justify-center z-50 p-4 overflow-y-auto transition-opacity duration-200 ${entering ? 'opacity-0' : 'opacity-100'}`}>
      <div className={`bg-white rounded-2xl shadow-xl max-w-6xl w-full max-h-[95vh] overflow-hidden flex flex-col transition-all duration-300 ${entering ? 'scale-95 opacity-0' : 'scale-100 opacity-100'}`}>
        {/* Header */}
        <div className="px-6 py-4 border-b border-surface-100">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-navy-800/[0.06] flex items-center justify-center text-navy-800">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
                </svg>
              </div>
              <div>
                <h2 className="text-xl font-display font-semibold text-navy-900">Effectiveness Analytics</h2>
                <p className="text-surface-400 text-[13px]">Track your learning intervention outcomes</p>
              </div>
            </div>
            <button
              onClick={handleClose}
              className="p-2 hover:bg-surface-100 rounded-xl transition-colors text-surface-400 hover:text-surface-500"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Tabs */}
          <div className="flex gap-1">
            {tabs.map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`px-3.5 py-2 rounded-lg font-medium text-sm transition-colors flex items-center gap-2 ${
                  activeTab === tab.id
                    ? 'bg-navy-800 text-white'
                    : 'text-surface-400 hover:bg-surface-50 hover:text-navy-800'
                }`}
              >
                {TabIcons[tab.id]}
                <span>{tab.label}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {error ? (
            <div className="bg-red-50/50 border border-red-200/80 rounded-xl p-4 text-red-700 text-sm">
              {error}
            </div>
          ) : (
            <>
              {/* Overview Tab */}
              {activeTab === 'overview' && summary && (
                <div className="space-y-6">
                  {/* Summary Cards */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <StatCard
                      title="Study Plans"
                      value={summary.summary.total_study_plans}
                      subtitle={`${summary.summary.active_study_plans} active`}
                      icon={<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 016-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0018 18a8.967 8.967 0 00-6 2.292m0-14.25v14.25" /></svg>}
                      color="bg-navy-800/[0.03] border-navy-800/10"
                      iconColor="bg-navy-800/[0.06] text-navy-800"
                    />
                    <StatCard
                      title="Avg Improvement"
                      value={`${summary.summary.average_improvement > 0 ? '+' : ''}${summary.summary.average_improvement}%`}
                      subtitle={`${summary.summary.positive_improvements} improved`}
                      icon={<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M2.25 18L9 11.25l4.306 4.307a11.95 11.95 0 015.814-5.519l2.74-1.22m0 0l-5.94-2.28m5.94 2.28l-2.28 5.941" /></svg>}
                      color={summary.summary.average_improvement > 0 ? "bg-emerald-50/50 border-emerald-200/60" : "bg-red-50/50 border-red-200/60"}
                      iconColor={summary.summary.average_improvement > 0 ? "bg-emerald-100 text-emerald-700" : "bg-red-100 text-red-600"}
                    />
                    <StatCard
                      title="Engagement Rate"
                      value={`${summary.engagement.engagement_rate}%`}
                      subtitle={`${summary.engagement.resources_clicked}/${summary.engagement.total_resources} clicked`}
                      icon={<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><circle cx="12" cy="12" r="9" strokeWidth={1.5} /><circle cx="12" cy="12" r="5" strokeWidth={1.5} /><circle cx="12" cy="12" r="1" fill="currentColor" /></svg>}
                      color="bg-purple-50/50 border-purple-200/60"
                      iconColor="bg-purple-100 text-purple-700"
                    />
                    <StatCard
                      title="Avg Rating"
                      value={`${summary.engagement.average_helpful_rating}/5`}
                      subtitle={`${summary.engagement.rated_resources_count} ratings`}
                      icon={<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M11.48 3.499a.562.562 0 011.04 0l2.125 5.111a.563.563 0 00.475.345l5.518.442c.499.04.701.663.321.988l-4.204 3.602a.563.563 0 00-.182.557l1.285 5.385a.562.562 0 01-.84.61l-4.725-2.885a.563.563 0 00-.586 0L6.982 20.54a.562.562 0 01-.84-.61l1.285-5.386a.562.562 0 00-.182-.557l-4.204-3.602a.563.563 0 01.321-.988l5.518-.442a.563.563 0 00.475-.345L11.48 3.5z" /></svg>}
                      color="bg-amber-50/50 border-amber-200/60"
                      iconColor="bg-amber-100 text-amber-700"
                    />
                  </div>

                  {/* Engagement Breakdown */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="bg-white rounded-xl border border-surface-200/80 p-6">
                      <h3 className="text-[15px] font-semibold text-navy-900 mb-4">Resource Engagement</h3>
                      <div className="space-y-4">
                        <ProgressBar
                          label="Clicked"
                          value={summary.engagement.resources_clicked}
                          max={summary.engagement.total_resources}
                          color="bg-blue-500"
                        />
                        <ProgressBar
                          label="Completed"
                          value={summary.engagement.resources_completed}
                          max={summary.engagement.total_resources}
                          color="bg-emerald-500"
                        />
                      </div>

                      <div className="mt-6 pt-4 border-t border-surface-100">
                        <div className="grid grid-cols-2 gap-4 text-center">
                          <div>
                            <p className="text-2xl font-bold text-navy-900">
                              {summary.summary.total_conversations}
                            </p>
                            <p className="text-xs text-surface-400">AI Conversations</p>
                          </div>
                          <div>
                            <p className="text-2xl font-bold text-navy-900">
                              {summary.summary.total_messages}
                            </p>
                            <p className="text-xs text-surface-400">Messages</p>
                          </div>
                        </div>
                      </div>
                    </div>

                    <div className="bg-white rounded-xl border border-surface-200/80 p-6">
                      <h3 className="text-[15px] font-semibold text-navy-900 mb-4">Study Plan Status</h3>
                      {summary.summary.total_study_plans > 0 ? (
                        <div className="h-64">
                          <VictoryPie
                            data={[
                              { x: 'Active', y: summary.summary.active_study_plans },
                              { x: 'Completed', y: summary.summary.completed_study_plans }
                            ]}
                            colorScale={[COLORS.primary, COLORS.success]}
                            labels={({ datum }) => `${datum.x}\n${datum.y}`}
                            labelRadius={({ innerRadius }) => innerRadius + 40}
                            style={{
                              labels: { fontSize: 12, fill: 'white', fontWeight: 'bold' }
                            }}
                            innerRadius={60}
                            height={250}
                          />
                        </div>
                      ) : (
                        <div className="h-64 flex items-center justify-center text-surface-300">
                          <p className="text-sm">No study plans yet</p>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Top Topics */}
                  {topicData && topicData.topics.length > 0 && (
                    <div className="bg-white rounded-xl border border-surface-200/80 p-6">
                      <h3 className="text-[15px] font-semibold text-navy-900 mb-4">Top Study Topics</h3>
                      <div className="space-y-2">
                        {topicData.topics.slice(0, 5).map((topic, idx) => (
                          <div key={idx} className="flex items-center justify-between p-3 bg-surface-50/50 rounded-xl">
                            <div className="flex items-center gap-3">
                              <span className={`w-7 h-7 rounded-lg flex items-center justify-center text-xs font-bold ${
                                idx === 0 ? 'bg-amber-100 text-amber-700' :
                                idx === 1 ? 'bg-surface-200 text-surface-500' :
                                idx === 2 ? 'bg-orange-100 text-orange-600' :
                                'bg-surface-100 text-surface-400'
                              }`}>
                                {idx + 1}
                              </span>
                              <div>
                                <p className="font-medium text-navy-900 text-sm">{topic.topic}</p>
                                <p className="text-xs text-surface-400">
                                  {topic.plan_count} plan{topic.plan_count !== 1 ? 's' : ''} · {topic.completed_count} completed
                                </p>
                              </div>
                            </div>
                            <div className="text-right">
                              <p className="font-bold text-emerald-600 text-sm">{topic.avg_completion}%</p>
                              <p className="text-[11px] text-surface-300">avg completion</p>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Learning Styles Tab */}
              {activeTab === 'learning' && learningStyleData && (
                <div className="space-y-6">
                  <div className="bg-white rounded-xl border border-surface-200/80 p-6">
                    <h3 className="text-[15px] font-semibold text-navy-900 mb-4">Performance by Learning Style</h3>
                    {Object.keys(learningStyleData.by_learning_style).length > 0 ? (
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        {Object.entries(learningStyleData.by_learning_style).map(([style, data]) => (
                          <div
                            key={style}
                            className="p-4 rounded-xl border"
                            style={{
                              backgroundColor: `${LEARNING_STYLE_COLORS[style]}08`,
                              borderColor: `${LEARNING_STYLE_COLORS[style]}30`
                            }}
                          >
                            <div className="mb-2" style={{ color: LEARNING_STYLE_COLORS[style] }}>
                              {StyleIcons[style] || StyleIcons.reading}
                            </div>
                            <p className="font-semibold capitalize text-navy-900 text-sm">{style}</p>
                            <p className="text-xs text-surface-400">{data.plan_count} plans</p>
                            <div className="mt-2 pt-2 border-t" style={{ borderColor: `${LEARNING_STYLE_COLORS[style]}20` }}>
                              <p className="text-lg font-bold" style={{ color: LEARNING_STYLE_COLORS[style] }}>
                                {data.avg_completion}%
                              </p>
                              <p className="text-[11px] text-surface-300">avg completion</p>
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-surface-400 text-center py-8 text-sm">No learning style data yet</p>
                    )}
                  </div>

                  <div className="bg-white rounded-xl border border-surface-200/80 p-6">
                    <h3 className="text-[15px] font-semibold text-navy-900 mb-4">Engagement by Resource Type</h3>
                    {Object.keys(learningStyleData.by_resource_type).length > 0 ? (
                      <div className="space-y-4">
                        {Object.entries(learningStyleData.by_resource_type).map(([type, data]) => (
                          <div key={type} className="flex items-center gap-4">
                            <div className="w-32 text-sm font-medium text-navy-800 capitalize">
                              {type.replace('_', ' ')}
                            </div>
                            <div className="flex-1">
                              <div className="h-6 bg-surface-100 rounded-full overflow-hidden">
                                <div
                                  className="h-full rounded-full transition-all"
                                  style={{
                                    width: `${data.engagement_rate}%`,
                                    backgroundColor: RESOURCE_TYPE_COLORS[type] || COLORS.secondary
                                  }}
                                />
                              </div>
                            </div>
                            <div className="w-24 text-right">
                              <span className="font-bold text-sm" style={{ color: RESOURCE_TYPE_COLORS[type] || COLORS.secondary }}>
                                {data.engagement_rate}%
                              </span>
                              <span className="text-surface-300 text-xs ml-1">({data.clicked}/{data.total})</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-surface-400 text-center py-8 text-sm">No resource engagement data yet</p>
                    )}
                  </div>
                </div>
              )}

              {/* Trends Tab */}
              {activeTab === 'trends' && timeData && (
                <div className="space-y-6">
                  <div className="bg-white rounded-xl border border-surface-200/80 p-6">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-[15px] font-semibold text-navy-900">Study Activity Over Time</h3>
                      <div className="flex items-center gap-1">
                        {[
                          { label: '7d', value: 7 },
                          { label: '30d', value: 30 },
                          { label: '90d', value: 90 },
                          { label: 'All', value: 365 },
                        ].map(opt => (
                          <button
                            key={opt.value}
                            onClick={() => handleDaysChange(opt.value)}
                            className={`px-2.5 py-1 rounded-lg text-[11px] font-semibold transition-colors ${
                              selectedDays === opt.value
                                ? 'bg-navy-800 text-white'
                                : 'text-surface-400 hover:text-navy-800 hover:bg-surface-100'
                            }`}
                          >
                            {opt.label}
                          </button>
                        ))}
                      </div>
                    </div>
                    {timeData.study_plans_over_time.length > 0 ? (
                      <div className="h-64">
                        <VictoryChart
                          theme={VictoryTheme.material}
                          height={250}
                          padding={{ top: 20, bottom: 50, left: 60, right: 20 }}
                        >
                          <VictoryAxis
                            tickFormat={(t) => {
                              const date = new Date(t)
                              return `${date.getMonth() + 1}/${date.getDate()}`
                            }}
                            style={{
                              tickLabels: { fontSize: 10, angle: -45 }
                            }}
                          />
                          <VictoryAxis
                            dependentAxis
                            label="Plans Created"
                            style={{
                              axisLabel: { fontSize: 12, padding: 40 }
                            }}
                          />
                          <VictoryBar
                            data={timeData.study_plans_over_time.map(d => ({
                              x: d.date,
                              y: d.plans_created
                            }))}
                            style={{
                              data: { fill: COLORS.primary }
                            }}
                          />
                        </VictoryChart>
                      </div>
                    ) : (
                      <p className="text-surface-400 text-center py-8 text-sm">No activity data yet</p>
                    )}
                  </div>

                  <div className="bg-white rounded-xl border border-surface-200/80 p-6">
                    <h3 className="text-[15px] font-semibold text-navy-900 mb-4">Resource Engagement Over Time</h3>
                    {timeData.engagement_over_time.length > 0 ? (
                      <div className="h-64">
                        <VictoryChart
                          theme={VictoryTheme.material}
                          height={250}
                          padding={{ top: 20, bottom: 50, left: 60, right: 20 }}
                        >
                          <VictoryAxis
                            tickFormat={(t) => {
                              const date = new Date(t)
                              return `${date.getMonth() + 1}/${date.getDate()}`
                            }}
                            style={{
                              tickLabels: { fontSize: 10, angle: -45 }
                            }}
                          />
                          <VictoryAxis
                            dependentAxis
                            label="Resources Engaged"
                            style={{
                              axisLabel: { fontSize: 12, padding: 40 }
                            }}
                          />
                          <VictoryArea
                            data={timeData.engagement_over_time.map(d => ({
                              x: d.date,
                              y: d.resources_engaged
                            }))}
                            style={{
                              data: { fill: `${COLORS.success}40`, stroke: COLORS.success, strokeWidth: 2 }
                            }}
                          />
                        </VictoryChart>
                      </div>
                    ) : (
                      <p className="text-surface-400 text-center py-8 text-sm">No engagement data yet</p>
                    )}
                  </div>
                </div>
              )}

              {/* Mood Impact Tab */}
              {activeTab === 'mood' && moodData && (
                <div className="space-y-6">
                  <div className="bg-white rounded-xl border border-surface-200/80 p-6">
                    <h3 className="text-[15px] font-semibold text-navy-900 mb-4">Your Mood Distribution</h3>
                    {Object.keys(moodData.mood_distribution).length > 0 ? (
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        {Object.entries(moodData.mood_distribution).map(([mood, data]) => (
                          <div key={mood} className="bg-surface-50/50 rounded-xl p-4 text-center border border-surface-100">
                            <div className="w-10 h-10 rounded-xl bg-navy-800/[0.06] flex items-center justify-center text-navy-800 mx-auto mb-2">
                              {getMoodSvg(mood)}
                            </div>
                            <p className="font-medium capitalize text-navy-900 text-sm">{mood}</p>
                            <p className="text-2xl font-bold text-navy-900">{data.count}</p>
                            <p className="text-[11px] text-surface-300">
                              Avg energy: {data.avg_energy}/5
                            </p>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-surface-400 text-center py-8 text-sm">No mood data yet. Start logging your mood!</p>
                    )}
                  </div>

                  <div className="bg-white rounded-xl border border-surface-200/80 p-6">
                    <h3 className="text-[15px] font-semibold text-navy-900 mb-4">Study Effectiveness by Mood</h3>
                    <p className="text-xs text-surface-400 mb-4">
                      How your mood affects your learning outcomes
                    </p>
                    {Object.keys(moodData.effectiveness_by_mood).length > 0 ? (
                      <div className="space-y-3">
                        {Object.entries(moodData.effectiveness_by_mood)
                          .sort((a, b) => b[1].avg_improvement - a[1].avg_improvement)
                          .map(([mood, data]) => (
                            <div key={mood} className="flex items-center gap-4">
                              <div className="w-32 flex items-center gap-2">
                                <span className="text-navy-800">{getMoodSvg(mood)}</span>
                                <span className="font-medium capitalize text-navy-800 text-sm">{mood}</span>
                              </div>
                              <div className="flex-1 h-5 bg-surface-100 rounded-full overflow-hidden">
                                <div
                                  className={`h-full rounded-full transition-all ${
                                    data.avg_improvement > 0 ? 'bg-emerald-500' : 'bg-red-400'
                                  }`}
                                  style={{
                                    width: `${Math.min(100, Math.abs(data.avg_improvement) * 10)}%`
                                  }}
                                />
                              </div>
                              <div className="w-24 text-right">
                                <span className={`font-bold text-sm ${
                                  data.avg_improvement > 0 ? 'text-emerald-600' : 'text-red-600'
                                }`}>
                                  {data.avg_improvement > 0 ? '+' : ''}{data.avg_improvement}%
                                </span>
                              </div>
                            </div>
                          ))}
                      </div>
                    ) : (
                      <div className="text-center py-8">
                        <p className="text-surface-400 text-sm">No effectiveness data by mood yet.</p>
                        <p className="text-xs text-surface-300 mt-2">
                          Complete study plans and log your mood to see correlations.
                        </p>
                      </div>
                    )}
                  </div>

                  {/* Insights */}
                  <div className="bg-navy-800/[0.03] rounded-xl border border-navy-800/10 p-6">
                    <h3 className="text-[15px] font-semibold mb-2 text-navy-900">Mood Insights</h3>
                    <div className="space-y-2 text-sm text-navy-800/70">
                      {Object.keys(moodData.mood_distribution).length > 0 && (
                        <>
                          <p>
                            Your most common mood is{' '}
                            <strong className="capitalize text-navy-900">
                              {Object.entries(moodData.mood_distribution)
                                .sort((a, b) => b[1].count - a[1].count)[0]?.[0] || 'unknown'}
                            </strong>
                          </p>
                          {Object.keys(moodData.effectiveness_by_mood).length > 0 && (
                            <p>
                              You learn best when feeling{' '}
                              <strong className="capitalize text-navy-900">
                                {Object.entries(moodData.effectiveness_by_mood)
                                  .sort((a, b) => b[1].avg_improvement - a[1].avg_improvement)[0]?.[0] || 'focused'}
                              </strong>
                            </p>
                          )}
                        </>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {/* Research Tab */}
              {activeTab === 'research' && (
                <div className="space-y-6">
                  {!statsData || statsData.sample_size === 0 ? (
                    <div className="bg-white rounded-xl p-5 border border-surface-200/80 text-center py-16">
                      <div className="w-16 h-16 rounded-2xl bg-navy-800/[0.04] flex items-center justify-center text-navy-800 mx-auto mb-4">
                        <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0112 15a9.065 9.065 0 00-6.23.693L5 14.5m14.8.8l1.402 5.235c.292 1.092-.757 2.075-1.871 1.822L18 21.89a9 9 0 01-12 0l-1.331.467c-1.114.253-2.163-.73-1.87-1.822L4.2 15.3" />
                        </svg>
                      </div>
                      <h3 className="text-lg font-display font-semibold text-navy-900 mb-2">No Statistical Data Yet</h3>
                      <p className="text-surface-400 text-sm max-w-md mx-auto">
                        Complete study plans with before/after scores to unlock statistical analysis.
                        You need at least 2 completed plans with scores.
                      </p>
                    </div>
                  ) : (
                    <>
                      {/* Export Button */}
                      <div className="flex justify-end mb-4">
                        <button
                          onClick={exportCSV}
                          className="flex items-center gap-1.5 px-3.5 py-2 rounded-lg text-[12px] font-semibold text-navy-600 hover:text-navy-800 hover:bg-surface-100 border border-surface-200/80 transition-colors"
                        >
                          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                            <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
                          </svg>
                          Export CSV
                        </button>
                      </div>

                      {/* Sample Info Card */}
                      <div className="bg-white rounded-xl p-5 border border-surface-200/80">
                        <div className="flex items-center justify-between mb-3">
                          <h3 className="text-[15px] font-semibold text-navy-900">Sample Information</h3>
                          <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                            statsData.sample_adequacy?.is_adequate
                              ? 'bg-emerald-100 text-emerald-700'
                              : 'bg-amber-100 text-amber-700'
                          }`}>
                            {statsData.sample_adequacy?.is_adequate ? 'Adequate' : 'More data needed'}
                          </span>
                        </div>
                        <div className="flex items-center gap-4">
                          <div className="text-3xl font-bold text-navy-800">
                            n = {statsData.sample_size}
                          </div>
                          {statsData.sample_adequacy?.power_note && (
                            <p className="text-xs text-surface-400">{statsData.sample_adequacy.power_note}</p>
                          )}
                        </div>
                      </div>

                      {/* Descriptive Statistics */}
                      <div className="bg-white rounded-xl p-5 border border-surface-200/80">
                        <h3 className="text-[15px] font-semibold text-navy-900 mb-4">Descriptive Statistics</h3>
                        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
                          {[
                            { label: 'Mean Improvement', value: statsData.descriptive_statistics?.mean_improvement, color: 'text-navy-800' },
                            { label: 'Median', value: statsData.descriptive_statistics?.median_improvement, color: 'text-navy-800' },
                            { label: 'Std Dev', value: statsData.descriptive_statistics?.std_improvement, color: 'text-purple-600' },
                            { label: 'Min', value: statsData.descriptive_statistics?.min_improvement, color: 'text-surface-500' },
                            { label: 'Max', value: statsData.descriptive_statistics?.max_improvement, color: 'text-surface-500' }
                          ].map((stat, i) => (
                            <div key={i} className="bg-surface-50/50 rounded-xl p-4 text-center border border-surface-100">
                              <p className="text-[11px] text-surface-400 mb-1 uppercase tracking-wider font-medium">{stat.label}</p>
                              <p className={`text-xl font-bold ${stat.color}`}>
                                {stat.value?.toFixed(2) ?? '—'}
                              </p>
                            </div>
                          ))}
                        </div>
                      </div>

                      {/* Inferential Statistics */}
                      {statsData.inferential_statistics && (
                        <div className="bg-white rounded-xl p-5 border border-surface-200/80">
                          <h3 className="text-[15px] font-semibold text-navy-900 mb-4">Inferential Statistics</h3>
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="space-y-2">
                              <div className="flex justify-between items-center p-3 bg-surface-50/50 rounded-xl border border-surface-100">
                                <span className="text-xs text-surface-400 uppercase tracking-wider font-medium">t-statistic</span>
                                <span className="font-bold text-navy-900 text-sm">
                                  {statsData.inferential_statistics.t_statistic?.toFixed(2) ?? '—'}
                                </span>
                              </div>
                              <div className="flex justify-between items-center p-3 bg-surface-50/50 rounded-xl border border-surface-100">
                                <span className="text-xs text-surface-400 uppercase tracking-wider font-medium">p-value</span>
                                <span className={`font-bold text-sm ${
                                  statsData.inferential_statistics.p_value < 0.05
                                    ? 'text-emerald-600'
                                    : statsData.inferential_statistics.p_value < 0.1
                                      ? 'text-amber-600'
                                      : 'text-red-600'
                                }`}>
                                  {statsData.inferential_statistics.p_value?.toFixed(4) ?? '—'}
                                </span>
                              </div>
                              <div className="flex justify-between items-center p-3 bg-surface-50/50 rounded-xl border border-surface-100">
                                <span className="text-xs text-surface-400 uppercase tracking-wider font-medium">Significance</span>
                                <span className={`px-2.5 py-0.5 rounded-full text-[11px] font-medium ${
                                  statsData.inferential_statistics.significant
                                    ? 'bg-emerald-100 text-emerald-700'
                                    : 'bg-red-100 text-red-700'
                                }`}>
                                  {statsData.inferential_statistics.significant ? 'Yes' : 'No'}
                                </span>
                              </div>
                            </div>
                            <div className="space-y-2">
                              <div className="flex justify-between items-center p-3 bg-surface-50/50 rounded-xl border border-surface-100">
                                <span className="text-xs text-surface-400 uppercase tracking-wider font-medium">Cohen&apos;s d</span>
                                <div className="flex items-center gap-2">
                                  <span className="font-bold text-navy-900 text-sm">
                                    {statsData.inferential_statistics.cohens_d?.toFixed(2) ?? '—'}
                                  </span>
                                  {statsData.inferential_statistics.effect_size_interpretation && (
                                    <span className={`px-2 py-0.5 rounded-full text-[11px] font-medium ${
                                      statsData.inferential_statistics.effect_size_interpretation === 'large'
                                        ? 'bg-purple-100 text-purple-700'
                                        : statsData.inferential_statistics.effect_size_interpretation === 'medium'
                                          ? 'bg-blue-100 text-blue-700'
                                          : 'bg-surface-100 text-surface-500'
                                    }`}>
                                      {statsData.inferential_statistics.effect_size_interpretation}
                                    </span>
                                  )}
                                </div>
                              </div>
                              <div className="flex justify-between items-center p-3 bg-surface-50/50 rounded-xl border border-surface-100">
                                <span className="text-xs text-surface-400 uppercase tracking-wider font-medium">95% CI</span>
                                <span className="font-bold text-navy-900 text-sm font-mono">
                                  [{statsData.inferential_statistics.confidence_interval_95?.lower?.toFixed(2) ?? '—'},{' '}
                                  {statsData.inferential_statistics.confidence_interval_95?.upper?.toFixed(2) ?? '—'}]
                                </span>
                              </div>
                            </div>
                          </div>
                        </div>
                      )}

                      {/* Before/After Chart */}
                      {statsData.paired_scores && statsData.paired_scores.length > 0 && (
                        <div className="bg-white rounded-xl p-5 border border-surface-200/80">
                          <h3 className="text-[15px] font-semibold text-navy-900 mb-4">Before vs After Scores</h3>
                          <div className="h-72">
                            <VictoryChart
                              theme={VictoryTheme.material}
                              height={270}
                              domainPadding={{ x: 30 }}
                              padding={{ top: 20, bottom: 60, left: 60, right: 20 }}
                            >
                              <VictoryAxis
                                tickFormat={(t) => {
                                  const entry = statsData.paired_scores.slice(0, 10)[t]
                                  return entry ? entry.topic.substring(0, 12) : ''
                                }}
                                style={{
                                  tickLabels: { fontSize: 9, angle: -30, textAnchor: 'end' }
                                }}
                              />
                              <VictoryAxis
                                dependentAxis
                                label="Score"
                                style={{
                                  axisLabel: { fontSize: 12, padding: 40 }
                                }}
                              />
                              <VictoryBar
                                data={statsData.paired_scores.slice(0, 10).map((d, i) => ({
                                  x: i,
                                  y: d.before_score
                                }))}
                                style={{
                                  data: { fill: COLORS.primary, width: 12 }
                                }}
                              />
                              <VictoryBar
                                data={statsData.paired_scores.slice(0, 10).map((d, i) => ({
                                  x: i + 0.3,
                                  y: d.after_score
                                }))}
                                style={{
                                  data: { fill: COLORS.success, width: 12 }
                                }}
                              />
                            </VictoryChart>
                          </div>
                          <div className="flex justify-center gap-6 mt-2">
                            <div className="flex items-center gap-2">
                              <div className="w-3 h-3 rounded" style={{ backgroundColor: COLORS.primary }}></div>
                              <span className="text-xs text-surface-400">Before</span>
                            </div>
                            <div className="flex items-center gap-2">
                              <div className="w-3 h-3 rounded" style={{ backgroundColor: COLORS.success }}></div>
                              <span className="text-xs text-surface-400">After</span>
                            </div>
                          </div>
                        </div>
                      )}

                      {/* Interpretation Box */}
                      {statsData.interpretation && (
                        <div className="bg-navy-800/[0.03] rounded-xl border border-navy-800/10 p-6">
                          <h3 className="text-[15px] font-semibold text-navy-900 mb-2">Interpretation</h3>
                          <p className="text-navy-800/70 text-sm italic leading-relaxed">{statsData.interpretation}</p>
                        </div>
                      )}
                    </>
                  )}
                </div>
              )}
            </>
          )}
        </div>

        {/* Footer */}
        <div className="bg-surface-50/50 px-6 py-4 border-t border-surface-100">
          <div className="flex items-center justify-between">
            <p className="text-[13px] text-surface-300">
              Data refreshed just now
            </p>
            <button
              onClick={handleClose}
              className="px-5 py-2 bg-navy-800 text-white rounded-xl hover:bg-navy-900 transition-colors font-medium text-sm"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

/* ── Helper Components ── */
function StatCard({ title, value, subtitle, icon, color, iconColor }) {
  return (
    <div className={`rounded-xl border p-4 ${color}`}>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-[11px] text-surface-400 uppercase tracking-wider font-medium">{title}</p>
          <p className="text-2xl font-bold text-navy-900 mt-1">{value}</p>
          <p className="text-[11px] text-surface-300 mt-1">{subtitle}</p>
        </div>
        <div className={`w-9 h-9 rounded-lg flex items-center justify-center ${iconColor}`}>
          {icon}
        </div>
      </div>
    </div>
  )
}

function ProgressBar({ label, value, max, color }) {
  const percentage = max > 0 ? (value / max) * 100 : 0
  return (
    <div>
      <div className="flex justify-between text-xs mb-1.5">
        <span className="text-surface-400 font-medium">{label}</span>
        <span className="font-medium text-navy-900">{value}/{max}</span>
      </div>
      <div className="h-2.5 bg-surface-100 rounded-full overflow-hidden">
        <div
          className={`h-full ${color} rounded-full transition-all duration-500`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  )
}
