import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()
  const { login } = useAuth()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await login({ email, password })
      navigate('/dashboard')
    } catch (err) {
      setError(err.detail || (typeof err === 'string' ? err : 'Login failed. Please check your credentials.'))
    } finally { setLoading(false) }
  }

  return (
    <div className="min-h-screen flex bg-surface-50">
      {/* Left panel — brand */}
      <div className="hidden lg:flex lg:w-[45%] relative overflow-hidden bg-gradient-to-br from-navy-900 via-navy-800 to-[#0c1425]">
        {/* Grid overlay */}
        <div className="absolute inset-0 opacity-[0.03]" style={{
          backgroundImage: 'linear-gradient(rgba(255,255,255,0.15) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.15) 1px, transparent 1px)',
          backgroundSize: '48px 48px',
        }} />
        {/* Glow orb */}
        <div className="absolute top-1/3 left-1/2 -translate-x-1/2 w-96 h-96 rounded-full bg-blue-500/[0.06] blur-[120px]" />

        <div className="relative z-10 flex flex-col justify-between p-12 w-full">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-white/10 flex items-center justify-center">
              <span className="text-white font-display text-[15px] font-bold">S</span>
            </div>
            <span className="text-[16px] font-bold text-white/90">Shadow</span>
          </div>

          <div>
            <h1 className="font-display text-[2.5rem] font-bold text-white leading-[1.15] tracking-tight mb-4">
              Your CGPA,<br />on track.
            </h1>
            <p className="text-[15px] text-white/40 leading-relaxed max-w-sm">
              AI-powered academic planning for Pan-Atlantic University students. Set your target, track every point.
            </p>
          </div>

          <p className="text-[11px] text-white/20 font-medium">Pan-Atlantic University</p>
        </div>
      </div>

      {/* Right panel — form */}
      <div className="flex-1 flex items-center justify-center px-6 py-12">
        <div className="w-full max-w-sm">
          {/* Mobile logo */}
          <div className="flex items-center gap-2.5 mb-10 lg:hidden">
            <div className="w-8 h-8 rounded-lg bg-navy-800 flex items-center justify-center">
              <span className="text-white font-display text-[15px] font-bold">S</span>
            </div>
            <span className="text-[16px] font-bold text-navy-900">Shadow</span>
          </div>

          <h2 className="font-display text-[24px] font-bold text-navy-900 tracking-tight mb-1">Welcome back</h2>
          <p className="text-[13px] text-surface-400 mb-8">Sign in to continue to your dashboard</p>

          {error && (
            <div className="px-4 py-2.5 rounded-xl bg-red-50 border border-red-100 flex items-center gap-2 mb-5">
              <svg className="w-4 h-4 text-red-400 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
              </svg>
              <span className="text-[12px] font-medium text-red-600">{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="text-[12px] font-semibold text-navy-800 uppercase tracking-wider mb-1.5 block">Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="w-full bg-surface-50 border border-surface-200/80 rounded-xl px-4 py-3 text-[13px] text-navy-900 placeholder:text-surface-300 focus:border-navy-300 focus:ring-2 focus:ring-navy-100 focus:bg-white transition-all outline-none"
                placeholder="your.email@pau.edu.ng"
              />
            </div>

            <div>
              <label className="text-[12px] font-semibold text-navy-800 uppercase tracking-wider mb-1.5 block">Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="w-full bg-surface-50 border border-surface-200/80 rounded-xl px-4 py-3 text-[13px] text-navy-900 placeholder:text-surface-300 focus:border-navy-300 focus:ring-2 focus:ring-navy-100 focus:bg-white transition-all outline-none"
                placeholder="Enter your password"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-navy-800 hover:bg-navy-900 text-white py-3 rounded-xl text-[13px] font-semibold transition-all disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center gap-2 mt-2"
            >
              {loading ? (
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : 'Sign In'}
            </button>
          </form>

          <p className="mt-8 text-center text-[13px] text-surface-400">
            Don't have an account?{' '}
            <Link to="/register" className="text-navy-700 hover:text-navy-900 font-semibold transition-colors">Register</Link>
          </p>
        </div>
      </div>
    </div>
  )
}

export default LoginPage
