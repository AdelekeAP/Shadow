import { useState, useEffect } from 'react'
import { VictoryPie, VictoryChart, VictoryLine, VictoryAxis, VictoryBar } from 'victory'
import api from '../services/api'

export default function CGPADashboard() {
  const [cgpaData, setCgpaData] = useState(null)
  const [analytics, setAnalytics] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [activeTab, setActiveTab] = useState('overview')

  useEffect(() => { fetchData() }, [])

  const fetchData = async () => {
    try {
      setLoading(true)
      const [dashRes, anaRes] = await Promise.all([
        api.get('/api/v1/cgpa/dashboard'),
        api.get('/api/v1/cgpa/analytics'),
      ])
      setCgpaData(dashRes.data.data)
      setAnalytics(anaRes.data.analytics)
      setError(null)
    } catch {
      setError('Failed to load CGPA data')
    } finally { setLoading(false) }
  }

  const fmt = (v, d = 2) => {
    if (v == null) return '0.00'
    const n = typeof v === 'number' ? v : parseFloat(v)
    return isNaN(n) ? '0.00' : n.toFixed(d)
  }

  const classify = (gpa) => {
    if (gpa >= 4.50) return { label: 'First Class',         cls: 'text-emerald-600', bg: 'bg-emerald-50 border-emerald-200/60' }
    if (gpa >= 3.50) return { label: 'Second Class Upper',  cls: 'text-blue-600',    bg: 'bg-blue-50 border-blue-200/60' }
    if (gpa >= 2.50) return { label: 'Second Class Lower',  cls: 'text-amber-600',   bg: 'bg-amber-50 border-amber-200/60' }
    if (gpa >= 1.50) return { label: 'Third Class',         cls: 'text-orange-600',  bg: 'bg-orange-50 border-orange-200/60' }
    return                   { label: 'Pass',                cls: 'text-red-600',     bg: 'bg-red-50 border-red-200/60' }
  }

  const gradeColor = (g) => {
    if (g === 'A') return 'bg-emerald-500 text-white'
    if (g === 'B') return 'bg-blue-500 text-white'
    if (g === 'C') return 'bg-amber-500 text-white'
    if (g === 'D') return 'bg-orange-500 text-white'
    if (g === 'E') return 'bg-red-400 text-white'
    return 'bg-red-600 text-white'
  }

  /* ── Loading ── */
  if (loading) return (
    <div className="space-y-4">
      {[1, 2, 3].map(i => (
        <div key={i} className="rounded-2xl border border-surface-200/60 bg-white p-6 animate-pulse">
          <div className="h-5 w-32 bg-surface-100 rounded-lg mb-3" />
          <div className="h-10 w-24 bg-surface-100/60 rounded-lg mb-2" />
          <div className="h-3 w-48 bg-surface-100/40 rounded-lg" />
        </div>
      ))}
    </div>
  )

  /* ── Error ── */
  if (error) return (
    <div className="rounded-2xl border border-red-200/60 bg-red-50 p-5 flex items-center gap-3">
      <svg className="w-5 h-5 text-red-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9 3.75h.008v.008H12v-.008Z" />
      </svg>
      <span className="text-[13px] font-medium text-red-700">{error}</span>
      <button onClick={fetchData} className="ml-auto text-[12px] font-semibold text-red-600 hover:text-red-800 transition-colors">Retry</button>
    </div>
  )

  /* ── Empty ── */
  if (!cgpaData) return (
    <div className="flex flex-col items-center py-16">
      <div className="w-14 h-14 rounded-2xl bg-surface-100 flex items-center justify-center mb-4">
        <svg className="w-6 h-6 text-surface-300" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
          <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 0 1 3 19.875v-6.75ZM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V8.625ZM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V4.125Z" />
        </svg>
      </div>
      <p className="text-[14px] font-semibold text-navy-900 mb-1">No CGPA data yet</p>
      <p className="text-[12px] text-surface-400">Start adding courses and grades to see your analytics</p>
    </div>
  )

  const currentClass = classify(cgpaData.current.cgpa)
  const predClass = classify(cgpaData.predictions.predicted_cgpa)
  const tabs = [
    { key: 'overview',   label: 'Overview' },
    { key: 'analytics',  label: 'Analytics' },
    { key: 'breakdown',  label: 'Breakdown' },
  ]

  return (
    <div className="space-y-5">

      {/* ── Tab bar ── */}
      <div className="flex items-center gap-1 p-1 rounded-xl bg-surface-100/80 border border-surface-200/60 w-fit">
        {tabs.map(t => (
          <button
            key={t.key}
            onClick={() => setActiveTab(t.key)}
            className={`px-4 py-1.5 rounded-lg text-[12px] font-semibold transition-all ${
              activeTab === t.key
                ? 'bg-white text-navy-800 shadow-sm'
                : 'text-surface-400 hover:text-navy-700'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* ══════════ OVERVIEW ══════════ */}
      {activeTab === 'overview' && (
        <div className="space-y-5">

          {/* ── Current CGPA hero card ── */}
          <div className="rounded-2xl border border-surface-200/60 bg-white overflow-hidden">
            <div className="p-6 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
              <div>
                <p className="text-[11px] font-semibold uppercase tracking-wider text-surface-400 mb-1">Current CGPA</p>
                <div className="flex items-baseline gap-2">
                  <span className={`font-display text-[3rem] font-bold leading-none tracking-tight ${currentClass.cls}`}>
                    {fmt(cgpaData.current.cgpa)}
                  </span>
                  <span className="text-[13px] text-surface-300 font-mono">/ 5.00</span>
                </div>
                <p className="text-[12px] text-surface-400 mt-1.5">
                  {cgpaData.current.total_credits} credits completed
                </p>
              </div>
              <div className={`px-4 py-2.5 rounded-xl border ${currentClass.bg}`}>
                <p className="text-[10px] font-semibold uppercase tracking-wider text-surface-400 mb-0.5">Classification</p>
                <p className={`text-[15px] font-bold ${currentClass.cls}`}>{currentClass.label}</p>
              </div>
            </div>
            {/* Progress bar to 5.0 */}
            <div className="h-1.5 bg-surface-100">
              <div
                className="h-full rounded-r-full bg-gradient-to-r from-navy-800 to-navy-600 transition-all duration-700"
                style={{ width: `${Math.min((cgpaData.current.cgpa / 5) * 100, 100)}%` }}
              />
            </div>
          </div>

          {/* ── Stat tiles ── */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Predicted */}
            <div className="rounded-2xl border border-surface-200/60 bg-white p-5">
              <div className="flex items-center gap-2 mb-3">
                <div className="w-8 h-8 rounded-lg bg-navy-800/[0.06] flex items-center justify-center">
                  <svg className="w-4 h-4 text-navy-700" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 18 9 11.25l4.306 4.306a11.95 11.95 0 0 1 5.814-5.518l2.74-1.22m0 0-5.94-2.281m5.94 2.28-2.28 5.941" />
                  </svg>
                </div>
                <span className="text-[11px] font-semibold uppercase tracking-wider text-surface-400">Predicted CGPA</span>
              </div>
              <p className={`font-display text-[28px] font-bold leading-none ${predClass.cls}`}>
                {fmt(cgpaData.predictions.predicted_cgpa)}
              </p>
              <p className="text-[11px] text-surface-400 mt-1.5">Based on current performance</p>
            </div>

            {/* Courses */}
            <div className="rounded-2xl border border-surface-200/60 bg-white p-5">
              <div className="flex items-center gap-2 mb-3">
                <div className="w-8 h-8 rounded-lg bg-navy-800/[0.06] flex items-center justify-center">
                  <svg className="w-4 h-4 text-navy-700" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.042A8.967 8.967 0 0 0 6 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 0 1 6 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 0 1 6-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0 0 18 18a8.967 8.967 0 0 0-6 2.292m0-14.25v14.25" />
                  </svg>
                </div>
                <span className="text-[11px] font-semibold uppercase tracking-wider text-surface-400">Total Courses</span>
              </div>
              <p className="font-display text-[28px] font-bold leading-none text-navy-900">
                {cgpaData.total_courses}
              </p>
              <p className="text-[11px] text-surface-400 mt-1.5">{cgpaData.semesters.length} semester{cgpaData.semesters.length !== 1 ? 's' : ''}</p>
            </div>

            {/* Target */}
            <div className="rounded-2xl border border-surface-200/60 bg-white p-5">
              <div className="flex items-center gap-2 mb-3">
                <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${
                  cgpaData.target_analysis.is_achievable ? 'bg-emerald-500/10' : 'bg-red-500/10'
                }`}>
                  <svg className={`w-4 h-4 ${cgpaData.target_analysis.is_achievable ? 'text-emerald-600' : 'text-red-500'}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                    {cgpaData.target_analysis.is_achievable
                      ? <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75 11.25 15 15 9.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
                      : <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" />
                    }
                  </svg>
                </div>
                <span className="text-[11px] font-semibold uppercase tracking-wider text-surface-400">Required GPA</span>
              </div>
              <p className={`font-display text-[28px] font-bold leading-none ${
                cgpaData.target_analysis.is_achievable ? 'text-emerald-600' : 'text-red-600'
              }`}>
                {fmt(cgpaData.target_analysis.required_gpa)}
              </p>
              <p className="text-[11px] text-surface-400 mt-1">
                Target: {fmt(cgpaData.target_analysis.target_cgpa)}
              </p>
              <span className={`inline-block mt-1.5 px-2 py-0.5 rounded-md text-[10px] font-semibold ${
                cgpaData.target_analysis.is_achievable
                  ? 'bg-emerald-50 text-emerald-700 border border-emerald-200/60'
                  : 'bg-red-50 text-red-600 border border-red-200/60'
              }`}>
                {cgpaData.target_analysis.difficulty}
              </span>
            </div>
          </div>

          {/* ── Semester trend chart ── */}
          {analytics?.semester_gpa_history?.length > 1 && (
            <div className="rounded-2xl border border-surface-200/60 bg-white p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-[14px] font-semibold text-navy-900">Semester Trend</h3>
                {analytics.trend && (
                  <span className={`px-2.5 py-1 rounded-lg text-[11px] font-semibold border ${
                    analytics.trend === 'Improving' ? 'bg-emerald-50 text-emerald-700 border-emerald-200/60' :
                    analytics.trend === 'Declining' ? 'bg-red-50 text-red-600 border-red-200/60' :
                    'bg-surface-100 text-surface-400 border-surface-200/60'
                  }`}>
                    {analytics.trend}
                  </span>
                )}
              </div>
              <div className="h-56">
                <VictoryChart
                  height={220}
                  padding={{ top: 16, bottom: 36, left: 44, right: 16 }}
                >
                  <VictoryAxis
                    label="Semester"
                    style={{
                      axis: { stroke: '#e5e7ee' },
                      axisLabel: { fontSize: 10, padding: 28, fill: '#9ba2b5', fontFamily: 'Plus Jakarta Sans' },
                      tickLabels: { fontSize: 9, fill: '#9ba2b5', fontFamily: 'Plus Jakarta Sans' },
                      grid: { stroke: 'none' },
                    }}
                  />
                  <VictoryAxis
                    dependentAxis
                    domain={[0, 5.0]}
                    style={{
                      axis: { stroke: '#e5e7ee' },
                      axisLabel: { fontSize: 10, padding: 36, fill: '#9ba2b5', fontFamily: 'Plus Jakarta Sans' },
                      tickLabels: { fontSize: 9, fill: '#9ba2b5', fontFamily: 'JetBrains Mono' },
                      grid: { stroke: '#f1f3f6', strokeDasharray: '4' },
                    }}
                  />
                  <VictoryLine
                    data={analytics.semester_gpa_history.map((gpa, i) => ({
                      x: analytics.semester_names?.[i] || `Sem ${i + 1}`,
                      y: gpa,
                    }))}
                    style={{
                      data: { stroke: '#1e3a8a', strokeWidth: 2.5 },
                    }}
                    interpolation="monotoneX"
                  />
                </VictoryChart>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ══════════ ANALYTICS ══════════ */}
      {activeTab === 'analytics' && analytics && (
        <div className="space-y-5">

          {/* ── Performance stats ── */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {[
              { label: 'Best Semester', value: fmt(analytics.best_semester_gpa), accent: 'emerald' },
              { label: 'Average Semester', value: fmt(analytics.average_semester_gpa), accent: 'navy' },
              { label: 'Worst Semester', value: fmt(analytics.worst_semester_gpa), accent: 'amber' },
            ].map(s => {
              const colors = {
                emerald: 'from-emerald-600/5 to-emerald-600/[0.02] border-emerald-200/60 text-emerald-600',
                navy:    'from-navy-800/5 to-navy-800/[0.02] border-navy-200/60 text-navy-900',
                amber:   'from-amber-500/5 to-amber-500/[0.02] border-amber-200/60 text-amber-600',
              }
              return (
                <div key={s.label} className={`rounded-2xl border bg-gradient-to-br p-5 ${colors[s.accent]}`}>
                  <p className="text-[11px] font-semibold uppercase tracking-wider text-surface-400 mb-1">{s.label}</p>
                  <p className={`font-display text-[32px] font-bold leading-none ${colors[s.accent].split(' ').pop()}`}>{s.value}</p>
                </div>
              )
            })}
          </div>

          {/* ── Grade distribution ── */}
          {analytics.grade_distribution && Object.keys(analytics.grade_distribution).length > 0 && (
            <div className="rounded-2xl border border-surface-200/60 bg-white p-6">
              <h3 className="text-[14px] font-semibold text-navy-900 mb-5">Grade Distribution</h3>
              <div className="flex flex-col md:flex-row items-center gap-6">
                <div className="w-full md:w-1/2 max-w-[280px]">
                  <VictoryPie
                    data={Object.entries(analytics.grade_distribution).map(([grade, count]) => ({
                      x: grade,
                      y: count,
                      label: `${grade}: ${count}`,
                    }))}
                    colorScale={['#059669', '#2563eb', '#d97706', '#ea580c', '#dc2626', '#6b7280']}
                    height={260}
                    innerRadius={60}
                    padAngle={2}
                    style={{
                      labels: { fontSize: 11, fill: '#172554', fontFamily: 'Plus Jakarta Sans', fontWeight: 600 },
                    }}
                  />
                </div>
                <div className="w-full md:w-1/2 space-y-2">
                  {Object.entries(analytics.grade_distribution)
                    .sort(([, a], [, b]) => b - a)
                    .map(([grade, count]) => {
                      const total = Object.values(analytics.grade_distribution).reduce((s, c) => s + c, 0)
                      const pct = total > 0 ? (count / total) * 100 : 0
                      return (
                        <div key={grade} className="flex items-center gap-3">
                          <span className={`w-7 h-7 rounded-lg ${gradeColor(grade)} text-[11px] font-bold flex items-center justify-center flex-shrink-0`}>{grade}</span>
                          <div className="flex-1">
                            <div className="flex items-baseline justify-between mb-1">
                              <span className="text-[12px] font-semibold text-navy-800">{count} course{count !== 1 ? 's' : ''}</span>
                              <span className="text-[10px] text-surface-400 font-mono">{pct.toFixed(0)}%</span>
                            </div>
                            <div className="h-1.5 bg-surface-100 rounded-full overflow-hidden">
                              <div className="h-full bg-navy-800/20 rounded-full" style={{ width: `${pct}%` }} />
                            </div>
                          </div>
                        </div>
                      )
                    })}
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ══════════ BREAKDOWN ══════════ */}
      {activeTab === 'breakdown' && (
        <div className="space-y-4">
          {cgpaData.semesters.map((semester, index) => {
            const semCredits = semester.courses ? semester.courses.reduce((s, c) => s + (c.credits || 0), 0) : 0
            const semQP = semester.courses ? semester.courses.reduce((s, c) => s + ((c.grade_point || 0) * (c.credits || 0)), 0) : 0
            const semGPA = semCredits > 0 ? semQP / semCredits : 0
            const semClass = classify(semGPA)

            return (
              <div key={index} className="rounded-2xl border border-surface-200/60 bg-white overflow-hidden">
                {/* Semester header */}
                <div className="flex items-center justify-between px-5 py-4 border-b border-surface-100">
                  <div>
                    <h4 className="text-[14px] font-semibold text-navy-900">{semester.name}</h4>
                    <p className="text-[11px] text-surface-400">{semCredits} credits</p>
                  </div>
                  <div className="text-right">
                    <p className={`font-mono text-[20px] font-bold ${semClass.cls}`}>{fmt(semGPA)}</p>
                    <p className={`text-[10px] font-semibold ${semClass.cls}`}>{semClass.label}</p>
                  </div>
                </div>

                {/* Course table */}
                <div className="overflow-x-auto">
                  <table className="w-full text-[12px]">
                    <thead>
                      <tr className="border-b border-surface-100 bg-surface-50/50">
                        <th className="text-left py-2.5 px-5 font-semibold text-surface-400 uppercase tracking-wider text-[10px]">Course</th>
                        <th className="text-center py-2.5 px-3 font-semibold text-surface-400 uppercase tracking-wider text-[10px]">Credits</th>
                        <th className="text-center py-2.5 px-3 font-semibold text-surface-400 uppercase tracking-wider text-[10px]">Score</th>
                        <th className="text-center py-2.5 px-3 font-semibold text-surface-400 uppercase tracking-wider text-[10px]">Grade</th>
                        <th className="text-center py-2.5 px-3 font-semibold text-surface-400 uppercase tracking-wider text-[10px]">Points</th>
                      </tr>
                    </thead>
                    <tbody>
                      {semester.courses?.map((course, idx) => (
                        <tr key={idx} className="border-b border-surface-100/60 last:border-0 hover:bg-surface-50/50 transition-colors">
                          <td className="py-3 px-5">
                            <p className="font-mono font-semibold text-navy-900 text-[12px]">{course.code}</p>
                            <p className="text-[11px] text-surface-400 mt-0.5">{course.name}</p>
                          </td>
                          <td className="text-center px-3 text-surface-400 font-mono">{course.credits}</td>
                          <td className="text-center px-3 font-mono text-navy-800">
                            {course.score && typeof course.score === 'number' && course.score > 0
                              ? course.score.toFixed(1)
                              : <span className="text-surface-300">—</span>}
                          </td>
                          <td className="text-center px-3">
                            <span className={`inline-flex w-6 h-6 rounded-md text-[10px] font-bold items-center justify-center ${gradeColor(course.grade)}`}>
                              {course.grade}
                            </span>
                          </td>
                          <td className="text-center px-3 font-mono font-semibold text-navy-800">
                            {course.grade_point != null ? (typeof course.grade_point === 'number' ? course.grade_point.toFixed(1) : course.grade_point) : '0.0'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
