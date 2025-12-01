import { useState, useEffect } from 'react'

/**
 * EditCourseScoresModal - Modal for updating CA and participation scores
 * Allows students to update their course scores when they find out from lecturers
 */
export default function EditCourseScoresModal({ isOpen, onClose, enrollment, onUpdate }) {
  const [formData, setFormData] = useState({
    ca_score: '',
    participation_score: '',
    exam_score: ''
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (enrollment) {
      setFormData({
        ca_score: enrollment.ca_score || '',
        participation_score: enrollment.participation_score || '',
        exam_score: enrollment.exam_score || ''
      })
    }
  }, [enrollment])

  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: value
    }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    // Validate scores
    const caScore = parseFloat(formData.ca_score) || 0
    const participationScore = formData.participation_score ? parseFloat(formData.participation_score) : null
    const examScore = formData.exam_score ? parseFloat(formData.exam_score) : null

    if (caScore < 0 || caScore > 30) {
      setError('CA score must be between 0 and 30')
      setLoading(false)
      return
    }

    if (participationScore !== null && (participationScore < 0 || participationScore > 5)) {
      setError('Participation score must be between 0 and 5')
      setLoading(false)
      return
    }

    if (examScore !== null && (examScore < 0 || examScore > 65)) {
      setError('Exam score must be between 0 and 65')
      setLoading(false)
      return
    }

    try {
      const updateData = {}

      // Only include fields that have values
      if (caScore > 0) updateData.ca_score = caScore
      if (participationScore !== null) updateData.participation_score = participationScore
      if (examScore !== null) updateData.exam_score = examScore

      console.log('Updating enrollment:', enrollment.id, 'with data:', updateData)

      await onUpdate(enrollment.id, updateData)
      console.log('Update successful!')
      onClose()
    } catch (err) {
      console.error('Update error:', err)
      setError(err.message || err.detail || 'Failed to update scores')
    } finally {
      setLoading(false)
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6">
        <h2 className="text-2xl font-bold text-stone-900 mb-2">
          Update Course Scores
        </h2>
        <p className="text-sm text-stone-600 mb-2">
          {enrollment?.course?.code} - {enrollment?.course?.title}
        </p>

        {/* Participation Assumption Notice */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-4">
          <p className="text-xs text-blue-900">
            <strong>Note:</strong> For grade predictions, we assume an average participation score of <strong>3/5</strong> if you haven't entered it yet. Update your actual participation score below when your lecturer informs you.
          </p>
        </div>

        {error && (
          <div className="bg-red-50 text-red-600 p-3 rounded-lg mb-4 text-sm">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* CA Score */}
          <div>
            <label className="block text-sm font-medium text-stone-700 mb-1">
              CA Score (out of 30)
            </label>
            <input
              type="number"
              name="ca_score"
              step="0.01"
              min="0"
              max="30"
              value={formData.ca_score}
              onChange={handleChange}
              className="w-full px-4 py-2 border-2 border-stone-200 rounded-lg focus:ring-4 focus:ring-navy-100 focus:border-navy-500 transition-all"
              placeholder="0.00"
            />
            <p className="text-xs text-stone-500 mt-1">
              CA marks from assignments, tests, etc. (max 30)
            </p>
          </div>

          {/* Participation Score */}
          <div>
            <label className="block text-sm font-medium text-stone-700 mb-1">
              Participation Score (out of 5)
            </label>
            <input
              type="number"
              name="participation_score"
              step="0.01"
              min="0"
              max="5"
              value={formData.participation_score}
              onChange={handleChange}
              className="w-full px-4 py-2 border-2 border-stone-200 rounded-lg focus:ring-4 focus:ring-navy-100 focus:border-navy-500 transition-all"
              placeholder="0.00"
            />
            <p className="text-xs text-stone-500 mt-1">
              Lecturer-awarded participation marks (usually unknown until results)
            </p>
          </div>

          {/* Exam Score */}
          <div>
            <label className="block text-sm font-medium text-stone-700 mb-1">
              Exam Score (out of 65) - Optional
            </label>
            <input
              type="number"
              name="exam_score"
              step="0.01"
              min="0"
              max="65"
              value={formData.exam_score}
              onChange={handleChange}
              className="w-full px-4 py-2 border-2 border-stone-200 rounded-lg focus:ring-4 focus:ring-navy-100 focus:border-navy-500 transition-all"
              placeholder="Leave blank if not taken"
            />
            <p className="text-xs text-stone-500 mt-1">
              Only fill this if you've taken the exam
            </p>
          </div>

          {/* Buttons */}
          <div className="flex gap-3 mt-6">
            <button
              type="button"
              onClick={onClose}
              disabled={loading}
              className="flex-1 px-4 py-2 border-2 border-stone-200 text-stone-700 rounded-lg font-medium hover:bg-stone-50 transition-colors disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex-1 px-4 py-2 bg-navy-800 text-white rounded-lg font-medium hover:bg-navy-900 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Saving...' : 'Save Scores'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
