import { useState, useEffect, useMemo, useRef } from 'react'
import { getEnrolledCourses, getCurrentUser } from '../services/api'

const GRADE_SCALE = [
  { grade: 'A', point: 5.0, label: 'A (5.0)' },
  { grade: 'B', point: 4.0, label: 'B (4.0)' },
  { grade: 'C', point: 3.0, label: 'C (3.0)' },
  { grade: 'D', point: 2.0, label: 'D (2.0)' },
  { grade: 'E', point: 1.0, label: 'E (1.0)' },
  { grade: 'F', point: 0.0, label: 'F (0.0)' },
]

const CLASSIFICATIONS = [
  { name: 'First Class',         min: 4.50, color: 'bg-emerald-500' },
  { name: 'Second Class Upper',  min: 3.50, color: 'bg-blue-500' },
  { name: 'Second Class Lower',  min: 2.50, color: 'bg-amber-500' },
  { name: 'Third Class',         min: 1.50, color: 'bg-orange-500' },
  { name: 'Pass',                min: 1.00, color: 'bg-red-400' },
  { name: 'Fail',                min: 0.00, color: 'bg-red-600' },
]

const gradeBtn = (g, active) => {
  const base = 'w-9 h-9 rounded-lg text-[11px] font-bold transition-all'
  if (!active) return `${base} bg-surface-50 border border-surface-200/80 text-surface-400 hover:border-surface-300`
  const map = { A: 'bg-emerald-500', B: 'bg-blue-500', C: 'bg-amber-500', D: 'bg-orange-500', E: 'bg-red-400', F: 'bg-red-600' }
  return `${base} ${map[g] || 'bg-surface-400'} text-white shadow-sm scale-105`
}

export default function WhatIfCalculator({ onClose }) {
  const [enrolledCourses, setEnrolledCourses] = useState([])
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('simulator')
  const [simulatedGrades, setSimulatedGrades] = useState({})
  const [targetCGPA, setTargetCGPA] = useState(4.5)
  const [selectedScenario, setSelectedScenario] = useState(null)
  const [entering, setEntering] = useState(false)
  const backdropRef = useRef(null)

  useEffect(() => {
    requestAnimationFrame(() => setEntering(true))
    loadData()
  }, [])

  const close = () => { setEntering(false); setTimeout(onClose, 200) }

  const loadData = async () => {
    setLoading(true)
    try {
      const [courses, userData] = await Promise.all([getEnrolledCourses(), getCurrentUser()])
      setEnrolledCourses(courses)
      setUser(userData)
      const init = {}
      courses.forEach(e => { init[e.id] = e.current_grade || 'B' })
      setSimulatedGrades(init)
      if (userData?.target_cgpa) setTargetCGPA(userData.target_cgpa)
    } catch { /* silently fail */ } finally { setLoading(false) }
  }

  /* ── Calculations ── */
  const semesterGPA = useMemo(() => {
    if (!enrolledCourses.length) return { gpa: 0, qp: 0, credits: 0 }
    let qp = 0, cr = 0
    enrolledCourses.forEach(e => {
      const credits = e.course?.credits || 3
      const point = GRADE_SCALE.find(g => g.grade === simulatedGrades[e.id])?.point || 0
      qp += point * credits
      cr += credits
    })
    return { gpa: cr > 0 ? qp / cr : 0, qp, credits: cr }
  }, [enrolledCourses, simulatedGrades])

  const cumulative = useMemo(() => {
    const hCr = user?.total_credits_completed || 0
    const hCGPA = user?.current_cgpa || 0
    const hQP = hCGPA * hCr
    const tQP = hQP + semesterGPA.qp
    const tCr = hCr + semesterGPA.credits
    return { cgpa: tCr > 0 ? tQP / tCr : 0, totalCredits: tCr, histCredits: hCr, histQP: hQP }
  }, [user, semesterGPA])

  const simCGPA = cumulative.cgpa
  const getClass = (gpa) => CLASSIFICATIONS.find(c => gpa >= c.min) || CLASSIFICATIONS[CLASSIFICATIONS.length - 1]
  const currentClass = getClass(simCGPA)
  const delta = simCGPA - (user?.current_cgpa || 0)

  /* ── Required grades for target ── */
  const required = useMemo(() => {
    if (!user || !enrolledCourses.length) return null
    const hCr = user.total_credits_completed || 0
    const hQP = (user.current_cgpa || 0) * hCr
    const curCr = enrolledCourses.reduce((s, e) => s + (e.course?.credits || 3), 0)
    const totalCr = hCr + curCr
    const reqQP = targetCGPA * totalCr
    const reqSemQP = reqQP - hQP
    const reqGPA = curCr > 0 ? reqSemQP / curCr : 0
    const ok = reqGPA <= 5.0 && reqGPA >= 0
    return {
      gpa: reqGPA, isAchievable: ok, totalCredits: totalCr, currentCredits: curCr,
      difficulty: reqGPA > 5 ? 'Impossible' : reqGPA >= 4.5 ? 'Very Challenging' : reqGPA >= 3.5 ? 'Challenging' : reqGPA >= 2.5 ? 'Moderate' : 'Comfortable',
    }
  }, [user, enrolledCourses, targetCGPA])

  /* ── Scenario apply ── */
  const applyScenario = (id) => {
    setSelectedScenario(id)
    const g = {}
    enrolledCourses.forEach(e => {
      if (id === 'all_a') g[e.id] = 'A'
      else if (id === 'all_b') g[e.id] = 'B'
      else if (id === 'mixed') g[e.id] = ['A', 'B', 'C'][Math.floor(Math.random() * 3)]
      else if (id === 'worst') g[e.id] = 'F'
      else g[e.id] = e.current_grade || 'B'
    })
    setSimulatedGrades(g)
  }

  const handleGradeChange = (id, grade) => {
    setSimulatedGrades(p => ({ ...p, [id]: grade }))
    setSelectedScenario(null)
  }

  const tabs = [
    { id: 'simulator', label: 'Simulator' },
    { id: 'target',    label: 'Target' },
    { id: 'scenarios', label: 'Scenarios' },
  ]

  return (
    <div
      ref={backdropRef}
      onClick={(e) => e.target === backdropRef.current && close()}
      className={`fixed inset-0 z-50 bg-navy-950/40 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto transition-opacity duration-200 ${entering ? 'opacity-100' : 'opacity-0'}`}
    >
      <div className={`bg-white rounded-2xl shadow-2xl max-w-3xl w-full max-h-[90vh] overflow-hidden flex flex-col transition-all duration-300 ${
        entering ? 'scale-100 translate-y-0 opacity-100' : 'scale-95 translate-y-4 opacity-0'
      }`}>

        {/* ── Header ── */}
        <div className="flex-shrink-0 px-6 pt-6 pb-0">
          <div className="flex items-start justify-between mb-4">
            <div>
              <h2 className="font-display text-[20px] font-bold text-navy-900 tracking-tight">What-If Calculator</h2>
              <p className="text-[12px] text-surface-400 mt-0.5">Simulate grades and plan your academic future</p>
            </div>
            <button onClick={close} className="p-1.5 rounded-lg text-surface-300 hover:text-surface-400 hover:bg-surface-100 transition-all -mt-1 -mr-1">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Tabs */}
          <div className="flex items-center gap-1 p-1 rounded-xl bg-surface-100/80 border border-surface-200/60 mb-4">
            {tabs.map(t => (
              <button
                key={t.id}
                onClick={() => setActiveTab(t.id)}
                className={`flex-1 px-3 py-1.5 rounded-lg text-[12px] font-semibold transition-all text-center ${
                  activeTab === t.id
                    ? 'bg-white text-navy-800 shadow-sm'
                    : 'text-surface-400 hover:text-navy-700'
                }`}
              >
                {t.label}
              </button>
            ))}
          </div>
        </div>

        {/* ── Loading ── */}
        {loading ? (
          <div className="flex-1 flex items-center justify-center py-16">
            <div className="w-8 h-8 border-2 border-surface-200 border-t-navy-800 rounded-full animate-spin" />
          </div>
        ) : (
          <div className="flex-1 overflow-y-auto px-6 pb-4">

            {/* ── GPA Summary strip ── */}
            <div className="grid grid-cols-3 gap-3 mb-5">
              {/* Semester GPA */}
              <div className="rounded-xl border border-surface-200/60 bg-surface-50/50 p-3.5">
                <p className="text-[10px] font-semibold uppercase tracking-wider text-surface-400 mb-1">Semester GPA</p>
                <p className="font-mono text-[22px] font-bold text-navy-900 leading-none">{semesterGPA.gpa.toFixed(2)}</p>
                <p className="text-[10px] text-surface-300 mt-1">{semesterGPA.credits} cr / {semesterGPA.qp.toFixed(1)} QP</p>
              </div>
              {/* CGPA */}
              <div className={`rounded-xl border p-3.5 ${
                delta > 0.005 ? 'border-emerald-200/60 bg-emerald-50/50' :
                delta < -0.005 ? 'border-red-200/60 bg-red-50/50' :
                'border-surface-200/60 bg-surface-50/50'
              }`}>
                <p className="text-[10px] font-semibold uppercase tracking-wider text-surface-400 mb-1">Sim. CGPA</p>
                <div className="flex items-baseline gap-1.5">
                  <span className="font-mono text-[22px] font-bold text-navy-900 leading-none">{simCGPA.toFixed(2)}</span>
                  {Math.abs(delta) > 0.005 && (
                    <span className={`text-[11px] font-semibold ${delta > 0 ? 'text-emerald-600' : 'text-red-600'}`}>
                      {delta > 0 ? '+' : ''}{delta.toFixed(2)}
                    </span>
                  )}
                </div>
                <p className={`text-[10px] font-semibold mt-1 ${
                  simCGPA >= 4.5 ? 'text-emerald-600' : simCGPA >= 3.5 ? 'text-blue-600' : simCGPA >= 2.5 ? 'text-amber-600' : 'text-red-600'
                }`}>{currentClass.name}</p>
              </div>
              {/* Target */}
              <div className="rounded-xl border border-surface-200/60 bg-surface-50/50 p-3.5">
                <p className="text-[10px] font-semibold uppercase tracking-wider text-surface-400 mb-1">Target</p>
                <p className="font-mono text-[22px] font-bold text-navy-900 leading-none">{(user?.target_cgpa || 0).toFixed(2)}</p>
                {simCGPA >= (user?.target_cgpa || 5) && (
                  <p className="text-[10px] font-semibold text-emerald-600 mt-1">Achieved</p>
                )}
              </div>
            </div>

            {/* ── Impact bar ── */}
            <div className="rounded-xl border border-surface-200/60 bg-surface-50/50 p-4 mb-5">
              <p className="text-[10px] font-semibold uppercase tracking-wider text-surface-400 mb-3">Semester Impact</p>
              <div className="flex items-center gap-3">
                <span className="font-mono text-[13px] font-bold text-surface-400 w-10 text-right">{(user?.current_cgpa || 0).toFixed(2)}</span>
                <div className="flex-1 h-2 bg-surface-200/60 rounded-full overflow-hidden relative">
                  <div
                    className={`h-full rounded-full transition-all duration-500 ${delta >= 0 ? 'bg-emerald-500' : 'bg-red-500'}`}
                    style={{ width: `${Math.min(100, Math.abs(delta) * 40 + 2)}%` }}
                  />
                </div>
                <span className={`font-mono text-[13px] font-bold w-10 ${
                  delta > 0.005 ? 'text-emerald-600' : delta < -0.005 ? 'text-red-600' : 'text-surface-400'
                }`}>{simCGPA.toFixed(2)}</span>
              </div>
            </div>

            {/* ════════ SIMULATOR TAB ════════ */}
            {activeTab === 'simulator' && (
              <div>
                <div className="flex items-center justify-between mb-3">
                  <p className="text-[13px] font-semibold text-navy-900">Adjust Grades</p>
                  <button
                    onClick={() => applyScenario('current')}
                    className="text-[11px] font-semibold text-navy-700 hover:text-navy-900 transition-colors"
                  >
                    Reset
                  </button>
                </div>

                {enrolledCourses.length === 0 ? (
                  <p className="text-[12px] text-surface-400 text-center py-8">No enrolled courses found.</p>
                ) : (
                  <div className="space-y-2">
                    {enrolledCourses.map(e => {
                      const credits = e.course?.credits || 3
                      const point = GRADE_SCALE.find(g => g.grade === simulatedGrades[e.id])?.point || 0
                      return (
                        <div key={e.id} className="flex items-center gap-3 rounded-xl border border-surface-200/60 bg-white p-3">
                          <div className="flex-1 min-w-0">
                            <p className="font-mono text-[12px] font-semibold text-navy-900 truncate">{e.course?.code}</p>
                            <p className="text-[11px] text-surface-400 truncate">{e.course?.title || e.course?.name}</p>
                          </div>
                          <div className="flex gap-1">
                            {GRADE_SCALE.map(g => (
                              <button
                                key={g.grade}
                                onClick={() => handleGradeChange(e.id, g.grade)}
                                className={gradeBtn(g.grade, simulatedGrades[e.id] === g.grade)}
                              >
                                {g.grade}
                              </button>
                            ))}
                          </div>
                          <div className="w-12 text-right">
                            <p className="font-mono text-[12px] font-bold text-navy-800">{(point * credits).toFixed(1)}</p>
                            <p className="text-[9px] text-surface-300">QP</p>
                          </div>
                        </div>
                      )
                    })}
                  </div>
                )}
              </div>
            )}

            {/* ════════ TARGET TAB ════════ */}
            {activeTab === 'target' && (
              <div className="space-y-5">
                {/* Slider */}
                <div className="rounded-xl border border-surface-200/60 bg-white p-5">
                  <p className="text-[13px] font-semibold text-navy-900 mb-4">Set Your Target CGPA</p>
                  <div className="flex items-center gap-4">
                    <input
                      type="range"
                      min="1.0" max="5.0" step="0.1"
                      value={targetCGPA}
                      onChange={(e) => setTargetCGPA(parseFloat(e.target.value))}
                      className="flex-1 h-2 rounded-full appearance-none bg-surface-200 cursor-pointer accent-navy-800"
                    />
                    <span className="font-mono text-[24px] font-bold text-navy-900 w-14 text-center">{targetCGPA.toFixed(1)}</span>
                  </div>
                  <div className="flex justify-between text-[10px] text-surface-300 mt-1 px-0.5">
                    <span>1.0</span><span>2.0</span><span>3.0</span><span>4.0</span><span>5.0</span>
                  </div>
                  <div className="flex justify-center mt-3">
                    <span className={`px-3 py-1 rounded-lg text-[11px] font-semibold text-white ${getClass(targetCGPA).color}`}>
                      {getClass(targetCGPA).name}
                    </span>
                  </div>
                </div>

                {/* Required performance */}
                {required && (
                  <div className={`rounded-xl border p-5 ${
                    required.isAchievable ? 'border-emerald-200/60 bg-emerald-50/30' : 'border-red-200/60 bg-red-50/30'
                  }`}>
                    <div className="flex items-start justify-between mb-3">
                      <div>
                        <p className="text-[13px] font-semibold text-navy-900">Required Performance</p>
                        <span className={`inline-block mt-1 px-2 py-0.5 rounded-md text-[10px] font-semibold ${
                          required.isAchievable ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-600'
                        }`}>{required.difficulty}</span>
                      </div>
                      <div className="text-right">
                        <p className="text-[10px] text-surface-400 mb-0.5">Required Semester GPA</p>
                        <p className={`font-mono text-[26px] font-bold leading-none ${
                          required.isAchievable ? 'text-emerald-600' : 'text-red-600'
                        }`}>{required.gpa.toFixed(2)}</p>
                      </div>
                    </div>

                    {!required.isAchievable ? (
                      <div className="rounded-lg bg-red-100/60 border border-red-200/60 p-3 mt-3">
                        <p className="text-[12px] font-medium text-red-700">
                          This target requires a GPA above 5.0, which is impossible.
                        </p>
                        <p className="text-[11px] text-red-600 mt-1">Consider a more realistic target.</p>
                      </div>
                    ) : (
                      <div className="mt-3">
                        <p className="text-[12px] text-surface-400 mb-2">
                          You need approximately <strong className="text-navy-800">{GRADE_SCALE.reduce((prev, curr) =>
                            Math.abs(curr.point - required.gpa) < Math.abs(prev.point - required.gpa) ? curr : prev
                          ).grade}</strong> grades across all courses.
                        </p>
                        <button
                          onClick={() => {
                            const best = GRADE_SCALE.reduce((prev, curr) =>
                              Math.abs(curr.point - required.gpa) < Math.abs(prev.point - required.gpa) ? curr : prev
                            )
                            const g = {}
                            enrolledCourses.forEach(e => { g[e.id] = best.grade })
                            setSimulatedGrades(g)
                            setActiveTab('simulator')
                          }}
                          className="text-[12px] font-semibold text-navy-700 hover:text-navy-900 transition-colors"
                        >
                          Apply to Simulator →
                        </button>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}

            {/* ════════ SCENARIOS TAB ════════ */}
            {activeTab === 'scenarios' && (
              <div>
                <p className="text-[12px] text-surface-400 mb-4">Quickly see how different outcomes affect your CGPA</p>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {[
                    { id: 'all_a',   name: 'Best Case',           desc: 'All A grades',          icon: ArrowUpIcon,  accent: 'emerald' },
                    { id: 'all_b',   name: 'Good Performance',    desc: 'All B grades',          icon: ThumbUpIcon,  accent: 'blue' },
                    { id: 'mixed',   name: 'Mixed Results',       desc: 'Random A, B, C mix',    icon: ShuffleIcon,  accent: 'amber' },
                    { id: 'current', name: 'Current Projection',  desc: 'Based on current data',  icon: ChartIcon,    accent: 'navy' },
                    { id: 'worst',   name: 'Worst Case',          desc: 'All F grades',          icon: ArrowDownIcon, accent: 'red' },
                  ].map(s => {
                    const active = selectedScenario === s.id
                    const accents = {
                      emerald: active ? 'bg-emerald-500/10 border-emerald-300/60 ring-2 ring-emerald-200/40' : '',
                      blue:    active ? 'bg-blue-500/10 border-blue-300/60 ring-2 ring-blue-200/40' : '',
                      amber:   active ? 'bg-amber-500/10 border-amber-300/60 ring-2 ring-amber-200/40' : '',
                      navy:    active ? 'bg-navy-800/[0.06] border-navy-300/60 ring-2 ring-navy-200/40' : '',
                      red:     active ? 'bg-red-500/10 border-red-300/60 ring-2 ring-red-200/40' : '',
                    }
                    return (
                      <button
                        key={s.id}
                        onClick={() => applyScenario(s.id)}
                        className={`p-4 rounded-xl border text-left transition-all ${
                          active
                            ? accents[s.accent]
                            : 'border-surface-200/60 bg-white hover:border-surface-300/80 hover:shadow-sm'
                        }`}
                      >
                        <div className="flex items-center gap-3">
                          <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${
                            active ? 'bg-white/60' : 'bg-surface-100'
                          }`}>
                            <s.icon className="w-4 h-4 text-navy-700" />
                          </div>
                          <div>
                            <p className="text-[12px] font-semibold text-navy-900">{s.name}</p>
                            <p className="text-[11px] text-surface-400">{s.desc}</p>
                          </div>
                        </div>
                      </button>
                    )
                  })}
                </div>

                {selectedScenario && (
                  <div className="mt-4 rounded-xl border border-surface-200/60 bg-surface-50/50 p-4 flex items-center justify-between">
                    <p className="text-[12px] text-surface-400">
                      Simulated CGPA: <span className="font-mono font-bold text-navy-900">{simCGPA.toFixed(2)}</span>
                      {' '}— <span className={`font-semibold ${
                        simCGPA >= 4.5 ? 'text-emerald-600' : simCGPA >= 3.5 ? 'text-blue-600' : simCGPA >= 2.5 ? 'text-amber-600' : 'text-red-600'
                      }`}>{currentClass.name}</span>
                    </p>
                    <button
                      onClick={() => setActiveTab('simulator')}
                      className="text-[11px] font-semibold text-navy-700 hover:text-navy-900 transition-colors"
                    >
                      Edit grades →
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* ── Footer ── */}
        <div className="flex-shrink-0 flex items-center justify-between px-6 py-4 border-t border-surface-100">
          <p className="text-[11px] text-surface-400">
            {enrolledCourses.reduce((s, e) => s + (e.course?.credits || 3), 0)} credits this semester
          </p>
          <div className="flex gap-3">
            <button onClick={() => applyScenario('current')} className="px-4 py-2 border border-surface-200 text-navy-700 rounded-xl text-[12px] font-semibold hover:bg-surface-50 transition-all">
              Reset
            </button>
            <button onClick={close} className="px-5 py-2 bg-navy-800 hover:bg-navy-900 text-white rounded-xl text-[12px] font-semibold transition-all">
              Done
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

/* ─── SVG Icon components ─── */
function ArrowUpIcon({ className }) {
  return <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2"><path strokeLinecap="round" strokeLinejoin="round" d="M2.25 18 9 11.25l4.306 4.306a11.95 11.95 0 0 1 5.814-5.518l2.74-1.22m0 0-5.94-2.281m5.94 2.28-2.28 5.941" /></svg>
}
function ThumbUpIcon({ className }) {
  return <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2"><path strokeLinecap="round" strokeLinejoin="round" d="M6.633 10.25c.806 0 1.533-.446 2.031-1.08a9.041 9.041 0 0 1 2.861-2.4c.723-.384 1.35-.956 1.653-1.715a4.498 4.498 0 0 0 .322-1.672V3a.75.75 0 0 1 .75-.75 2.25 2.25 0 0 1 2.25 2.25c0 1.152-.26 2.243-.723 3.218-.266.558.107 1.282.725 1.282m0 0h3.126c1.026 0 1.945.694 2.054 1.715.045.422.068.85.068 1.285a11.95 11.95 0 0 1-2.649 7.521c-.388.482-.987.729-1.605.729H13.48c-.483 0-.964-.078-1.423-.23l-3.114-1.04a4.501 4.501 0 0 0-1.423-.23H5.904m7.594 0H5.904m7.594 0a.75.75 0 0 1 .75.75v.008a.75.75 0 0 1-.75.75h-7.594" /></svg>
}
function ShuffleIcon({ className }) {
  return <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2"><path strokeLinecap="round" strokeLinejoin="round" d="M7.5 21 3 16.5m0 0L7.5 12M3 16.5h13.5m0-13.5L21 7.5m0 0L16.5 12M21 7.5H7.5" /></svg>
}
function ChartIcon({ className }) {
  return <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2"><path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 0 1 3 19.875v-6.75ZM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V8.625ZM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V4.125Z" /></svg>
}
function ArrowDownIcon({ className }) {
  return <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2"><path strokeLinecap="round" strokeLinejoin="round" d="M2.25 6 9 12.75l4.286-4.286a11.948 11.948 0 0 1 4.306 6.43l.776 2.898m0 0 3.182-5.511m-3.182 5.51-5.511-3.181" /></svg>
}
