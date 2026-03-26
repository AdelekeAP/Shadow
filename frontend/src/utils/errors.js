/**
 * Parse API errors into user-friendly messages.
 * Shared across SmartStudy components.
 */
export function friendlyError(err) {
  const detail = err?.detail || err?.response?.data?.detail || err?.message || ''
  if (typeof detail === 'string') {
    if (detail.includes('429') || /rate.?limit/i.test(detail))
      return 'Too many requests — please wait a moment and try again.'
    if (/quota|insufficient/i.test(detail))
      return 'AI quota reached. Try again later.'
    if (/timeout/i.test(detail))
      return 'Request timed out. Please try again.'
  }
  return typeof detail === 'string' && detail.length > 0
    ? detail
    : 'Something went wrong. Please try again.'
}
