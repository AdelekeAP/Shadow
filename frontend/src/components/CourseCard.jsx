import { useState } from 'react'

/**
 * CourseCard Component
 * Displays course information with enroll/unenroll functionality
 */
const CourseCard = ({ course, enrolled = false, onEnroll, onUnenroll, loading = false }) => {
  const [isLoading, setIsLoading] = useState(false)

  const handleAction = async () => {
    setIsLoading(true)
    try {
      if (enrolled) {
        await onUnenroll(course.id)
      } else {
        await onEnroll(course.id)
      }
    } finally {
      setIsLoading(false)
    }
  }

  const getStatusBadge = () => {
    const statusMap = {
      'C': { label: 'Compulsory', color: 'bg-red-100 text-red-800' },
      'E': { label: 'Elective', color: 'bg-blue-100 text-blue-800' },
      'R': { label: 'Required', color: 'bg-yellow-100 text-yellow-800' }
    }
    const status = statusMap[course.status] || statusMap['C']

    return (
      <span className={`px-2 py-1 text-xs font-semibold rounded-full ${status.color}`}>
        {status.label}
      </span>
    )
  }

  return (
    <div className="bg-white border border-stone-200 rounded-lg p-6 hover:shadow-md transition-shadow">
      {/* Header */}
      <div className="flex justify-between items-start mb-3">
        <div>
          <h3 className="text-lg font-bold text-stone-900">{course.code}</h3>
          <p className="text-sm text-stone-600 mt-1">{course.title}</p>
        </div>
        {getStatusBadge()}
      </div>

      {/* Details */}
      <div className="space-y-2 mb-4">
        <div className="flex items-center text-sm text-stone-600">
          <span className="font-medium mr-2">Credits:</span>
          <span className="bg-stone-100 px-2 py-0.5 rounded">{course.credits}</span>
        </div>

        {course.description && (
          <p className="text-sm text-stone-600 leading-relaxed">
            {course.description}
          </p>
        )}

        <div className="flex items-center text-xs text-stone-500">
          <span>Level {course.level} • {course.department}</span>
        </div>
      </div>

      {/* Action Button */}
      <button
        onClick={handleAction}
        disabled={isLoading || loading}
        className={`
          w-full py-2 px-4 rounded-lg font-medium transition-colors
          ${enrolled
            ? 'bg-red-50 text-red-600 hover:bg-red-100 border border-red-200'
            : 'bg-navy-800 text-white hover:bg-navy-900'
          }
          ${(isLoading || loading) ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
        `}
      >
        {isLoading || loading ? (
          <span className="flex items-center justify-center">
            <svg className="animate-spin h-5 w-5 mr-2" viewBox="0 0 24 24">
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
                fill="none"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
            {enrolled ? 'Unenrolling...' : 'Enrolling...'}
          </span>
        ) : (
          <span>
            {enrolled ? 'Unenroll' : '+ Enroll in Course'}
          </span>
        )}
      </button>
    </div>
  )
}

export default CourseCard
