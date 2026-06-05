import { useState } from 'react'
import { Navigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { resendVerification } from '../services/api'

export default function ProtectedRoute({ children }) {
  const { isAuthenticated, loading, user } = useAuth()
  const [bannerDismissed, setBannerDismissed] = useState(false)
  const [resending, setResending] = useState(false)

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-stone-50">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-navy-800"></div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  const handleResend = async () => {
    setResending(true)
    try {
      await resendVerification()
    } catch {
      // silently ignore — best effort
    } finally {
      setResending(false)
    }
  }

  return (
    <>
      {user && user.email_verified === false && user.email_delivery_enabled && !bannerDismissed && (
        <div className="bg-amber-50 border-b border-amber-200 px-4 py-2.5 flex items-center justify-between text-sm">
          <span className="text-amber-800">
            Please verify your email address.{' '}
            <button
              onClick={handleResend}
              disabled={resending}
              className="underline font-medium hover:text-amber-900 disabled:opacity-50"
            >
              {resending ? 'Sending...' : 'Resend verification email'}
            </button>
          </span>
          <button
            onClick={() => setBannerDismissed(true)}
            className="text-amber-600 hover:text-amber-800 ml-4 text-lg leading-none"
            aria-label="Dismiss"
          >
            &times;
          </button>
        </div>
      )}
      {children}
    </>
  )
}
