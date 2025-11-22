import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { login } from '../services/api'

function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      // Call login API
      const response = await login({ email, password })

      console.log('✅ Login successful:', response)

      // Redirect to dashboard on success
      navigate('/dashboard')
    } catch (err) {
      console.error('❌ Login error:', err)

      // Handle error messages
      if (err.detail) {
        setError(err.detail)
      } else if (typeof err === 'string') {
        setError(err)
      } else {
        setError('Login failed. Please check your credentials.')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-stone-50 px-4">
      <div className="max-w-md w-full bg-white rounded-xl shadow-sm border border-stone-200 p-8">
        <h2 className="text-3xl font-bold text-center text-stone-900 mb-8">
          Login to Shadow
        </h2>

        {error && (
          <div className="bg-red-50 text-red-600 p-3 rounded-lg mb-4 text-sm">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-stone-700 mb-2">
              Email Address
            </label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="w-full px-4 py-3 border-2 border-stone-200 rounded-lg focus:ring-4 focus:ring-navy-100 focus:border-navy-500 transition-all duration-200"
              placeholder="your.email@pau.edu.ng"
            />
          </div>

          <div>
            <label htmlFor="password" className="block text-sm font-medium text-stone-700 mb-2">
              Password
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
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
            {loading ? 'Signing In...' : 'Sign In'}
          </button>
        </form>

        <p className="mt-6 text-center text-sm text-stone-600">
          Don't have an account?{' '}
          <Link to="/register" className="text-navy-800 hover:text-navy-900 font-semibold">
            Register here
          </Link>
        </p>

        <Link to="/" className="block mt-4 text-center text-sm text-stone-500 hover:text-stone-700">
          ← Back to home
        </Link>
      </div>
    </div>
  )
}

export default LoginPage
