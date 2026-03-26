import { Component } from 'react'

export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error }
  }

  componentDidCatch(error, errorInfo) {
    console.error('ErrorBoundary caught:', error, errorInfo?.componentStack)
    if (window.Sentry) {
      window.Sentry.captureException(error, { extra: { componentStack: errorInfo?.componentStack } })
    }
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: null })
  }

  render() {
    if (this.state.hasError) {
      const label = this.props.label || 'this page'
      const inline = this.props.inline

      if (inline) {
        return (
          <div className="flex flex-col items-center justify-center py-16 px-6 text-center">
            <div className="w-12 h-12 rounded-xl bg-red-50 border border-red-200/60 flex items-center justify-center mb-3">
              <svg className="w-5 h-5 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8">
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" />
              </svg>
            </div>
            <p className="text-[14px] font-semibold text-navy-900 mb-1">Something went wrong</p>
            <p className="text-[12px] text-surface-400 mb-4 max-w-xs">An error occurred in {label}.</p>
            <button
              onClick={this.handleRetry}
              className="px-4 py-2 bg-navy-800 hover:bg-navy-900 text-white text-[12px] font-semibold rounded-xl transition-all"
            >
              Try Again
            </button>
          </div>
        )
      }

      return (
        <div className="min-h-screen flex items-center justify-center bg-surface-50 p-4">
          <div className="max-w-md w-full bg-white rounded-2xl shadow-sm border border-surface-200/60 p-8 text-center">
            <div className="w-14 h-14 rounded-2xl bg-red-50 border border-red-100 flex items-center justify-center mx-auto mb-5">
              <svg className="w-6 h-6 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8">
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" />
              </svg>
            </div>
            <h2 className="font-display text-[20px] font-bold text-navy-900 tracking-tight mb-2">Something went wrong</h2>
            <p className="text-[13px] text-surface-400 mb-6 leading-relaxed">
              An unexpected error occurred in {label}. Please try again.
            </p>
            <div className="flex items-center justify-center gap-3">
              <button
                onClick={this.handleRetry}
                className="px-5 py-2.5 bg-navy-800 text-white rounded-xl text-[13px] font-semibold hover:bg-navy-900 transition-colors"
              >
                Try Again
              </button>
              <button
                onClick={() => window.location.reload()}
                className="px-5 py-2.5 text-surface-400 hover:text-navy-800 hover:bg-surface-100 rounded-xl text-[13px] font-semibold transition-all"
              >
                Refresh Page
              </button>
            </div>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}
