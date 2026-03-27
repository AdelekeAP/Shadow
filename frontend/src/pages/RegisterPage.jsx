import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

function RegisterPage() {
  const [form, setForm] = useState({
    fullName: '', email: '', password: '', confirmPassword: '',
    universityId: '', entryLevel: '400L', currentCgpa: '', targetCgpa: '4.50',
  })
  const [error, setError] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirm, setShowConfirm] = useState(false)
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()
  const { register } = useAuth()

  const set = (k, v) => { setForm(p => ({ ...p, [k]: v })); setError('') }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    if (form.password !== form.confirmPassword) { setError('Passwords do not match'); return }
    if (form.password.length < 8) { setError('Password must be at least 8 characters'); return }
    if (!/[A-Z]/.test(form.password)) { setError('Password must contain an uppercase letter'); return }
    if (!/[a-z]/.test(form.password)) { setError('Password must contain a lowercase letter'); return }
    if (!/[0-9]/.test(form.password)) { setError('Password must contain a number'); return }

    setLoading(true)
    try {
      await register({
        full_name: form.fullName, email: form.email, password: form.password,
        university_id: form.universityId || null, entry_level: form.entryLevel,
        current_cgpa: form.currentCgpa ? parseFloat(form.currentCgpa) : null,
        target_cgpa: parseFloat(form.targetCgpa),
      })
      navigate('/dashboard')
    } catch (err) {
      setError(err.detail || (typeof err === 'string' ? err : 'Registration failed. Please try again.'))
    } finally { setLoading(false) }
  }

  const inputCls = "w-full bg-surface-50 border border-surface-200/80 rounded-xl px-4 py-2.5 text-[13px] text-navy-900 placeholder:text-surface-300 focus:border-navy-300 focus:ring-2 focus:ring-navy-100 focus:bg-white transition-all outline-none"

  return (
    <div className="min-h-screen flex bg-surface-50">
      {/* Left panel — brand */}
      <div className="hidden lg:flex lg:w-[45%] relative overflow-hidden bg-gradient-to-br from-navy-900 via-navy-800 to-[#0c1425]">
        <div className="absolute inset-0 opacity-[0.03]" style={{
          backgroundImage: 'linear-gradient(rgba(255,255,255,0.15) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.15) 1px, transparent 1px)',
          backgroundSize: '48px 48px',
        }} />
        <div className="absolute top-1/3 left-1/2 -translate-x-1/2 w-96 h-96 rounded-full bg-emerald-500/[0.06] blur-[120px]" />

        <div className="relative z-10 flex flex-col justify-between p-12 w-full">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-white/10 flex items-center justify-center">
              <span className="text-white font-display text-[15px] font-bold">S</span>
            </div>
            <span className="text-[16px] font-bold text-white/90">Shadow</span>
          </div>

          <div>
            <h1 className="font-display text-[2.5rem] font-bold text-white leading-[1.15] tracking-tight mb-4">
              Set your target.<br />We'll track the rest.
            </h1>
            <p className="text-[15px] text-white/40 leading-relaxed max-w-sm">
              AI-powered grade predictions, smart task prioritization, and study recommendations built for PAU.
            </p>
          </div>

          <p className="text-[11px] text-white/20 font-medium">Pan-Atlantic University</p>
        </div>
      </div>

      {/* Right panel — form */}
      <div className="flex-1 flex items-center justify-center px-6 py-10">
        <div className="w-full max-w-sm">
          {/* Mobile logo */}
          <div className="flex items-center gap-2.5 mb-8 lg:hidden">
            <div className="w-8 h-8 rounded-lg bg-navy-800 flex items-center justify-center">
              <span className="text-white font-display text-[15px] font-bold">S</span>
            </div>
            <span className="text-[16px] font-bold text-navy-900">Shadow</span>
          </div>

          <h2 className="font-display text-[24px] font-bold text-navy-900 tracking-tight mb-1">Create account</h2>
          <p className="text-[13px] text-surface-400 mb-6">Start tracking your academic goals</p>

          {error && (
            <div className="px-4 py-2.5 rounded-xl bg-red-50 border border-red-100 flex items-center gap-2 mb-5">
              <svg className="w-4 h-4 text-red-400 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
              </svg>
              <span className="text-[12px] font-medium text-red-600">{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-3.5">
            <Field label="Full name">
              <input type="text" value={form.fullName} onChange={(e) => set('fullName', e.target.value)} required autoComplete="name" className={inputCls} placeholder="Full Name" />
            </Field>

            <Field label="Email">
              <input type="email" value={form.email} onChange={(e) => set('email', e.target.value)} required autoComplete="email" className={inputCls} placeholder="your.email@pau.edu.ng" />
            </Field>

            <div className="grid grid-cols-2 gap-3">
              <Field label="Student ID" hint="optional">
                <input type="text" value={form.universityId} onChange={(e) => set('universityId', e.target.value)} className={inputCls} placeholder="21120612479" />
              </Field>
              <Field label="Level">
                <select value={form.entryLevel} onChange={(e) => set('entryLevel', e.target.value)} className={inputCls}>
                  <option value="100L">100 Level</option>
                  <option value="200L">200 Level</option>
                  <option value="300L">300 Level</option>
                  <option value="400L">400 Level</option>
                </select>
              </Field>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <Field label="Current CGPA" hint="optional">
                <input type="number" step="0.01" min="0" max="5" value={form.currentCgpa} onChange={(e) => set('currentCgpa', e.target.value)} className={`${inputCls} font-mono`} placeholder="0.00" />
              </Field>
              <Field label="Target CGPA">
                <input type="number" step="0.01" min="0" max="5" value={form.targetCgpa} onChange={(e) => set('targetCgpa', e.target.value)} className={`${inputCls} font-mono`} placeholder="4.50" />
                <p className="text-[10px] text-surface-300 mt-0.5">First Class = 4.50+</p>
              </Field>
            </div>

            <Field label="Password">
              <div className="relative">
                <input type={showPassword ? 'text' : 'password'} value={form.password} onChange={(e) => set('password', e.target.value)} required autoComplete="new-password" className={`${inputCls} pr-10`} placeholder="Min 8 characters" />
                <button type="button" onClick={() => setShowPassword(!showPassword)} className="absolute right-3 top-1/2 -translate-y-1/2 text-surface-300 hover:text-navy-600 transition-colors">
                  {showPassword ? (
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8"><path strokeLinecap="round" strokeLinejoin="round" d="M3.98 8.223A10.477 10.477 0 001.934 12C3.226 16.338 7.244 19.5 12 19.5c.993 0 1.953-.138 2.863-.395M6.228 6.228A10.45 10.45 0 0112 4.5c4.756 0 8.773 3.162 10.065 7.498a10.523 10.523 0 01-4.293 5.774M6.228 6.228L3 3m3.228 3.228l3.65 3.65m7.894 7.894L21 21m-3.228-3.228l-3.65-3.65m0 0a3 3 0 10-4.243-4.243m4.242 4.242L9.88 9.88" /></svg>
                  ) : (
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8"><path strokeLinecap="round" strokeLinejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z" /><path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /></svg>
                  )}
                </button>
              </div>
            </Field>

            <Field label="Confirm password">
              <div className="relative">
                <input type={showConfirm ? 'text' : 'password'} value={form.confirmPassword} onChange={(e) => set('confirmPassword', e.target.value)} required autoComplete="new-password" className={`${inputCls} pr-10`} placeholder="Re-enter password" />
                <button type="button" onClick={() => setShowConfirm(!showConfirm)} className="absolute right-3 top-1/2 -translate-y-1/2 text-surface-300 hover:text-navy-600 transition-colors">
                  {showConfirm ? (
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8"><path strokeLinecap="round" strokeLinejoin="round" d="M3.98 8.223A10.477 10.477 0 001.934 12C3.226 16.338 7.244 19.5 12 19.5c.993 0 1.953-.138 2.863-.395M6.228 6.228A10.45 10.45 0 0112 4.5c4.756 0 8.773 3.162 10.065 7.498a10.523 10.523 0 01-4.293 5.774M6.228 6.228L3 3m3.228 3.228l3.65 3.65m7.894 7.894L21 21m-3.228-3.228l-3.65-3.65m0 0a3 3 0 10-4.243-4.243m4.242 4.242L9.88 9.88" /></svg>
                  ) : (
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8"><path strokeLinecap="round" strokeLinejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z" /><path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /></svg>
                  )}
                </button>
              </div>
            </Field>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-navy-800 hover:bg-navy-900 text-white py-3 rounded-xl text-[13px] font-semibold transition-all disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center gap-2 mt-1"
            >
              {loading ? (
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : 'Create Account'}
            </button>
          </form>

          <p className="mt-6 text-center text-[13px] text-surface-400">
            Already have an account?{' '}
            <Link to="/login" className="text-navy-700 hover:text-navy-900 font-semibold transition-colors">Sign in</Link>
          </p>
        </div>
      </div>
    </div>
  )
}

function Field({ label, hint, children }) {
  return (
    <div>
      <label className="flex items-baseline gap-1.5 mb-1.5">
        <span className="text-[12px] font-semibold text-navy-800 uppercase tracking-wider">{label}</span>
        {hint && <span className="text-[10px] text-surface-300 normal-case tracking-normal font-normal">{hint}</span>}
      </label>
      {children}
    </div>
  )
}

export default RegisterPage
