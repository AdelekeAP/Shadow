import { useState, useEffect, useRef, memo } from 'react'
import {
  getNotifications,
  getNotificationCount,
  markNotificationRead,
  markAllNotificationsRead,
  dismissNotification
} from '../services/api'

/* ─── Notification type config ─── */
const typeConfig = {
  task_reminder: { icon: (
    <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h3.75M9 15h3.75M9 18h3.75m3 .75H18a2.25 2.25 0 002.25-2.25V6.108c0-1.135-.845-2.098-1.976-2.192a48.424 48.424 0 00-1.123-.08m-5.801 0c-.065.21-.1.433-.1.664 0 .414.336.75.75.75h4.5a.75.75 0 00.75-.75 2.25 2.25 0 00-.1-.664m-5.8 0A2.251 2.251 0 0113.5 2.25H15c1.012 0 1.867.668 2.15 1.586m-5.8 0c-.376.023-.75.05-1.124.08C9.095 4.01 8.25 4.973 8.25 6.108V8.25m0 0H4.875c-.621 0-1.125.504-1.125 1.125v11.25c0 .621.504 1.125 1.125 1.125h9.75c.621 0 1.125-.504 1.125-1.125V9.375c0-.621-.504-1.125-1.125-1.125H8.25z" />
    </svg>
  ), color: 'text-blue-500', bg: 'bg-blue-500/[0.08]' },
  task_overdue: { icon: (
    <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
    </svg>
  ), color: 'text-red-500', bg: 'bg-red-500/[0.08]' },
  study_plan: { icon: (
    <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 016-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0018 18a8.967 8.967 0 00-6 2.292m0-14.25v14.25" />
    </svg>
  ), color: 'text-violet-500', bg: 'bg-violet-500/[0.08]' },
  mood_check: { icon: (
    <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
      <path strokeLinecap="round" strokeLinejoin="round" d="M15.182 15.182a4.5 4.5 0 01-6.364 0M21 12a9 9 0 11-18 0 9 9 0 0118 0zM9.75 9.75c0 .414-.168.75-.375.75S9 10.164 9 9.75 9.168 9 9.375 9s.375.336.375.75zm-.375 0h.008v.015h-.008V9.75zm5.625 0c0 .414-.168.75-.375.75s-.375-.336-.375-.75.168-.75.375-.75.375.336.375.75zm-.375 0h.008v.015h-.008V9.75z" />
    </svg>
  ), color: 'text-emerald-500', bg: 'bg-emerald-500/[0.08]' },
  goal_progress: { icon: (
    <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
      <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
    </svg>
  ), color: 'text-amber-500', bg: 'bg-amber-500/[0.08]' },
  achievement: { icon: (
    <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
      <path strokeLinecap="round" strokeLinejoin="round" d="M11.48 3.499a.562.562 0 011.04 0l2.125 5.111a.563.563 0 00.475.345l5.518.442c.499.04.701.663.321.988l-4.204 3.602a.563.563 0 00-.182.557l1.285 5.385a.562.562 0 01-.84.61l-4.725-2.885a.563.563 0 00-.586 0L6.982 20.54a.562.562 0 01-.84-.61l1.285-5.386a.562.562 0 00-.182-.557l-4.204-3.602a.563.563 0 01.321-.988l5.518-.442a.563.563 0 00.475-.345L11.48 3.5z" />
    </svg>
  ), color: 'text-yellow-500', bg: 'bg-yellow-500/[0.08]' },
  smart_study: { icon: (
    <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
      <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z" />
    </svg>
  ), color: 'text-navy-500', bg: 'bg-navy-500/[0.08]' },
  system: { icon: (
    <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
      <path strokeLinecap="round" strokeLinejoin="round" d="M14.857 17.082a23.848 23.848 0 005.454-1.31A8.967 8.967 0 0118 9.75v-.7V9A6 6 0 006 9v.75a8.967 8.967 0 01-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 01-5.714 0m5.714 0a3 3 0 11-5.714 0" />
    </svg>
  ), color: 'text-surface-400', bg: 'bg-surface-100' },
}

const priorityDot = {
  urgent: 'bg-red-500',
  high: 'bg-amber-500',
  medium: '',
  low: '',
}

const NotificationBell = memo(function NotificationBell() {
  const [isOpen, setIsOpen] = useState(false)
  const [notifications, setNotifications] = useState([])
  const [unreadCount, setUnreadCount] = useState(0)
  const [totalCount, setTotalCount] = useState(0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const ref = useRef(null)

  // Smart polling: pause when tab is hidden, use longer interval when idle
  useEffect(() => {
    fetchCount()
    let iv = null
    let interval = 30000 // 30s default

    const startPolling = () => {
      if (iv) clearInterval(iv)
      iv = setInterval(fetchCount, interval)
    }

    const handleVisibility = () => {
      if (document.hidden) {
        // Pause polling when tab not visible
        if (iv) { clearInterval(iv); iv = null }
      } else {
        // Resume with fresh fetch
        fetchCount()
        interval = 30000
        startPolling()
      }
    }

    startPolling()
    document.addEventListener('visibilitychange', handleVisibility)
    return () => {
      if (iv) clearInterval(iv)
      document.removeEventListener('visibilitychange', handleVisibility)
    }
  }, [])

  useEffect(() => {
    const onClick = (e) => { if (ref.current && !ref.current.contains(e.target)) setIsOpen(false) }
    document.addEventListener('mousedown', onClick)
    return () => document.removeEventListener('mousedown', onClick)
  }, [])

  useEffect(() => { if (isOpen) fetchList() }, [isOpen])

  const fetchCount = async () => {
    try {
      const d = await getNotificationCount()
      setUnreadCount(d.unread_count); setTotalCount(d.total_count)
      setError(null)
    } catch (err) {
      console.error('Notification count fetch failed:', err)
    }
  }
  const fetchList = async () => {
    setLoading(true); setError(null)
    try {
      const d = await getNotifications({ limit: 20 })
      setNotifications(d.notifications); setUnreadCount(d.unread_count); setTotalCount(d.total_count)
    } catch (err) {
      console.error('Notification list fetch failed:', err)
      setError(true)
    } finally { setLoading(false) }
  }
  const markRead = async (id) => {
    // Optimistic update
    setNotifications(p => p.map(n => n.id === id ? { ...n, is_read: true } : n))
    setUnreadCount(p => Math.max(0, p - 1))
    try { await markNotificationRead(id) }
    catch (err) {
      console.error('Mark read failed:', err)
      // Revert on failure
      setNotifications(p => p.map(n => n.id === id ? { ...n, is_read: false } : n))
      setUnreadCount(p => p + 1)
    }
  }
  const markAllRead = async () => {
    const prev = notifications.map(n => ({ ...n }))
    const prevCount = unreadCount
    setNotifications(p => p.map(n => ({ ...n, is_read: true }))); setUnreadCount(0)
    try { await markAllNotificationsRead() }
    catch (err) {
      console.error('Mark all read failed:', err)
      setNotifications(prev); setUnreadCount(prevCount)
    }
  }
  const dismiss = async (id, e) => {
    e.stopPropagation()
    const prev = notifications
    setNotifications(p => p.filter(n => n.id !== id)); setTotalCount(p => p - 1)
    try { await dismissNotification(id) }
    catch (err) {
      console.error('Dismiss failed:', err)
      setNotifications(prev); setTotalCount(p => p + 1)
    }
  }
  const clickNotif = (n) => {
    if (!n.is_read) markRead(n.id)
    if (n.action_url) { window.location.href = n.action_url; setIsOpen(false) }
  }

  const timeAgo = (d) => {
    const ms = Date.now() - new Date(d)
    const m = Math.floor(ms / 60000), h = Math.floor(ms / 3600000), dy = Math.floor(ms / 864e5)
    if (m < 1) return 'now'
    if (m < 60) return `${m}m`
    if (h < 24) return `${h}h`
    if (dy < 7) return `${dy}d`
    return new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
  }

  const getType = (t) => typeConfig[t] || typeConfig.system

  return (
    <div className="relative" ref={ref}>
      {/* Bell button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`relative p-1.5 rounded-lg transition-colors ${
          isOpen ? 'bg-surface-100 text-navy-800' : 'text-surface-400 hover:text-navy-700 hover:bg-surface-100'
        }`}
        aria-label="Notifications"
      >
        <svg className="w-[18px] h-[18px]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8">
          <path strokeLinecap="round" strokeLinejoin="round" d="M14.857 17.082a23.848 23.848 0 005.454-1.31A8.967 8.967 0 0118 9.75v-.7V9A6 6 0 006 9v.75a8.967 8.967 0 01-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 01-5.714 0m5.714 0a3 3 0 11-5.714 0" />
        </svg>
        {unreadCount > 0 && (
          <span className="absolute -top-0.5 -right-0.5 flex items-center justify-center min-w-[16px] h-4 px-1 text-[10px] font-bold text-white bg-red-500 rounded-full shadow-sm shadow-red-200">
            {unreadCount > 99 ? '99+' : unreadCount}
          </span>
        )}
      </button>

      {/* Dropdown */}
      {isOpen && (
        <>
          <div className="fixed inset-0 z-40" onClick={() => setIsOpen(false)} />
          <div className="absolute right-0 mt-2 w-[340px] bg-white rounded-xl shadow-xl border border-surface-200/80 overflow-hidden z-50 animate-fade-in">
            {/* Header */}
            <div className="flex items-center justify-between px-4 py-3 border-b border-surface-100">
              <div className="flex items-center gap-2">
                <h3 className="text-[13px] font-bold text-navy-900">Notifications</h3>
                {unreadCount > 0 && (
                  <span className="flex items-center justify-center min-w-[18px] h-[18px] px-1 text-[10px] font-bold text-navy-700 bg-navy-100 rounded-full">
                    {unreadCount}
                  </span>
                )}
              </div>
              {unreadCount > 0 && (
                <button onClick={markAllRead} className="text-[11px] font-semibold text-navy-600 hover:text-navy-800 transition-colors">
                  Mark all read
                </button>
              )}
            </div>

            {/* List */}
            <div className="overflow-y-auto max-h-[380px] scrollbar-thin">
              {loading ? (
                <div className="py-10 flex justify-center">
                  <div className="w-5 h-5 border-2 border-surface-200 border-t-navy-600 rounded-full animate-spin" />
                </div>
              ) : error ? (
                <div className="p-4 text-center text-[12px] text-red-500">Failed to load</div>
              ) : notifications.length === 0 ? (
                <div className="py-10 text-center">
                  <div className="w-10 h-10 rounded-xl bg-surface-100 flex items-center justify-center mx-auto mb-2.5">
                    <svg className="w-5 h-5 text-surface-300" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M14.857 17.082a23.848 23.848 0 005.454-1.31A8.967 8.967 0 0118 9.75v-.7V9A6 6 0 006 9v.75a8.967 8.967 0 01-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 01-5.714 0m5.714 0a3 3 0 11-5.714 0" />
                    </svg>
                  </div>
                  <p className="text-[13px] font-semibold text-navy-900">No notifications</p>
                  <p className="text-[11px] text-surface-400 mt-0.5">We'll notify you about updates</p>
                </div>
              ) : (
                <div>
                  {notifications.map((n) => {
                    const t = getType(n.notification_type)
                    return (
                      <div
                        key={n.id}
                        onClick={() => clickNotif(n)}
                        className={`group px-4 py-3 cursor-pointer transition-colors hover:bg-surface-50 ${
                          !n.is_read ? 'bg-navy-800/[0.02]' : ''
                        }`}
                      >
                        <div className="flex gap-2.5">
                          {/* Type icon */}
                          <div className={`flex-shrink-0 w-7 h-7 rounded-lg ${t.bg} ${t.color} flex items-center justify-center mt-0.5`}>
                            {t.icon}
                          </div>

                          {/* Content */}
                          <div className="flex-1 min-w-0">
                            <div className="flex items-start justify-between gap-2">
                              <p className={`text-[12px] leading-snug ${!n.is_read ? 'font-semibold text-navy-900' : 'font-medium text-surface-400'}`}>
                                {n.title}
                              </p>
                              {/* Dismiss */}
                              <button
                                onClick={(e) => dismiss(n.id, e)}
                                className="p-0.5 rounded text-surface-200 hover:text-surface-400 opacity-0 group-hover:opacity-100 transition-all flex-shrink-0"
                              >
                                <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5">
                                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                                </svg>
                              </button>
                            </div>
                            {n.message && (
                              <p className="text-[11px] text-surface-400 mt-0.5 line-clamp-2 leading-relaxed">{n.message}</p>
                            )}
                            <div className="flex items-center gap-1.5 mt-1.5">
                              <span className="text-[10px] text-surface-300 font-medium">{timeAgo(n.created_at)}</span>
                              {priorityDot[n.priority] && (
                                <>
                                  <span className="text-surface-200">·</span>
                                  <span className={`w-1.5 h-1.5 rounded-full ${priorityDot[n.priority]}`} />
                                  <span className="text-[10px] text-surface-300 capitalize">{n.priority}</span>
                                </>
                              )}
                              {!n.is_read && (
                                <span className="ml-auto w-1.5 h-1.5 bg-navy-500 rounded-full" />
                              )}
                            </div>
                          </div>
                        </div>
                      </div>
                    )
                  })}
                </div>
              )}
            </div>

            {/* Footer */}
            {totalCount > 20 && (
              <div className="px-4 py-2.5 border-t border-surface-100 text-center">
                <a href="/notifications" className="text-[11px] font-semibold text-navy-600 hover:text-navy-800 transition-colors">
                  View all notifications
                </a>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  )
})

export default NotificationBell
