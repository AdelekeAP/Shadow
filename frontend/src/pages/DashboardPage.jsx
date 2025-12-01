import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { getCurrentUser, isAuthenticated, logout, getEnrolledCourses, getTasks, getTaskStats, getSmartStudyDashboardTrigger, updateEnrollment } from '../services/api'
import TaskList from '../components/TaskList'
import AddTaskModal from '../components/AddTaskModal'
import PriorityRecommendationsCompact from '../components/PriorityRecommendationsCompact'
import MoodLogger from '../components/MoodLogger'
import CourseCarousel from '../components/CourseCarousel'
import SmartStudyChat from '../components/SmartStudyChat'
import SmartStudyTriggerBanner from '../components/SmartStudyTriggerBanner'
import EditCourseScoresModal from '../components/EditCourseScoresModal'

function DashboardPage() {
  const navigate = useNavigate()
  const [user, setUser] = useState(null)
  const [enrolledCourses, setEnrolledCourses] = useState([])
  const [tasks, setTasks] = useState([])
  const [taskStats, setTaskStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [showAddTaskModal, setShowAddTaskModal] = useState(false)
  const [menuOpen, setMenuOpen] = useState(false)
  const [showMoodLogger, setShowMoodLogger] = useState(false)
  const [todayMood, setTodayMood] = useState(null)
  const [showSmartStudy, setShowSmartStudy] = useState(false)
  const [editingCourse, setEditingCourse] = useState(null)
  const [showCourseMenu, setShowCourseMenu] = useState(null) // Store course for menu

  useEffect(() => {
    // Check authentication
    if (!isAuthenticated()) {
      navigate('/login')
      return
    }

    // Get user from localStorage
    const currentUser = getCurrentUser()
    setUser(currentUser)

    // Load enrolled courses and tasks
    loadEnrolledCourses()
    loadTasks()
    loadTaskStats()
  }, [navigate])

  const loadEnrolledCourses = async () => {
    try {
      setLoading(true)
      const data = await getEnrolledCourses()
      setEnrolledCourses(data)
    } catch (err) {
      console.error('Error loading enrolled courses:', err)
    } finally {
      setLoading(false)
    }
  }

  const loadTasks = async () => {
    try {
      const data = await getTasks()
      setTasks(data)
    } catch (err) {
      console.error('Error loading tasks:', err)
    }
  }

  const loadTaskStats = async () => {
    try {
      const data = await getTaskStats()
      setTaskStats(data)
    } catch (err) {
      console.error('Error loading task stats:', err)
    }
  }

  const handleTaskCreated = () => {
    loadTasks()
    loadTaskStats()
    loadEnrolledCourses() // Reload to update CA scores
  }

  const handlePriorityTaskClick = (taskId) => {
    // Scroll to task list section
    const taskSection = document.getElementById('task-section')
    if (taskSection) {
      taskSection.scrollIntoView({ behavior: 'smooth', block: 'start' })

      // Highlight the task briefly
      setTimeout(() => {
        const taskElement = document.querySelector(`[data-task-id="${taskId}"]`)
        if (taskElement) {
          taskElement.classList.add('ring-4', 'ring-navy-500', 'ring-opacity-50')
          setTimeout(() => {
            taskElement.classList.remove('ring-4', 'ring-navy-500', 'ring-opacity-50')
          }, 2000)
        }
      }, 500)
    }
  }

  const handleLogout = () => {
    logout()
  }

  const handleUpdateCourseScores = async (enrollmentId, updateData) => {
    try {
      await updateEnrollment(enrollmentId, updateData)
      // Reload enrollments to show updated data
      await loadEnrolledCourses()
      setEditingCourse(null)
    } catch (error) {
      console.error('Error updating course scores:', error)
      throw error
    }
  }

  const getGradeColor = (gradePoint) => {
    if (!gradePoint) return 'text-stone-400'
    if (gradePoint >= 4.5) return 'text-green-600'
    if (gradePoint >= 3.5) return 'text-navy-800'
    if (gradePoint >= 2.5) return 'text-amber-600'
    return 'text-red-600'
  }


  const totalCredits = enrolledCourses.reduce((sum, e) => sum + e.course.credits, 0)
  const completedCA = enrolledCourses.filter(e => e.ca_score > 0).length
  const averageCA = enrolledCourses.length > 0
    ? enrolledCourses.reduce((sum, e) => sum + e.ca_score, 0) / enrolledCourses.length
    : 0

  return (
    <div className="min-h-screen bg-stone-50">
      <nav className="bg-white shadow-sm border-b border-stone-200 sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-2xl font-bold text-navy-800">Shadow</h1>
              <span className="ml-2 text-sm text-stone-500 hidden sm:inline">Academic Achievement System</span>
            </div>

            {/* Desktop nav */}
            <div className="hidden md:flex items-center gap-4">
              <button
                onClick={() => navigate('/courses')}
                className="text-stone-600 hover:text-navy-800 font-medium transition-colors"
              >
                Courses
              </button>
              <button
                onClick={() => navigate('/cgpa')}
                className="text-stone-600 hover:text-navy-800 font-medium transition-colors"
              >
                CGPA
              </button>
              <button
                onClick={() => setShowSmartStudy(true)}
                className="bg-gradient-to-r from-navy-600 to-navy-700 text-white px-4 py-2 rounded-lg font-medium hover:from-navy-700 hover:to-navy-800 transition-all duration-200 flex items-center gap-2 shadow-md hover:shadow-lg"
              >
                <span>🤖</span>
                <span>SmartStudy AI</span>
              </button>
              <div className="h-6 w-px bg-stone-200" />
              <span className="text-stone-700 font-medium">{user?.full_name || 'User'}</span>
              <button
                onClick={handleLogout}
                className="text-sm text-stone-500 hover:text-red-600 transition-colors"
              >
                Logout
              </button>
            </div>

            {/* Mobile burger */}
            <button
              onClick={() => setMenuOpen(!menuOpen)}
              className="md:hidden p-2 text-stone-600 hover:text-navy-800"
            >
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                {menuOpen ? (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                ) : (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                )}
              </svg>
            </button>
          </div>
        </div>

        {/* Mobile menu */}
        {menuOpen && (
          <div className="md:hidden border-t border-stone-200 bg-white animate-fade-in">
            <div className="px-4 py-3 space-y-2">
              <button
                onClick={() => { navigate('/courses'); setMenuOpen(false); }}
                className="block w-full text-left px-3 py-2 rounded-lg text-stone-700 hover:bg-stone-100 font-medium"
              >
                Browse Courses
              </button>
              <button
                onClick={() => { navigate('/cgpa'); setMenuOpen(false); }}
                className="block w-full text-left px-3 py-2 rounded-lg text-stone-700 hover:bg-stone-100 font-medium"
              >
                CGPA Analytics
              </button>
              <button
                onClick={() => { setShowSmartStudy(true); setMenuOpen(false); }}
                className="block w-full text-left px-3 py-2 rounded-lg bg-gradient-to-r from-navy-600 to-navy-700 text-white hover:from-navy-700 hover:to-navy-800 font-medium flex items-center gap-2"
              >
                <span>🤖</span>
                <span>SmartStudy AI</span>
              </button>
              <div className="border-t border-stone-200 pt-2 mt-2">
                <div className="px-3 py-2 text-sm text-stone-500">{user?.full_name || 'User'}</div>
                <button
                  onClick={handleLogout}
                  className="block w-full text-left px-3 py-2 rounded-lg text-red-600 hover:bg-red-50 font-medium"
                >
                  Logout
                </button>
              </div>
            </div>
          </div>
        )}
      </nav>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h2 className="text-3xl font-bold text-stone-900">Dashboard</h2>
          <p className="text-stone-600 mt-2">Welcome back! Here's your academic overview.</p>
        </div>

        {/* SmartStudy AI Trigger Banner - New trigger system with 8 detection criteria */}
        <SmartStudyTriggerBanner onOpenSmartStudy={(suggestedPrompt) => {
          setShowSmartStudy(true);
          // TODO: Pass suggestedPrompt to SmartStudyChat to auto-fill
        }} />

        {/* CGPA Overview */}
        <div className="bg-gradient-to-br from-navy-800 to-navy-900 rounded-2xl shadow-lg p-6 mb-6 text-white">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            <div>
              <p className="text-sm text-white/70 mb-1">Current CGPA</p>
              <p className="text-4xl font-bold">
                {user?.current_cgpa?.toFixed(2) || '0.00'}
              </p>
            </div>
            <div>
              <p className="text-sm text-white/70 mb-1">Target CGPA</p>
              <p className="text-4xl font-bold text-amber-300">
                {user?.target_cgpa?.toFixed(2) || 'N/A'}
              </p>
            </div>
            <div>
              <p className="text-sm text-white/70 mb-1">Total Credits</p>
              <p className="text-4xl font-bold">{user?.total_credits_completed || 0}</p>
            </div>
            <div>
              <p className="text-sm text-white/70 mb-1">Status</p>
              <p className="text-2xl font-bold text-emerald-400">
                {(user?.current_cgpa || 0) >= (user?.target_cgpa || 4.5) ? 'On Track' : 'Keep Going'}
              </p>
            </div>
          </div>
          {user?.target_cgpa && (
            <div className="mt-6">
              <div className="w-full bg-white/20 rounded-full h-2.5">
                <div
                  className="bg-gradient-to-r from-emerald-400 to-emerald-300 h-2.5 rounded-full transition-all duration-500"
                  style={{
                    width: `${Math.min(100, ((user?.current_cgpa || 0) / user.target_cgpa) * 100)}%`
                  }}
                ></div>
              </div>
              <p className="text-sm text-white/70 mt-2">
                {user?.current_cgpa
                  ? `${Math.round(((user.current_cgpa / user.target_cgpa) * 100))}% toward target`
                  : 'Complete courses to see progress'}
              </p>
            </div>
          )}
        </div>

        {/* Auto-scrolling Course Carousel - Shows enrolled courses with grades */}
        {enrolledCourses.length > 0 && (
          <div className="mb-8">
            <CourseCarousel
              enrolledCourses={enrolledCourses}
              onCourseClick={(enrollment) => {
                // Show menu to choose action
                setShowCourseMenu(enrollment)
              }}
            />
          </div>
        )}

        {/* Semester Stats + Mood Widget */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <div className="bg-white rounded-xl shadow-sm border border-stone-200 p-5 flex items-center gap-4 hover:shadow-md transition-shadow">
            <div className="w-12 h-12 rounded-xl bg-navy-100 flex items-center justify-center">
              <svg className="w-6 h-6 text-navy-700" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
              </svg>
            </div>
            <div>
              <div className="text-2xl font-bold text-stone-900">{enrolledCourses.length}</div>
              <div className="text-sm text-stone-500">Enrolled Courses</div>
            </div>
          </div>
          <div className="bg-white rounded-xl shadow-sm border border-stone-200 p-5 flex items-center gap-4 hover:shadow-md transition-shadow">
            <div className="w-12 h-12 rounded-xl bg-emerald-100 flex items-center justify-center">
              <svg className="w-6 h-6 text-emerald-700" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" />
              </svg>
            </div>
            <div>
              <div className="text-2xl font-bold text-stone-900">{totalCredits}</div>
              <div className="text-sm text-stone-500">Credit Hours</div>
            </div>
          </div>
          <div className="bg-white rounded-xl shadow-sm border border-stone-200 p-5 flex items-center gap-4 hover:shadow-md transition-shadow">
            <div className="w-12 h-12 rounded-xl bg-amber-100 flex items-center justify-center">
              <svg className="w-6 h-6 text-amber-700" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
            <div>
              <div className="text-2xl font-bold text-stone-900">{averageCA.toFixed(1)}/35</div>
              <div className="text-sm text-stone-500">Average CA Score</div>
            </div>
          </div>

          {/* Mood Insights Widget */}
          <div
            onClick={() => setShowMoodLogger(true)}
            className={`bg-gradient-to-br from-teal-50 to-teal-100 border-2 rounded-xl p-5 cursor-pointer hover:shadow-lg transition-all relative overflow-hidden ${
              !todayMood ? 'border-teal-300 animate-pulse' : 'border-teal-200 hover:border-teal-300'
            }`}
          >
            {/* Sparkle effect for unlogged */}
            {!todayMood && (
              <div className="absolute top-2 right-2">
                <svg className="w-5 h-5 text-teal-500 animate-bounce" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                </svg>
              </div>
            )}

            <div className="flex items-center justify-between mb-3">
              <span className="text-sm font-bold text-teal-900">How's your day?</span>
              {todayMood && (
                <span className="text-xs font-semibold text-teal-700 bg-teal-200 px-2 py-0.5 rounded-full">
                  ✓ Logged
                </span>
              )}
            </div>

            {todayMood ? (
              <div className="text-center">
                <div className="text-4xl mb-2">
                  {todayMood.mood_type === 'focused' ? '🎯' :
                   todayMood.mood_type === 'motivated' ? '💪' :
                   todayMood.mood_type === 'calm' ? '😌' :
                   todayMood.mood_type === 'confident' ? '😎' :
                   todayMood.mood_type === 'tired' ? '😴' :
                   todayMood.mood_type === 'stressed' ? '😰' :
                   todayMood.mood_type === 'anxious' ? '😟' :
                   todayMood.mood_type === 'overwhelmed' ? '😵' : '😊'}
                </div>
                <p className="text-sm font-bold text-teal-900 capitalize mb-1">{todayMood.mood_type}</p>
                <div className="flex items-center justify-center gap-1 text-xs text-teal-700">
                  {[...Array(5)].map((_, i) => (
                    <span key={i}>
                      {i < todayMood.energy_level ? '⚡' : '○'}
                    </span>
                  ))}
                </div>
              </div>
            ) : (
              <div className="text-center">
                <div className="text-3xl mb-2">💭</div>
                <p className="text-xs font-semibold text-teal-900 mb-1">Track your wellness</p>
                <p className="text-xs text-teal-600">Click to log</p>
              </div>
            )}

            <button
              onClick={(e) => { e.stopPropagation(); setShowMoodLogger(true); }}
              className={`mt-3 w-full py-2 text-xs font-bold rounded-lg transition-all ${
                todayMood
                  ? 'bg-teal-200 hover:bg-teal-300 text-teal-900'
                  : 'bg-teal-600 hover:bg-teal-700 text-white shadow-md'
              }`}
            >
              {todayMood ? 'Update Mood' : '💭 Log Mood'}
            </button>
          </div>
        </div>

        {/* Task Overview */}
        {taskStats && (
          <div className="bg-white rounded-xl shadow-sm border border-stone-200 p-6 mb-8">
            <h3 className="text-xl font-bold text-stone-900 mb-4">Task Overview</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
              <div>
                <div className="text-2xl font-bold text-navy-800">{taskStats.total_tasks}</div>
                <div className="text-sm text-stone-600">Total Tasks</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-green-600">{taskStats.completed_tasks}</div>
                <div className="text-sm text-stone-600">Completed</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-amber-600">{taskStats.pending_tasks}</div>
                <div className="text-sm text-stone-600">Pending</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-red-600">{taskStats.overdue_tasks}</div>
                <div className="text-sm text-stone-600">Overdue</div>
              </div>
            </div>
            <div className="mt-4 pt-4 border-t border-stone-200">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <span className="text-sm text-stone-600">Total CA Earned (All Courses):</span>
                  <div className="mt-1">
                    <span className="text-lg font-bold text-stone-900">
                      {taskStats.total_ca_earned.toFixed(1)}
                    </span>
                    <span className="text-sm text-stone-500"> / {taskStats.total_ca_available.toFixed(1)} marks</span>
                  </div>
                  <p className="text-xs text-stone-500 mt-1">
                    Combined CA from {enrolledCourses.length} course{enrolledCourses.length !== 1 ? 's' : ''}
                  </p>
                </div>
                <div>
                  <span className="text-sm text-stone-600">Task Completion:</span>
                  <div className="mt-1">
                    <span className="text-lg font-bold text-navy-800">
                      {taskStats.completion_rate.toFixed(0)}%
                    </span>
                    <span className="text-sm text-stone-500"> ({taskStats.completed_tasks}/{taskStats.total_tasks})</span>
                  </div>
                  <p className="text-xs text-stone-500 mt-1">
                    Tasks marked as done
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Priority Recommendations */}
        <div className="mb-8">
          <PriorityRecommendationsCompact onTaskClick={handlePriorityTaskClick} />
        </div>

        {/* Tasks Section */}
        <div id="task-section" className="mb-8">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-xl font-bold text-stone-900">My Tasks</h3>
            <button
              onClick={() => setShowAddTaskModal(true)}
              disabled={enrolledCourses.length === 0}
              className="bg-navy-800 text-white px-4 py-2 rounded-lg font-medium hover:bg-navy-900 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
            >
              <svg className="w-5 h-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              Add Task
            </button>
          </div>

          {enrolledCourses.length === 0 ? (
            <div className="bg-white rounded-xl shadow-sm border-2 border-dashed border-stone-300 p-12 text-center">
              <p className="text-stone-600 mb-4">Enroll in courses first to start adding tasks</p>
              <button
                onClick={() => navigate('/courses')}
                className="bg-navy-800 text-white px-6 py-3 rounded-lg font-medium hover:bg-navy-900 transition-colors"
              >
                Browse Courses
              </button>
            </div>
          ) : (
            <div className="bg-white rounded-xl shadow-sm border border-stone-200 p-6">
              <TaskList
                tasks={tasks}
                onUpdate={handleTaskCreated}
                showCompleted={true}
                enrolledCourses={enrolledCourses}
              />
            </div>
          )}
        </div>

      </main>

      {/* Add Task Modal */}
      <AddTaskModal
        isOpen={showAddTaskModal}
        onClose={() => setShowAddTaskModal(false)}
        onTaskCreated={handleTaskCreated}
        enrolledCourses={enrolledCourses}
      />

      {/* Mood Logger - Modal */}
      {showMoodLogger && (
        <MoodLogger
          onMoodLogged={(mood) => {
            setTodayMood(mood);
            setShowMoodLogger(false);
          }}
          onClose={() => setShowMoodLogger(false)}
        />
      )}

      {/* SmartStudy Chat - Modal */}
      {showSmartStudy && (
        <SmartStudyChat onClose={() => setShowSmartStudy(false)} />
      )}

      {/* Course Action Menu - Choose between Add Task or Update Scores */}
      {showCourseMenu && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-sm w-full p-6">
            <h3 className="text-xl font-bold text-stone-900 mb-2">
              {showCourseMenu.course?.code}
            </h3>
            <p className="text-sm text-stone-600 mb-6">
              What would you like to do?
            </p>

            <div className="space-y-3">
              <button
                onClick={() => {
                  setShowCourseMenu(null)
                  setShowAddTaskModal(true)
                }}
                className="w-full bg-navy-800 text-white px-4 py-3 rounded-lg font-medium hover:bg-navy-900 transition-colors flex items-center justify-center gap-2"
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                Add Task for this Course
              </button>

              <button
                onClick={() => {
                  setEditingCourse(showCourseMenu)
                  setShowCourseMenu(null)
                }}
                className="w-full bg-white border-2 border-navy-800 text-navy-800 px-4 py-3 rounded-lg font-medium hover:bg-navy-50 transition-colors flex items-center justify-center gap-2"
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                </svg>
                Update CA/Participation Scores
              </button>

              <button
                onClick={() => setShowCourseMenu(null)}
                className="w-full text-stone-600 hover:text-stone-900 py-2 text-sm font-medium"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Edit Course Scores Modal */}
      <EditCourseScoresModal
        isOpen={!!editingCourse}
        onClose={() => setEditingCourse(null)}
        enrollment={editingCourse}
        onUpdate={handleUpdateCourseScores}
      />
    </div>
  )
}

export default DashboardPage
