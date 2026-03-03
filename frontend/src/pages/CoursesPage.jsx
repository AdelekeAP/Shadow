import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { getCourses, enrollInCourse, getEnrolledCourses, unenrollFromCourse, getSemesters, getActiveSemester, createAcademicYear, activateSemester, assignCoursesToSemester } from '../services/api'
import { useAuth } from '../contexts/AuthContext'
import NotificationBell from '../components/NotificationBell'

/* ─── Courses Page ─── */
export default function CoursesPage() {
  const navigate = useNavigate()
  const { isAuthenticated, user, logout: doLogout } = useAuth()
  const [courses, setCourses] = useState([])
  const [enrolledCourses, setEnrolledCourses] = useState([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('all')
  const [search, setSearch] = useState('')
  const [toast, setToast] = useState(null)
  const [confirmUnenroll, setConfirmUnenroll] = useState(null)
  const [actionLoading, setActionLoading] = useState(null)

  // Semester state
  const [semesters, setSemesters] = useState([])
  const [activeSem, setActiveSem] = useState(null)
  const [semesterView, setSemesterView] = useState('all')
  const [showYearModal, setShowYearModal] = useState(false)

  useEffect(() => {
    if (!isAuthenticated) { navigate('/login'); return }
    loadData()
  }, [isAuthenticated, navigate])

  const loadData = async () => {
    setLoading(true)
    try {
      const [allCourses, enrolled, semData, activeData] = await Promise.all([
        getCourses(),
        getEnrolledCourses(false),
        getSemesters().catch(() => []),
        getActiveSemester().catch(() => ({ semester: null })),
      ])
      setCourses(allCourses)
      setEnrolledCourses(enrolled)
      setSemesters(semData)
      setActiveSem(activeData.semester)
    } catch {
      showToast('Failed to load courses', 'error')
    } finally { setLoading(false) }
  }

  const showToast = (message, type = 'success') => {
    setToast({ message, type })
    setTimeout(() => setToast(null), 3000)
  }

  const handleEnroll = async (courseId) => {
    setActionLoading(courseId)
    try {
      await enrollInCourse(courseId)
      const enrolled = await getEnrolledCourses(false)
      setEnrolledCourses(enrolled)
      showToast(activeSem ? `Enrolled in ${activeSem.name}` : 'Enrolled successfully')
    } catch (err) {
      showToast(err.detail || 'Failed to enroll', 'error')
    } finally { setActionLoading(null) }
  }

  const handleUnenroll = async (courseId) => {
    const enrollment = enrolledCourses.find(e => e.course.id === courseId)
    if (!enrollment) return
    setActionLoading(courseId)
    try {
      await unenrollFromCourse(enrollment.id)
      const enrolled = await getEnrolledCourses(false)
      setEnrolledCourses(enrolled)
      setConfirmUnenroll(null)
      showToast('Unenrolled successfully')
    } catch (err) {
      showToast(err.detail || 'Failed to unenroll', 'error')
    } finally { setActionLoading(null) }
  }

  const handleCreateYear = async (yearStr) => {
    try {
      await createAcademicYear(yearStr)
      const [semData, activeData] = await Promise.all([
        getSemesters(),
        getActiveSemester(),
      ])
      setSemesters(semData)
      setActiveSem(activeData.semester)
      setShowYearModal(false)
      showToast(`Academic year ${yearStr} created`)
    } catch (err) {
      throw err
    }
  }

  const handleActivateSemester = async (semId) => {
    try {
      await activateSemester(semId)
      const [semData, activeData] = await Promise.all([
        getSemesters(),
        getActiveSemester(),
      ])
      setSemesters(semData)
      setActiveSem(activeData.semester)
      showToast('Active semester updated')
    } catch {
      showToast('Failed to switch semester', 'error')
    }
  }

  const handleAssignAll = async (semId) => {
    const unassigned = enrolledCourses.filter(e => !e.semester_id)
    if (!unassigned.length) return
    try {
      await assignCoursesToSemester(semId, unassigned.map(e => e.id))
      const enrolled = await getEnrolledCourses(false)
      setEnrolledCourses(enrolled)
      showToast(`${unassigned.length} course${unassigned.length > 1 ? 's' : ''} assigned`)
    } catch {
      showToast('Failed to assign courses', 'error')
    }
  }

  const isEnrolled = (courseId) => enrolledCourses.some(e => e.course.id === courseId)

  // Semester-aware filtering
  const getEnrollment = (courseId) => enrolledCourses.find(e => e.course.id === courseId)

  const filteredCourses = courses.filter(c => {
    // Type filter
    if (filter === 'enrolled') {
      const enrollment = getEnrollment(c.id)
      if (!enrollment) return false
      // Then apply semester filter
      if (semesterView === 'all') return true
      if (semesterView === 'unassigned') return !enrollment.semester_id
      return enrollment.semester_id === semesterView
    }
    if (filter !== 'all' && c.status !== filter) return false
    if (search) {
      const q = search.toLowerCase()
      return c.code.toLowerCase().includes(q) || c.title.toLowerCase().includes(q)
    }
    return true
  })

  const compulsoryCount = courses.filter(c => c.status === 'C').length
  const electiveCount = courses.filter(c => c.status === 'E').length
  const enrolledCount = enrolledCourses.length
  const totalCredits = enrolledCourses.reduce((sum, e) => sum + (e.course?.credits || 0), 0)
  const unassignedCount = enrolledCourses.filter(e => !e.semester_id).length

  const filters = [
    { key: 'all',      label: 'All',        count: courses.length },
    { key: 'enrolled', label: 'Enrolled',   count: enrolledCount },
    { key: 'C',        label: 'Compulsory', count: compulsoryCount },
    { key: 'E',        label: 'Elective',   count: electiveCount },
  ]

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
                { label: 'Courses', path: '/courses', active: true },
                { label: 'CGPA', path: '/cgpa' },
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
              onClick={() => { doLogout() }}
              className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-[13px] font-medium text-surface-400 hover:text-navy-800 hover:bg-surface-100 transition-colors"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
                <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 9V5.25A2.25 2.25 0 0013.5 3h-6a2.25 2.25 0 00-2.25 2.25v13.5A2.25 2.25 0 007.5 21h6a2.25 2.25 0 002.25-2.25V15m3 0l3-3m0 0l-3-3m3 3H9" />
              </svg>
              <span className="hidden sm:inline">Sign out</span>
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
                <h1 className="font-display text-[28px] font-bold text-navy-900 tracking-tight">Course Catalog</h1>
                <span className="px-2 py-0.5 rounded-md bg-navy-800/[0.06] border border-navy-200/40 text-[10px] font-bold text-navy-600 uppercase tracking-wider">400L</span>
              </div>
              <p className="text-[13px] text-surface-400 mt-1">Browse and enroll in your Computer Science courses</p>
            </div>

            {/* Quick stats chips — glass pill style */}
            <div className="flex items-center gap-2.5 flex-wrap">
              <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/80 border border-surface-200/60">
                <svg className="w-3.5 h-3.5 text-navy-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M4.26 10.147a60.438 60.438 0 0 0-.491 6.347A48.62 48.62 0 0 1 12 20.904a48.62 48.62 0 0 1 8.232-4.41 60.46 60.46 0 0 0-.491-6.347m-15.482 0a50.636 50.636 0 0 0-2.658-.813A59.906 59.906 0 0 1 12 3.493a59.903 59.903 0 0 1 10.399 5.84c-.896.248-1.783.52-2.658.814m-15.482 0A50.717 50.717 0 0 1 12 13.489a50.702 50.702 0 0 1 7.74-3.342" />
                </svg>
                <span className="text-[12px] font-semibold text-navy-800">{enrolledCount}</span>
                <span className="text-[11px] text-surface-400">enrolled</span>
              </div>
              <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/80 border border-surface-200/60">
                <span className="text-[12px] font-semibold text-navy-800 font-mono">{totalCredits}</span>
                <span className="text-[11px] text-surface-400">credit units</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ══════════ SEMESTER BAR ══════════ */}
      <SemesterBar
        semesters={semesters}
        activeSem={activeSem}
        semesterView={semesterView}
        onViewChange={setSemesterView}
        onCreateYear={() => setShowYearModal(true)}
        onActivate={handleActivateSemester}
        onAssignAll={handleAssignAll}
        unassignedCount={unassignedCount}
        enrolledCourses={enrolledCourses}
      />

      {/* ══════════ TOOLBAR ══════════ */}
      <div className="border-b border-surface-200/60 bg-white/60 backdrop-blur-sm">
        <div className="mx-auto max-w-[1360px] px-5 py-3 flex flex-col sm:flex-row sm:items-center gap-3">
          {/* Segmented filter */}
          <div className="flex items-center gap-1 p-1 rounded-xl bg-surface-100/80 border border-surface-200/60">
            {filters.map(f => (
              <button
                key={f.key}
                onClick={() => setFilter(f.key)}
                className={`px-3 py-1.5 rounded-lg text-[12px] font-semibold transition-all ${
                  filter === f.key
                    ? 'bg-white text-navy-800 shadow-sm'
                    : 'text-surface-400 hover:text-navy-700'
                }`}
              >
                {f.label}
                <span className={`ml-1 text-[10px] ${filter === f.key ? 'text-navy-500' : 'text-surface-300'}`}>
                  {f.count}
                </span>
              </button>
            ))}
          </div>

          {/* Search */}
          <div className="relative flex-1 max-w-xs ml-auto">
            <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-surface-300" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
              <path strokeLinecap="round" strokeLinejoin="round" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z" />
            </svg>
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search courses..."
              className="w-full bg-surface-50 border border-surface-200/80 rounded-xl pl-9 pr-3 py-2 text-[12px] text-navy-900 placeholder:text-surface-300 focus:border-navy-300 focus:ring-2 focus:ring-navy-100 focus:bg-white transition-all outline-none"
            />
          </div>
        </div>
      </div>

      {/* ══════════ CONTENT ══════════ */}
      <div className="mx-auto max-w-[1360px] px-5 py-6">

        {/* Loading skeleton — shimmer style */}
        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="rounded-2xl border border-surface-200/60 bg-white p-5">
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <div className="h-5 w-20 skeleton-shimmer rounded-lg mb-2" />
                    <div className="h-3 w-40 skeleton-shimmer rounded-lg" />
                  </div>
                  <div className="h-5 w-16 skeleton-shimmer rounded-full" />
                </div>
                <div className="h-3 w-full skeleton-shimmer rounded-lg mb-2" />
                <div className="h-3 w-2/3 skeleton-shimmer rounded-lg mb-5" />
                <div className="h-9 w-full skeleton-shimmer rounded-xl" />
              </div>
            ))}
          </div>

        ) : filteredCourses.length === 0 ? (
          /* ── Empty state — elevated ── */
          <div className="flex flex-col items-center justify-center py-20 relative">
            <div className="absolute top-10 left-1/2 -translate-x-1/2 w-64 h-40 bg-navy-800/[0.03] rounded-full blur-3xl pointer-events-none" />
            <div className="relative w-16 h-16 rounded-2xl bg-surface-100 border border-surface-200/60 flex items-center justify-center mb-4">
              <svg className="w-7 h-7 text-surface-300" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.042A8.967 8.967 0 0 0 6 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 0 1 6 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 0 1 6-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0 0 18 18a8.967 8.967 0 0 0-6 2.292m0-14.25v14.25" />
              </svg>
            </div>
            <p className="text-[14px] font-semibold text-navy-900 mb-1 relative">No courses found</p>
            <p className="text-[12px] text-surface-400 relative">
              {search ? `No results for "${search}"` : 'No courses match this filter'}
            </p>
            {search && (
              <button onClick={() => setSearch('')} className="relative mt-4 px-4 py-2 rounded-xl bg-gradient-to-b from-navy-700 to-navy-900 text-white text-[12px] font-semibold shadow-sm btn-glow transition-all">
                Clear search
              </button>
            )}
          </div>

        ) : (
          /* ── Course grid ── */
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredCourses.map((course, i) => (
              <CourseCard
                key={course.id}
                course={course}
                enrolled={isEnrolled(course.id)}
                onEnroll={handleEnroll}
                onUnenroll={(id) => setConfirmUnenroll(id)}
                isLoading={actionLoading === course.id}
                delay={i}
              />
            ))}
          </div>
        )}
      </div>

      {/* ══════════ TOAST ══════════ */}
      {toast && (
        <div className={`fixed bottom-6 left-1/2 -translate-x-1/2 z-50 flex items-center gap-2.5 px-4 py-2.5 rounded-xl shadow-lg border animate-fade-in ${
          toast.type === 'error'
            ? 'bg-red-50 border-red-200/60 text-red-700'
            : 'bg-emerald-50 border-emerald-200/60 text-emerald-700'
        }`}>
          {toast.type === 'error' ? (
            <svg className="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9 3.75h.008v.008H12v-.008Z" />
            </svg>
          ) : (
            <svg className="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75 11.25 15 15 9.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
            </svg>
          )}
          <span className="text-[12px] font-semibold">{toast.message}</span>
        </div>
      )}

      {/* ══════════ UNENROLL CONFIRM ══════════ */}
      {confirmUnenroll && (
        <UnenrollConfirm
          course={courses.find(c => c.id === confirmUnenroll)}
          loading={actionLoading === confirmUnenroll}
          onConfirm={() => handleUnenroll(confirmUnenroll)}
          onCancel={() => setConfirmUnenroll(null)}
        />
      )}

      {/* ══════════ ACADEMIC YEAR MODAL ══════════ */}
      {showYearModal && (
        <AcademicYearModal
          onClose={() => setShowYearModal(false)}
          onSubmit={handleCreateYear}
        />
      )}
    </div>
  )
}


/* ═══════════════════════════════════════════
   Semester Bar
   ═══════════════════════════════════════════ */
function SemesterBar({ semesters, activeSem, semesterView, onViewChange, onCreateYear, onActivate, onAssignAll, unassignedCount, enrolledCourses }) {
  const [assignDropdown, setAssignDropdown] = useState(false)

  const fmtDate = (iso) => {
    if (!iso) return ''
    const d = new Date(iso)
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
  }

  const semCredits = (semId) => {
    return enrolledCourses
      .filter(e => semId === 'unassigned' ? !e.semester_id : e.semester_id === semId)
      .reduce((s, e) => s + (e.course?.credits || 0), 0)
  }

  const semCourseCount = (semId) => {
    return enrolledCourses.filter(e => semId === 'unassigned' ? !e.semester_id : e.semester_id === semId).length
  }

  // No semesters — empty state
  if (!semesters.length) {
    return (
      <div className="border-b border-navy-700/30 bg-gradient-to-r from-navy-800 to-navy-900">
        <div className="mx-auto max-w-[1360px] px-5 py-5 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-white/10 flex items-center justify-center">
              <svg className="w-5 h-5 text-white/60" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
                <path strokeLinecap="round" strokeLinejoin="round" d="M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 0 1 2.25-2.25h13.5A2.25 2.25 0 0 1 21 7.5v11.25m-18 0A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75m-18 0v-7.5A2.25 2.25 0 0 1 5.25 9h13.5A2.25 2.25 0 0 1 21 11.25v7.5" />
              </svg>
            </div>
            <div>
              <p className="text-[14px] font-semibold text-white">No academic year set up</p>
              <p className="text-[11px] text-white/40">Create your academic year to organize courses by semester</p>
            </div>
          </div>
          <button
            onClick={onCreateYear}
            className="flex items-center gap-2 px-4 py-2.5 bg-white/10 hover:bg-white/15 border border-white/15 text-white rounded-xl text-[12px] font-semibold transition-all"
          >
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
            </svg>
            Create Academic Year
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="border-b border-navy-700/30 bg-gradient-to-r from-navy-800 to-navy-900">
      <div className="mx-auto max-w-[1360px] px-5 py-3.5">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-3">

          {/* Left: Active semester info */}
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-white/10 flex items-center justify-center flex-shrink-0">
              <svg className="w-4.5 h-4.5 text-white/70" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
                <path strokeLinecap="round" strokeLinejoin="round" d="M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 0 1 2.25-2.25h13.5A2.25 2.25 0 0 1 21 7.5v11.25m-18 0A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75m-18 0v-7.5A2.25 2.25 0 0 1 5.25 9h13.5A2.25 2.25 0 0 1 21 11.25v7.5" />
              </svg>
            </div>
            {activeSem ? (
              <div>
                <p className="text-[13px] font-semibold text-white leading-tight">{activeSem.name}</p>
                <p className="text-[10px] text-white/35">{fmtDate(activeSem.start_date)} - {fmtDate(activeSem.end_date)}</p>
              </div>
            ) : (
              <p className="text-[12px] text-white/50">No active semester</p>
            )}
          </div>

          {/* Center: Semester pills */}
          <div className="flex items-center gap-1.5 flex-wrap">
            <button
              onClick={() => onViewChange('all')}
              className={`px-3 py-1.5 rounded-lg text-[11px] font-semibold transition-all ${
                semesterView === 'all'
                  ? 'bg-white/20 text-white'
                  : 'text-white/40 hover:text-white/70 hover:bg-white/10'
              }`}
            >
              All
            </button>
            {semesters.map(s => (
              <button
                key={s.id}
                onClick={() => onViewChange(s.id)}
                className={`group flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[11px] font-semibold transition-all ${
                  semesterView === s.id
                    ? 'bg-white/20 text-white'
                    : 'text-white/40 hover:text-white/70 hover:bg-white/10'
                }`}
              >
                {s.name.replace(` ${s.academic_year}`, '')}
                <span className="text-[9px] text-white/25 font-mono">{semCourseCount(s.id)}</span>
                {s.is_active && (
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                )}
                {!s.is_active && semesterView === s.id && (
                  <button
                    onClick={(e) => { e.stopPropagation(); onActivate(s.id) }}
                    className="ml-1 text-[9px] text-white/30 hover:text-emerald-400 transition-colors"
                    title="Set as active"
                  >
                    Activate
                  </button>
                )}
              </button>
            ))}
            {unassignedCount > 0 && (
              <button
                onClick={() => onViewChange('unassigned')}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[11px] font-semibold transition-all ${
                  semesterView === 'unassigned'
                    ? 'bg-amber-500/20 text-amber-300'
                    : 'text-amber-400/50 hover:text-amber-300 hover:bg-white/10'
                }`}
              >
                Unassigned
                <span className="text-[9px] font-mono">{unassignedCount}</span>
              </button>
            )}
          </div>

          {/* Right: New Academic Year */}
          <button
            onClick={onCreateYear}
            className="flex items-center gap-1.5 px-3 py-2 bg-white/[0.07] hover:bg-white/[0.12] border border-white/10 text-white/70 hover:text-white rounded-lg text-[11px] font-semibold transition-all flex-shrink-0"
          >
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
            </svg>
            New Year
          </button>
        </div>

        {/* Unassigned courses banner */}
        {semesterView === 'unassigned' && unassignedCount > 0 && semesters.length > 0 && (
          <div className="mt-3 flex items-center gap-3 px-3.5 py-2.5 rounded-xl bg-amber-500/10 border border-amber-400/20">
            <svg className="w-4 h-4 text-amber-400 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" />
            </svg>
            <p className="text-[11px] text-amber-200/80 flex-1">
              {unassignedCount} course{unassignedCount > 1 ? 's' : ''} not assigned to any semester.
              Assign them for accurate CGPA breakdown.
            </p>
            <div className="relative">
              <button
                onClick={() => setAssignDropdown(!assignDropdown)}
                className="px-3 py-1.5 bg-amber-500/20 hover:bg-amber-500/30 text-amber-200 rounded-lg text-[11px] font-semibold transition-all"
              >
                Assign All
              </button>
              {assignDropdown && (
                <div className="absolute right-0 top-full mt-1 w-56 bg-white rounded-xl shadow-xl border border-surface-200/60 py-1 z-10">
                  {semesters.map(s => (
                    <button
                      key={s.id}
                      onClick={() => { onAssignAll(s.id); setAssignDropdown(false) }}
                      className="w-full text-left px-3.5 py-2 text-[12px] text-navy-800 hover:bg-surface-50 transition-colors"
                    >
                      {s.name}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}


/* ═══════════════════════════════════════════
   Academic Year Modal
   ═══════════════════════════════════════════ */
function AcademicYearModal({ onClose, onSubmit }) {
  const [entering, setEntering] = useState(false)
  const [year, setYear] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const backdropRef = useRef(null)

  useEffect(() => {
    requestAnimationFrame(() => setEntering(true))
  }, [])

  const close = () => { setEntering(false); setTimeout(onClose, 200) }

  const validate = (v) => {
    if (!v) return 'Enter an academic year'
    if (!/^\d{4}\/\d{4}$/.test(v)) return 'Use format: YYYY/YYYY'
    const [a, b] = v.split('/').map(Number)
    if (b !== a + 1) return 'Second year must be first year + 1'
    return ''
  }

  const handleSubmit = async () => {
    const err = validate(year)
    if (err) { setError(err); return }
    setSubmitting(true)
    setError('')
    try {
      await onSubmit(year)
    } catch (e) {
      setError(e.detail || e.message || 'Failed to create academic year')
    } finally { setSubmitting(false) }
  }

  const firstYear = year.match(/^(\d{4})\//) ? parseInt(year.match(/^(\d{4})\//)[1]) : null
  const secondYear = firstYear ? firstYear + 1 : null

  return (
    <div
      ref={backdropRef}
      onClick={(e) => e.target === backdropRef.current && close()}
      className={`fixed inset-0 z-50 bg-navy-950/40 backdrop-blur-sm flex items-center justify-center p-4 transition-opacity duration-200 ${entering ? 'opacity-100' : 'opacity-0'}`}
    >
      <div className={`bg-white rounded-2xl shadow-2xl max-w-md w-full overflow-hidden transition-all duration-300 ${
        entering ? 'scale-100 translate-y-0 opacity-100' : 'scale-95 translate-y-4 opacity-0'
      }`}>
        <div className="p-6">
          {/* Icon */}
          <div className="w-12 h-12 rounded-xl bg-navy-800/[0.06] border border-navy-200/40 flex items-center justify-center mb-4 mx-auto">
            <svg className="w-5 h-5 text-navy-700" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
              <path strokeLinecap="round" strokeLinejoin="round" d="M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 0 1 2.25-2.25h13.5A2.25 2.25 0 0 1 21 7.5v11.25m-18 0A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75m-18 0v-7.5A2.25 2.25 0 0 1 5.25 9h13.5A2.25 2.25 0 0 1 21 11.25v7.5" />
            </svg>
          </div>

          <h3 className="font-display text-[18px] font-bold text-navy-900 text-center tracking-tight mb-1">
            New Academic Year
          </h3>
          <p className="text-[12px] text-surface-400 text-center leading-relaxed mb-5">
            This creates First Semester and Second Semester automatically.
          </p>

          {/* Input */}
          <label className="block text-[11px] font-semibold text-navy-800 uppercase tracking-wider mb-2">Academic Year</label>
          <input
            type="text"
            value={year}
            onChange={(e) => { setYear(e.target.value); setError('') }}
            onKeyDown={(e) => e.key === 'Enter' && handleSubmit()}
            placeholder="e.g. 2025/2026"
            className="w-full bg-surface-50 border border-surface-200/80 rounded-xl px-4 py-3 text-[14px] font-mono text-navy-900 placeholder:text-surface-300 focus:border-navy-300 focus:ring-2 focus:ring-navy-100 focus:bg-white transition-all outline-none"
            autoFocus
          />

          {error && (
            <p className="text-[11px] text-red-600 font-medium mt-2">{error}</p>
          )}

          {/* Preview — green dot on whichever semester is current */}
          {firstYear && secondYear && !validate(year) && (() => {
            const month = new Date().getMonth() + 1
            const day = new Date().getDate()
            // First Semester: Sept 1 - Feb 14, Second Semester: Mar 2 - Jul 31
            const firstIsActive = month >= 9 || month === 1 || (month === 2 && day <= 14)
            const secondIsActive = (month === 3 && day >= 2) || (month >= 4 && month <= 7)
            return (
              <div className="mt-4 space-y-2">
                <p className="text-[10px] font-semibold text-surface-400 uppercase tracking-wider">Will create:</p>
                <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-surface-50 border border-surface-200/60">
                  <span className={`w-1.5 h-1.5 rounded-full ${firstIsActive ? 'bg-emerald-400' : 'bg-surface-300'}`} />
                  <span className="text-[12px] font-semibold text-navy-800">First Semester {year}</span>
                  <span className="text-[10px] text-surface-300 ml-auto font-mono">Sep - Feb 14</span>
                </div>
                <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-surface-50 border border-surface-200/60">
                  <span className={`w-1.5 h-1.5 rounded-full ${secondIsActive ? 'bg-emerald-400' : 'bg-surface-300'}`} />
                  <span className="text-[12px] font-semibold text-navy-800">Second Semester {year}</span>
                  <span className="text-[10px] text-surface-300 ml-auto font-mono">Mar 2 - Jul</span>
                </div>
              </div>
            )
          })()}
        </div>

        <div className="flex gap-3 px-6 py-4 border-t border-surface-100">
          <button
            onClick={close}
            disabled={submitting}
            className="flex-1 px-4 py-2.5 border border-surface-200 text-navy-700 rounded-xl text-[12px] font-semibold hover:bg-surface-50 transition-all disabled:opacity-40"
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={submitting || !year}
            className="flex-1 px-4 py-2.5 bg-navy-800 hover:bg-navy-900 text-white rounded-xl text-[12px] font-semibold transition-all disabled:opacity-40 flex items-center justify-center gap-2"
          >
            {submitting ? (
              <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            ) : 'Create'}
          </button>
        </div>
      </div>
    </div>
  )
}


/* ═══════════════════════════════════════════
   Course Card
   ═══════════════════════════════════════════ */
function CourseCard({ course, enrolled, onEnroll, onUnenroll, isLoading, delay = 0 }) {
  const statusConfig = {
    C: { label: 'Compulsory', cls: 'bg-amber-500/10 text-amber-700 border-amber-200/60' },
    E: { label: 'Elective',   cls: 'bg-blue-500/10 text-blue-700 border-blue-200/60' },
    R: { label: 'Required',   cls: 'bg-red-500/10 text-red-700 border-red-200/60' },
  }
  const status = statusConfig[course.status] || statusConfig.C

  return (
    <div
      className="group relative rounded-2xl border border-surface-200/60 bg-white hover:border-surface-300/80 transition-all duration-300 card-lift"
      style={{ animationDelay: `${Math.min(delay, 8) * 40}ms` }}
    >
      {/* Enrolled indicator bar */}
      {enrolled && (
        <div className="absolute top-0 left-0 right-0 h-[3px] rounded-t-2xl bg-gradient-to-r from-emerald-400 to-emerald-500" />
      )}

      <div className="p-5">
        {/* Header row */}
        <div className="flex items-start justify-between mb-3">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <span className="font-mono text-[15px] font-bold text-navy-900 tracking-tight">{course.code}</span>
              {enrolled && (
                <div className="flex items-center gap-1 px-1.5 py-0.5 rounded-md bg-emerald-500/10">
                  <svg className="w-3 h-3 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5">
                    <path strokeLinecap="round" strokeLinejoin="round" d="m4.5 12.75 6 6 9-13.5" />
                  </svg>
                  <span className="text-[10px] font-semibold text-emerald-700">Enrolled</span>
                </div>
              )}
            </div>
            <p className="text-[13px] text-surface-500 leading-snug line-clamp-1">{course.title}</p>
          </div>

          {/* Status badge */}
          <span className={`flex-shrink-0 ml-3 px-2 py-0.5 rounded-full text-[10px] font-semibold border ${status.cls}`}>
            {status.label}
          </span>
        </div>

        {/* Description */}
        {course.description && (
          <p className="text-[12px] text-surface-400 leading-relaxed line-clamp-2 mb-3">{course.description}</p>
        )}

        {/* Meta row */}
        <div className="flex items-center gap-3 mb-4">
          <div className="flex items-center gap-1.5">
            <svg className="w-3.5 h-3.5 text-surface-300" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
            </svg>
            <span className="text-[11px] text-surface-400">{course.credits} credit{course.credits !== 1 ? 's' : ''}</span>
          </div>
          <span className="w-px h-3 bg-surface-200" />
          <span className="text-[11px] text-surface-400">Level {course.level}</span>
          {course.department && (
            <>
              <span className="w-px h-3 bg-surface-200" />
              <span className="text-[11px] text-surface-400">{course.department}</span>
            </>
          )}
        </div>

        {/* Action button */}
        {enrolled ? (
          <button
            onClick={() => onUnenroll(course.id)}
            disabled={isLoading}
            className="w-full py-2.5 rounded-xl border border-surface-200/80 text-[12px] font-semibold text-surface-400 hover:text-red-600 hover:border-red-200 hover:bg-red-50/50 transition-all disabled:opacity-40"
          >
            {isLoading ? (
              <span className="flex items-center justify-center gap-2">
                <div className="w-3.5 h-3.5 border-2 border-surface-300 border-t-surface-500 rounded-full animate-spin" />
                Unenrolling...
              </span>
            ) : 'Unenroll'}
          </button>
        ) : (
          <button
            onClick={() => onEnroll(course.id)}
            disabled={isLoading}
            className="w-full py-2.5 rounded-xl bg-navy-800 hover:bg-navy-900 text-white text-[12px] font-semibold transition-all disabled:opacity-40 flex items-center justify-center gap-1.5"
          >
            {isLoading ? (
              <>
                <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Enrolling...
              </>
            ) : (
              <>
                <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
                </svg>
                Enroll
              </>
            )}
          </button>
        )}
      </div>
    </div>
  )
}


/* ═══════════════════════════════════════════
   Unenroll Confirmation Modal
   ═══════════════════════════════════════════ */
function UnenrollConfirm({ course, loading, onConfirm, onCancel }) {
  const [entering, setEntering] = useState(false)
  const backdropRef = useRef(null)

  useEffect(() => {
    requestAnimationFrame(() => setEntering(true))
  }, [])

  const close = () => { setEntering(false); setTimeout(onCancel, 200) }

  if (!course) return null

  return (
    <div
      ref={backdropRef}
      onClick={(e) => e.target === backdropRef.current && close()}
      className={`fixed inset-0 z-50 bg-navy-950/40 backdrop-blur-sm flex items-center justify-center p-4 transition-opacity duration-200 ${entering ? 'opacity-100' : 'opacity-0'}`}
    >
      <div className={`bg-white rounded-2xl shadow-2xl max-w-sm w-full overflow-hidden transition-all duration-300 ${
        entering ? 'scale-100 translate-y-0 opacity-100' : 'scale-95 translate-y-4 opacity-0'
      }`}>
        <div className="p-6">
          {/* Warning icon */}
          <div className="w-12 h-12 rounded-xl bg-red-50 border border-red-100 flex items-center justify-center mb-4 mx-auto">
            <svg className="w-5 h-5 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" />
            </svg>
          </div>

          <h3 className="font-display text-[18px] font-bold text-navy-900 text-center tracking-tight mb-1">
            Unenroll from {course.code}?
          </h3>
          <p className="text-[12px] text-surface-400 text-center leading-relaxed mb-1">
            {course.title}
          </p>
          <p className="text-[11px] text-surface-300 text-center leading-relaxed">
            This will remove all tasks and scores associated with this course.
          </p>
        </div>

        <div className="flex gap-3 px-6 py-4 border-t border-surface-100">
          <button
            onClick={close}
            disabled={loading}
            className="flex-1 px-4 py-2.5 border border-surface-200 text-navy-700 rounded-xl text-[12px] font-semibold hover:bg-surface-50 transition-all disabled:opacity-40"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            disabled={loading}
            className="flex-1 px-4 py-2.5 bg-red-600 hover:bg-red-700 text-white rounded-xl text-[12px] font-semibold transition-all disabled:opacity-40 flex items-center justify-center gap-2"
          >
            {loading ? (
              <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            ) : 'Unenroll'}
          </button>
        </div>
      </div>
    </div>
  )
}
