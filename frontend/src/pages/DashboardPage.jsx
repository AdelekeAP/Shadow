import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { getCurrentUser, isAuthenticated, logout, getEnrolledCourses, getTasks, getTaskStats } from '../services/api'
import TaskList from '../components/TaskList'
import AddTaskModal from '../components/AddTaskModal'
import PriorityRecommendations from '../components/PriorityRecommendations'
import MoodLogger from '../components/MoodLogger'

function DashboardPage() {
  const navigate = useNavigate()
  const [user, setUser] = useState(null)
  const [enrolledCourses, setEnrolledCourses] = useState([])
  const [tasks, setTasks] = useState([])
  const [taskStats, setTaskStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [showAddTaskModal, setShowAddTaskModal] = useState(false)

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

  const handleLogout = () => {
    logout()
  }

  const getGradeColor = (gradePoint) => {
    if (!gradePoint) return 'text-gray-400'
    if (gradePoint >= 4.5) return 'text-green-600'
    if (gradePoint >= 3.5) return 'text-blue-600'
    if (gradePoint >= 2.5) return 'text-yellow-600'
    return 'text-red-600'
  }

  const totalCredits = enrolledCourses.reduce((sum, e) => sum + e.course.credits, 0)
  const completedCA = enrolledCourses.filter(e => e.ca_score > 0).length
  const averageCA = enrolledCourses.length > 0
    ? enrolledCourses.reduce((sum, e) => sum + e.ca_score, 0) / enrolledCourses.length
    : 0

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-2xl font-bold text-blue-600">Shadow</h1>
              <span className="ml-2 text-sm text-gray-500">Academic Achievement System</span>
            </div>
            <div className="flex items-center gap-4">
              <button
                onClick={() => navigate('/courses')}
                className="text-blue-600 hover:text-blue-700 font-medium"
              >
                Browse Courses
              </button>
              <button
                onClick={() => navigate('/cgpa')}
                className="text-purple-600 hover:text-purple-700 font-medium"
              >
                📊 CGPA Analytics
              </button>
              <div className="flex items-center gap-3">
                <span className="text-gray-700 font-medium">{user?.full_name || 'User'}</span>
                <button
                  onClick={handleLogout}
                  className="text-sm text-gray-600 hover:text-gray-800"
                >
                  Logout
                </button>
              </div>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h2 className="text-3xl font-bold text-gray-900">Dashboard</h2>
          <p className="text-gray-600 mt-2">Welcome back! Here's your academic overview.</p>
        </div>

        {/* CGPA Overview */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div>
              <p className="text-sm text-gray-600 mb-1">Current CGPA</p>
              <p className="text-4xl font-bold text-blue-600">
                {user?.current_cgpa?.toFixed(2) || '0.00'}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-600 mb-1">Target CGPA</p>
              <p className="text-4xl font-bold text-gray-900">
                {user?.target_cgpa?.toFixed(2) || 'N/A'}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-600 mb-1">Total Credits</p>
              <p className="text-4xl font-bold text-purple-600">{user?.total_credits_completed || 0}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600 mb-1">Status</p>
              <p className="text-2xl font-bold text-green-600">
                {(user?.current_cgpa || 0) >= (user?.target_cgpa || 4.5) ? 'On Track ✓' : 'Keep Going 💪'}
              </p>
            </div>
          </div>
          {user?.target_cgpa && (
            <div className="mt-6">
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-green-600 h-2 rounded-full"
                  style={{
                    width: `${Math.min(100, ((user?.current_cgpa || 0) / user.target_cgpa) * 100)}%`
                  }}
                ></div>
              </div>
              <p className="text-sm text-gray-600 mt-2">
                {user?.current_cgpa
                  ? `${Math.round(((user.current_cgpa / user.target_cgpa) * 100))}% toward target`
                  : 'Complete courses to see progress'}
              </p>
            </div>
          )}
        </div>

        {/* Semester Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="text-3xl font-bold text-gray-900">{enrolledCourses.length}</div>
            <div className="text-sm text-gray-600 mt-1">Enrolled Courses</div>
          </div>
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="text-3xl font-bold text-gray-900">{totalCredits}</div>
            <div className="text-sm text-gray-600 mt-1">Credit Hours</div>
          </div>
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="text-3xl font-bold text-gray-900">{averageCA.toFixed(1)}/35</div>
            <div className="text-sm text-gray-600 mt-1">Average CA Score</div>
          </div>
        </div>

        {/* Task Overview */}
        {taskStats && (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-8">
            <h3 className="text-xl font-bold text-gray-900 mb-4">Task Overview</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
              <div>
                <div className="text-2xl font-bold text-blue-600">{taskStats.total_tasks}</div>
                <div className="text-sm text-gray-600">Total Tasks</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-green-600">{taskStats.completed_tasks}</div>
                <div className="text-sm text-gray-600">Completed</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-yellow-600">{taskStats.pending_tasks}</div>
                <div className="text-sm text-gray-600">Pending</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-red-600">{taskStats.overdue_tasks}</div>
                <div className="text-sm text-gray-600">Overdue</div>
              </div>
            </div>
            <div className="mt-4 pt-4 border-t border-gray-200">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <span className="text-sm text-gray-600">Total CA Earned (All Courses):</span>
                  <div className="mt-1">
                    <span className="text-lg font-bold text-gray-900">
                      {taskStats.total_ca_earned.toFixed(1)}
                    </span>
                    <span className="text-sm text-gray-500"> / {taskStats.total_ca_available.toFixed(1)} marks</span>
                  </div>
                  <p className="text-xs text-gray-500 mt-1">
                    Combined CA from {enrolledCourses.length} course{enrolledCourses.length !== 1 ? 's' : ''}
                  </p>
                </div>
                <div>
                  <span className="text-sm text-gray-600">Task Completion:</span>
                  <div className="mt-1">
                    <span className="text-lg font-bold text-blue-600">
                      {taskStats.completion_rate.toFixed(0)}%
                    </span>
                    <span className="text-sm text-gray-500"> ({taskStats.completed_tasks}/{taskStats.total_tasks})</span>
                  </div>
                  <p className="text-xs text-gray-500 mt-1">
                    Tasks marked as done
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Priority Recommendations */}
        <div className="mb-8">
          <PriorityRecommendations />
        </div>

        {/* Tasks Section */}
        <div className="mb-8">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-xl font-bold text-gray-900">My Tasks</h3>
            <button
              onClick={() => setShowAddTaskModal(true)}
              disabled={enrolledCourses.length === 0}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
            >
              <svg className="w-5 h-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              Add Task
            </button>
          </div>

          {enrolledCourses.length === 0 ? (
            <div className="bg-white rounded-lg shadow-sm border-2 border-dashed border-gray-300 p-12 text-center">
              <p className="text-gray-600 mb-4">Enroll in courses first to start adding tasks</p>
              <button
                onClick={() => navigate('/courses')}
                className="bg-blue-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-blue-700 transition-colors"
              >
                Browse Courses
              </button>
            </div>
          ) : (
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <TaskList
                tasks={tasks}
                onUpdate={handleTaskCreated}
                showCompleted={true}
                enrolledCourses={enrolledCourses}
              />
            </div>
          )}
        </div>

        {/* Enrolled Courses */}
        <div className="mb-6">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-xl font-bold text-gray-900">My Courses</h3>
            {enrolledCourses.length > 0 && (
              <button
                onClick={() => navigate('/courses')}
                className="text-sm text-blue-600 hover:text-blue-700 font-medium"
              >
                Manage Courses →
              </button>
            )}
          </div>

          {loading ? (
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
              <p className="text-gray-600">Loading courses...</p>
            </div>
          ) : enrolledCourses.length === 0 ? (
            <div className="bg-white rounded-lg shadow-sm border-2 border-dashed border-gray-300 p-12 text-center">
              <p className="text-gray-600 mb-4">You haven't enrolled in any courses yet</p>
              <button
                onClick={() => navigate('/courses')}
                className="bg-blue-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-blue-700 transition-colors"
              >
                + Browse Available Courses
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {enrolledCourses.map(enrollment => (
                <div
                  key={enrollment.id}
                  className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow"
                >
                  <div className="flex justify-between items-start mb-3">
                    <div>
                      <h3 className="font-bold text-lg text-gray-900">{enrollment.course.code}</h3>
                      <p className="text-sm text-gray-600 mt-1">{enrollment.course.title}</p>
                    </div>
                    {enrollment.is_priority && (
                      <span className="bg-yellow-100 text-yellow-800 text-xs px-2 py-1 rounded-full">
                        Priority
                      </span>
                    )}
                  </div>

                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">CA Score:</span>
                      <span className="font-semibold text-gray-900">
                        {enrollment.ca_score.toFixed(1)}/35
                      </span>
                    </div>

                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">EXAM Score:</span>
                      <span className="font-semibold text-gray-900">
                        {(enrollment.exam_score || 0).toFixed(1)}/65
                      </span>
                    </div>

                    <div className="flex justify-between text-sm border-t border-gray-200 pt-2">
                      <span className="text-gray-700 font-medium">Total Score:</span>
                      <span className="font-bold text-blue-600">
                        {((enrollment.ca_score || 0) + (enrollment.exam_score || 0)).toFixed(1)}/100
                      </span>
                    </div>

                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Tasks Done:</span>
                      <span className="font-semibold text-gray-900">
                        {enrollment.completion_rate.toFixed(0)}%
                      </span>
                    </div>

                    {enrollment.predicted_grade_point && (
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-600">Predicted Grade:</span>
                        <span className={`font-bold ${getGradeColor(enrollment.predicted_grade_point)}`}>
                          {enrollment.predicted_letter_grade || 'TBD'} ({enrollment.predicted_grade_point.toFixed(2)})
                        </span>
                      </div>
                    )}
                  </div>

                  <div className="mt-4 pt-4 border-t border-gray-200">
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-blue-600 h-2 rounded-full"
                        style={{ width: `${enrollment.completion_rate}%` }}
                      ></div>
                    </div>
                  </div>
                </div>
              ))}

              {/* Add Course Card */}
              <div
                onClick={() => navigate('/courses')}
                className="bg-white rounded-lg shadow-sm border-2 border-dashed border-gray-300 p-6 hover:border-blue-400 hover:bg-blue-50 transition-colors cursor-pointer"
              >
                <div className="flex flex-col items-center justify-center h-full text-center py-8">
                  <div className="text-4xl text-gray-400 mb-2">+</div>
                  <p className="text-gray-600 font-medium">Add More Courses</p>
                  <p className="text-sm text-gray-500 mt-1">{18 - enrolledCourses.length} available</p>
                </div>
              </div>
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

      {/* Mood Logger - Floating Button */}
      <MoodLogger onMoodLogged={() => console.log('Mood logged!')} />
    </div>
  )
}

export default DashboardPage
