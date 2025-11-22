import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { register } from '../services/api'

function RegisterPage() {
  const [formData, setFormData] = useState({
    fullName: '',
    email: '',
    password: '',
    confirmPassword: '',
    universityId: '',
    entryLevel: '400L',
    targetCgpa: '4.50'
  })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    })
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    // Validation
    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match')
      setLoading(false)
      return
    }

    if (formData.password.length < 8) {
      setError('Password must be at least 8 characters long')
      setLoading(false)
      return
    }

    try {
      // Prepare data for API (match backend schema)
      const registrationData = {
        full_name: formData.fullName,
        email: formData.email,
        password: formData.password,
        university_id: formData.universityId || null,
        entry_level: formData.entryLevel,
        target_cgpa: parseFloat(formData.targetCgpa)
      }

      // Call registration API
      const response = await register(registrationData)

      console.log('✅ Registration successful:', response)

      // Redirect to dashboard on success
      navigate('/dashboard')
    } catch (err) {
      console.error('❌ Registration error:', err)

      // Handle error messages
      if (err.detail) {
        setError(err.detail)
      } else if (typeof err === 'string') {
        setError(err)
      } else {
        setError('Registration failed. Please try again.')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-stone-50 px-4 py-8">
      <div className="max-w-md w-full bg-white rounded-xl shadow-sm border border-stone-200 p-8">
        <h2 className="text-3xl font-bold text-center text-stone-900 mb-2">
          Join Shadow
        </h2>
        <p className="text-center text-stone-600 mb-8 text-sm">
          Start achieving your academic goals
        </p>

        {error && (
          <div className="bg-red-50 text-red-600 p-3 rounded-lg mb-4 text-sm">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="fullName" className="block text-sm font-medium text-stone-700 mb-1">
              Full Name
            </label>
            <input
              id="fullName"
              name="fullName"
              type="text"
              value={formData.fullName}
              onChange={handleChange}
              required
              className="w-full px-4 py-3 border-2 border-stone-200 rounded-lg focus:ring-4 focus:ring-navy-100 focus:border-navy-500 transition-all duration-200"
              placeholder="Paul Adeleke Aladenusi"
            />
          </div>

          <div>
            <label htmlFor="email" className="block text-sm font-medium text-stone-700 mb-1">
              Email Address
            </label>
            <input
              id="email"
              name="email"
              type="email"
              value={formData.email}
              onChange={handleChange}
              required
              className="w-full px-4 py-3 border-2 border-stone-200 rounded-lg focus:ring-4 focus:ring-navy-100 focus:border-navy-500 transition-all duration-200"
              placeholder="your.email@pau.edu.ng"
            />
          </div>

          <div>
            <label htmlFor="universityId" className="block text-sm font-medium text-stone-700 mb-1">
              Student ID (Optional)
            </label>
            <input
              id="universityId"
              name="universityId"
              type="text"
              value={formData.universityId}
              onChange={handleChange}
              className="w-full px-4 py-3 border-2 border-stone-200 rounded-lg focus:ring-4 focus:ring-navy-100 focus:border-navy-500 transition-all duration-200"
              placeholder="21120612479"
            />
          </div>

          <div>
            <label htmlFor="entryLevel" className="block text-sm font-medium text-stone-700 mb-1">
              Current Level
            </label>
            <select
              id="entryLevel"
              name="entryLevel"
              value={formData.entryLevel}
              onChange={handleChange}
              className="w-full px-4 py-3 border-2 border-stone-200 rounded-lg focus:ring-4 focus:ring-navy-100 focus:border-navy-500 transition-all duration-200 bg-white"
            >
              <option value="100L">100 Level</option>
              <option value="200L">200 Level</option>
              <option value="300L">300 Level</option>
              <option value="400L">400 Level</option>
            </select>
          </div>

          <div>
            <label htmlFor="targetCgpa" className="block text-sm font-medium text-stone-700 mb-1">
              Target CGPA
            </label>
            <input
              id="targetCgpa"
              name="targetCgpa"
              type="number"
              step="0.01"
              min="0"
              max="5"
              value={formData.targetCgpa}
              onChange={handleChange}
              className="w-full px-4 py-3 border-2 border-stone-200 rounded-lg focus:ring-4 focus:ring-navy-100 focus:border-navy-500 transition-all duration-200"
              placeholder="4.50"
            />
            <p className="text-xs text-stone-500 mt-1">First Class = 4.50+</p>
          </div>

          <div>
            <label htmlFor="password" className="block text-sm font-medium text-stone-700 mb-1">
              Password
            </label>
            <input
              id="password"
              name="password"
              type="password"
              value={formData.password}
              onChange={handleChange}
              required
              className="w-full px-4 py-3 border-2 border-stone-200 rounded-lg focus:ring-4 focus:ring-navy-100 focus:border-navy-500 transition-all duration-200"
              placeholder="••••••••"
            />
          </div>

          <div>
            <label htmlFor="confirmPassword" className="block text-sm font-medium text-stone-700 mb-1">
              Confirm Password
            </label>
            <input
              id="confirmPassword"
              name="confirmPassword"
              type="password"
              value={formData.confirmPassword}
              onChange={handleChange}
              required
              className="w-full px-4 py-3 border-2 border-stone-200 rounded-lg focus:ring-4 focus:ring-navy-100 focus:border-navy-500 transition-all duration-200"
              placeholder="••••••••"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-navy-800 text-white py-3 rounded-lg font-semibold hover:bg-navy-900 transition-colors disabled:bg-stone-400 disabled:cursor-not-allowed"
          >
            {loading ? 'Creating Account...' : 'Create Account'}
          </button>
        </form>

        <p className="mt-6 text-center text-sm text-stone-600">
          Already have an account?{' '}
          <Link to="/login" className="text-navy-800 hover:text-navy-900 font-semibold">
            Login here
          </Link>
        </p>

        <Link to="/" className="block mt-4 text-center text-sm text-stone-500 hover:text-stone-700">
          ← Back to home
        </Link>
      </div>
    </div>
  )
}

export default RegisterPage
