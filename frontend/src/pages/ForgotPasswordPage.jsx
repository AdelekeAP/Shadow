import { useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../services/api'

function ForgotPasswordPage() {
  const [email, setEmail] = useState('')
  const [submitted, setSubmitted] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await api.post('/api/v1/auth/forgot-password', { email })
      setSubmitted(true)
    } catch (err) {
      setError(err.response?.data?.detail || 'Something went wrong. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex bg-surface-50">
      {/* Left panel */}
      <div className="hidden lg:flex lg:w-[45%] relative overflow-hidden bg-gradient-to-br from-navy-900 via-navy-800 to-[#0c1425]">
        <div className="absolute inset-0 opacity-[0.03]" style={{
          backgroundImage: 'linear-gradient(rgba(255,255,255,0.15) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.15) 1px, transparent 1px)',
          backgroundSize: '48px 48px',
        }} />
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
              Reset your<br />password.
            </h1>
            <p className="text-[15px] text-white/40 leading-relaxed max-w-sm">
              Enter the email you registered with and we'll send you a link to set a new password.
            </p>
          </div>
          <p className="text-[11px] text-white/20 font-medium">Pan-Atlantic University</p>
        </div>
      </div>

      {/* Right panel */}
      <div className="flex-1 flex items-center justify-center px-6 py-12">
        <div className="w-full max-w-sm">
          <div className="flex items-center gap-2.5 mb-10 lg:hidden">
            <div className="w-8 h-8 rounded-lg bg-navy-800 flex items-center justify-center">
              <span className="text-white font-display text-[15px] font-bold">S</span>
            </div>
            <span className="text-[16px] font-bold text-navy-900">Shadow</span>
          </div>

          <h2 className="font-display text-[24px] font-bold text-navy-900 tracking-tight mb-1">Forgot password</h2>
          <p className="text-[13px] text-surface-400 mb-8">We'll email you a link to reset it</p>

          {submitted ? (
            <div className="px-4 py-4 rounded-xl bg-emerald-50 border border-emerald-100">
              <p className="text-[13px] font-medium text-emerald-700 mb-1">Check your inbox</p>
              <p className="text-[12px] text-emerald-600">
                If an account exists for <strong>{email}</strong>, we've sent a password reset link. It expires in 1 hour.
              </p>
              <Link to="/login" className="inline-block mt-4 text-[12px] font-semibold text-navy-700 hover:text-navy-900 transition-colors">
                Back to Sign In
              </Link>
            </div>
          ) : (
            <>
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
                    autoComplete="email"
                    className="w-full bg-surface-50 border border-surface-200/80 rounded-xl px-4 py-3 text-[13px] text-navy-900 placeholder:text-surface-300 focus:border-navy-300 focus:ring-2 focus:ring-navy-100 focus:bg-white transition-all outline-none"
                    placeholder="your.email@pau.edu.ng"
                  />
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full bg-navy-800 hover:bg-navy-900 text-white py-3 rounded-xl text-[13px] font-semibold transition-all disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center gap-2 mt-2"
                >
                  {loading ? (
                    <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  ) : 'Send Reset Link'}
                </button>
              </form>

              <p className="mt-8 text-center text-[13px] text-surface-400">
                Remember your password?{' '}
                <Link to="/login" className="text-navy-700 hover:text-navy-900 font-semibold transition-colors">Sign In</Link>
              </p>
            </>
          )}
        </div>
      </div>
    </div>
  )
}

export default ForgotPasswordPage
