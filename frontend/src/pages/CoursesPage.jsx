import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { getCourses, enrollInCourse, getEnrolledCourses, unenrollFromCourse, isAuthenticated } from '../services/api'
import CourseCard from '../components/CourseCard'

/**
 * Courses Page - Browse and enroll in CS400 courses
 */
const CoursesPage = () => {
  const navigate = useNavigate()
  const [courses, setCourses] = useState([])
  const [enrolledCourses, setEnrolledCourses] = useState([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('all') // 'all', 'C' (compulsory), 'E' (elective)
  const [error, setError] = useState(null)
  const [successMessage, setSuccessMessage] = useState(null)

  useEffect(() => {
    // Check authentication
    if (!isAuthenticated()) {
      navigate('/login')
      return
    }

    loadCourses()
    loadEnrolledCourses()
  }, [navigate])

  const loadCourses = async () => {
    try {
      setLoading(true)
      const data = await getCourses()
      setCourses(data)
    } catch (err) {
      console.error('Error loading courses:', err)
      setError('Failed to load courses')
    } finally {
      setLoading(false)
    }
  }

  const loadEnrolledCourses = async () => {
    try {
      const data = await getEnrolledCourses()
      setEnrolledCourses(data)
    } catch (err) {
      console.error('Error loading enrolled courses:', err)
    }
  }

  const handleEnroll = async (courseId) => {
    try {
      await enrollInCourse(courseId)
      setSuccessMessage('Successfully enrolled in course!')
      await loadEnrolledCourses() // Refresh enrolled courses

      // Clear success message after 3 seconds
      setTimeout(() => setSuccessMessage(null), 3000)
    } catch (err) {
      console.error('Error enrolling:', err)
      setError(err.detail || 'Failed to enroll in course')
      setTimeout(() => setError(null), 5000)
    }
  }

  const handleUnenroll = async (courseId) => {
    // Find the enrollment ID
    const enrollment = enrolledCourses.find(e => e.course.id === courseId)
    if (!enrollment) return

    if (!window.confirm('Are you sure you want to unenroll from this course?')) {
      return
    }

    try {
      await unenrollFromCourse(enrollment.id)
      setSuccessMessage('Successfully unenrolled from course')
      await loadEnrolledCourses() // Refresh enrolled courses
      setTimeout(() => setSuccessMessage(null), 3000)
    } catch (err) {
      console.error('Error unenrolling:', err)
      setError(err.detail || 'Failed to unenroll from course')
      setTimeout(() => setError(null), 5000)
    }
  }

  const isEnrolled = (courseId) => {
    return enrolledCourses.some(e => e.course.id === courseId)
  }

  const filteredCourses = courses.filter(course => {
    if (filter === 'all') return true
    return course.status === filter
  })

  const compulsoryCount = courses.filter(c => c.status === 'C').length
  const electiveCount = courses.filter(c => c.status === 'E').length
  const enrolledCount = enrolledCourses.length

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">CS400 Courses</h1>
              <p className="text-gray-600 mt-1">
                Browse and enroll in your 400-level Computer Science courses
              </p>
            </div>
            <button
              onClick={() => navigate('/dashboard')}
              className="bg-gray-100 hover:bg-gray-200 text-gray-700 px-4 py-2 rounded-lg font-medium transition-colors"
            >
              ← Back to Dashboard
            </button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Success/Error Messages */}
        {successMessage && (
          <div className="mb-6 bg-green-50 border border-green-200 text-green-800 px-4 py-3 rounded-lg">
            {successMessage}
          </div>
        )}

        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-lg">
            {error}
          </div>
        )}

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-white rounded-lg p-6 border border-gray-200">
            <div className="text-2xl font-bold text-gray-900">{enrolledCount}</div>
            <div className="text-sm text-gray-600">Enrolled Courses</div>
          </div>
          <div className="bg-white rounded-lg p-6 border border-gray-200">
            <div className="text-2xl font-bold text-gray-900">{compulsoryCount}</div>
            <div className="text-sm text-gray-600">Compulsory Courses</div>
          </div>
          <div className="bg-white rounded-lg p-6 border border-gray-200">
            <div className="text-2xl font-bold text-gray-900">{electiveCount}</div>
            <div className="text-sm text-gray-600">Elective Courses</div>
          </div>
          <div className="bg-white rounded-lg p-6 border border-gray-200">
            <div className="text-2xl font-bold text-gray-900">{courses.length}</div>
            <div className="text-sm text-gray-600">Total Available</div>
          </div>
        </div>

        {/* Filters */}
        <div className="flex gap-3 mb-6">
          <button
            onClick={() => setFilter('all')}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              filter === 'all'
                ? 'bg-blue-600 text-white'
                : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
            }`}
          >
            All Courses ({courses.length})
          </button>
          <button
            onClick={() => setFilter('C')}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              filter === 'C'
                ? 'bg-blue-600 text-white'
                : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
            }`}
          >
            Compulsory ({compulsoryCount})
          </button>
          <button
            onClick={() => setFilter('E')}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              filter === 'E'
                ? 'bg-blue-600 text-white'
                : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
            }`}
          >
            Elective ({electiveCount})
          </button>
        </div>

        {/* Course Grid */}
        {loading ? (
          <div className="flex justify-center items-center h-64">
            <div className="text-gray-600">Loading courses...</div>
          </div>
        ) : filteredCourses.length === 0 ? (
          <div className="text-center py-12 bg-white rounded-lg border border-gray-200">
            <p className="text-gray-600">No courses found</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredCourses.map(course => (
              <CourseCard
                key={course.id}
                course={course}
                enrolled={isEnrolled(course.id)}
                onEnroll={handleEnroll}
                onUnenroll={handleUnenroll}
                loading={loading}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default CoursesPage
