import { useState, useEffect } from 'react'
import { Link, useParams } from 'react-router-dom'
import api from '../services/api'

function EmailVerificationPage() {
  const { token } = useParams()
  const [status, setStatus] = useState('verifying') // verifying | success | error
  const [errorMsg, setErrorMsg] = useState('')

  useEffect(() => {
    if (!token) {
      setStatus('error')
      setErrorMsg('Missing verification token.')
      return
    }

    const verify = async () => {
      try {
        await api.get(`/api/v1/auth/verify-email/${token}`)
        setStatus('success')
      } catch (err) {
        setStatus('error')
        setErrorMsg(err.response?.data?.detail || 'Verification failed. The link may have expired.')
      }
    }
    verify()
  }, [token])

  return (
    <div className="min-h-screen flex items-center justify-center bg-surface-50 px-6">
      <div className="text-center max-w-sm">
        <div className="flex items-center justify-center gap-2.5 mb-8">
          <div className="w-8 h-8 rounded-lg bg-navy-800 flex items-center justify-center">
            <span className="text-white font-display text-[15px] font-bold">S</span>
          </div>
          <span className="text-[16px] font-bold text-navy-900">Shadow</span>
        </div>

        {status === 'verifying' && (
          <>
            <div className="w-8 h-8 border-2 border-navy-200 border-t-navy-600 rounded-full animate-spin mx-auto mb-4" />
            <h2 className="font-display text-[20px] font-bold text-navy-900 mb-1">Verifying your email...</h2>
            <p className="text-[13px] text-surface-400">This will only take a moment.</p>
          </>
        )}

        {status === 'success' && (
          <div className="px-6 py-5 rounded-xl bg-emerald-50 border border-emerald-100">
            <svg className="w-10 h-10 text-emerald-500 mx-auto mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <h2 className="font-display text-[20px] font-bold text-emerald-800 mb-1">Email verified</h2>
            <p className="text-[13px] text-emerald-600 mb-4">Your email has been verified successfully.</p>
            <Link to="/dashboard" className="inline-block text-[13px] font-semibold bg-navy-800 text-white px-5 py-2.5 rounded-xl hover:bg-navy-900 transition-colors">
              Go to Dashboard
            </Link>
          </div>
        )}

        {status === 'error' && (
          <div className="px-6 py-5 rounded-xl bg-red-50 border border-red-100">
            <svg className="w-10 h-10 text-red-400 mx-auto mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
            </svg>
            <h2 className="font-display text-[20px] font-bold text-red-700 mb-1">Verification failed</h2>
            <p className="text-[13px] text-red-600 mb-4">{errorMsg}</p>
            <Link to="/dashboard" className="inline-block text-[13px] font-semibold text-navy-700 hover:text-navy-900 transition-colors">
              Go to Dashboard
            </Link>
          </div>
        )}
      </div>
    </div>
  )
}

export default EmailVerificationPage
