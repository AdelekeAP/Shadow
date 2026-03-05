/**
 * NotificationPreferences Component
 * Allows users to manage their notification settings
 */
import { useState, useEffect, useRef } from 'react'
import {
  getNotificationPreferences,
  updateNotificationPreferences
} from '../services/api'

/* ─── Notification type config with SVG icons ─── */
const notifTypes = [
  { key: 'task_reminders', label: 'Task Reminders', desc: 'Get reminded about upcoming task deadlines', icon: ClipboardIcon },
  { key: 'task_overdue', label: 'Overdue Task Alerts', desc: 'Be notified when tasks become overdue', icon: AlertIcon },
  { key: 'study_plan_updates', label: 'Study Plan Updates', desc: 'Notifications about your study plans', icon: BookIcon },
  { key: 'mood_check_reminders', label: 'Mood Check Reminders', desc: 'Daily reminders to log your mood', icon: SmileIcon },
  { key: 'goal_progress', label: 'Goal Progress', desc: 'Updates on your CGPA goal progress', icon: TargetIcon },
  { key: 'achievements', label: 'Achievements', desc: 'Celebrate when you unlock achievements', icon: TrophyIcon },
  { key: 'smart_study', label: 'SmartStudy Recommendations', desc: 'AI-powered study suggestions', icon: SparkleIcon },
  { key: 'system_announcements', label: 'System Announcements', desc: 'Important system updates and news', icon: BellIcon },
]

export default function NotificationPreferences({ onClose }) {
  const [preferences, setPreferences] = useState(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState(null)
  const [successMessage, setSuccessMessage] = useState(null)
  const [entering, setEntering] = useState(false)
  const backdropRef = useRef(null)

  useEffect(() => {
    requestAnimationFrame(() => setEntering(true))
    fetchPreferences()
  }, [])

  const close = () => { setEntering(false); setTimeout(onClose, 200) }

  const fetchPreferences = async () => {
    setLoading(true)
    try {
      const data = await getNotificationPreferences()
      setPreferences(data)
    } catch (e) {
      console.error('Load preferences error:', e)
      setError('Failed to load notification preferences')
    } finally { setLoading(false) }
  }

  const handleToggle = (field) => {
    setPreferences(prev => ({ ...prev, [field]: !prev[field] }))
    setSuccessMessage(null)
  }

  const handleInputChange = (field, value) => {
    setPreferences(prev => ({ ...prev, [field]: value }))
    setSuccessMessage(null)
  }

  const handleSave = async () => {
    setSaving(true)
    setError(null)
    setSuccessMessage(null)
    try {
      await updateNotificationPreferences({
        email_enabled: preferences.email_enabled,
        in_app_enabled: preferences.in_app_enabled,
        task_reminders: preferences.task_reminders,
        task_overdue: preferences.task_overdue,
        study_plan_updates: preferences.study_plan_updates,
        mood_check_reminders: preferences.mood_check_reminders,
        goal_progress: preferences.goal_progress,
        achievements: preferences.achievements,
        smart_study: preferences.smart_study,
        system_announcements: preferences.system_announcements,
        quiet_hours_enabled: preferences.quiet_hours_enabled,
        quiet_hours_start: preferences.quiet_hours_start,
        quiet_hours_end: preferences.quiet_hours_end,
        task_reminder_hours: preferences.task_reminder_hours,
        reduce_when_stressed: preferences.reduce_when_stressed,
        motivate_when_low_energy: preferences.motivate_when_low_energy,
        daily_digest: preferences.daily_digest,
        weekly_digest: preferences.weekly_digest
      })
      setSuccessMessage('Preferences saved successfully!')
    } catch (e) {
      console.error('Save preferences error:', e)
      setError('Failed to save preferences')
    } finally { setSaving(false) }
  }

  const inputCls = 'bg-surface-50 border border-surface-200/80 rounded-xl px-3.5 py-2.5 text-[13px] text-navy-900 focus:border-navy-300 focus:ring-2 focus:ring-navy-100 focus:bg-white transition-all outline-none'

  if (!onClose) {
    // Inline (non-modal) rendering
    return renderContent()
  }

  return (
    <div
      ref={backdropRef}
      onClick={(e) => e.target === backdropRef.current && close()}
      className={`fixed inset-0 z-50 bg-navy-950/40 backdrop-blur-sm flex items-center justify-center p-4 transition-opacity duration-200 ${entering ? 'opacity-100' : 'opacity-0'}`}
    >
      <div className={`bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-hidden flex flex-col transition-all duration-300 ${
        entering ? 'scale-100 translate-y-0 opacity-100' : 'scale-95 translate-y-4 opacity-0'
      }`}>
        {renderContent()}
      </div>
    </div>
  )

  function renderContent() {
    return (
      <>
        {/* Header */}
        <div className="flex-shrink-0 px-6 pt-6 pb-0 flex items-start justify-between">
          <div>
            <h2 className="font-display text-[20px] font-bold text-navy-900 tracking-tight">Notification Preferences</h2>
            <p className="text-[12px] text-surface-400 mt-0.5">Manage how and when Shadow notifies you</p>
          </div>
          {onClose && (
            <button onClick={close} className="p-1.5 rounded-lg text-surface-300 hover:text-surface-400 hover:bg-surface-100 transition-all -mt-1 -mr-1">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          )}
        </div>

        {/* Body */}
        {loading ? (
          <div className="flex-1 flex items-center justify-center py-16">
            <div className="w-8 h-8 border-2 border-surface-200 border-t-navy-800 rounded-full animate-spin" />
          </div>
        ) : !preferences ? (
          <div className="flex-1 flex flex-col items-center justify-center py-16">
            <div className="w-12 h-12 rounded-xl bg-red-50 border border-red-100 flex items-center justify-center mb-3">
              <svg className="w-5 h-5 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
              </svg>
            </div>
            <p className="text-[13px] font-medium text-red-600">{error || 'Failed to load preferences'}</p>
          </div>
        ) : (
          <div className="flex-1 overflow-y-auto px-6 py-5 space-y-6 scrollbar-thin">

            {/* Delivery Channels */}
            <Section title="Delivery Channels">
              <Toggle label="In-App Notifications" desc="Show notifications in the app" enabled={preferences.in_app_enabled} onChange={() => handleToggle('in_app_enabled')} />
              <Toggle label="Email Notifications" desc="Receive notifications via email" enabled={preferences.email_enabled} onChange={() => handleToggle('email_enabled')} />
            </Section>

            {/* Notification Types */}
            <Section title="Notification Types">
              {notifTypes.map(t => (
                <Toggle
                  key={t.key}
                  label={t.label}
                  desc={t.desc}
                  enabled={preferences[t.key]}
                  onChange={() => handleToggle(t.key)}
                  Icon={t.icon}
                />
              ))}
            </Section>

            {/* Timing Settings */}
            <Section title="Timing Settings">
              <div className="flex items-center justify-between py-1">
                <div>
                  <p className="text-[13px] font-semibold text-navy-900">Remind me before deadline</p>
                  <p className="text-[11px] text-surface-400 mt-0.5">How early to send task reminders</p>
                </div>
                <select
                  value={preferences.task_reminder_hours}
                  onChange={(e) => handleInputChange('task_reminder_hours', parseInt(e.target.value))}
                  className={inputCls}
                >
                  <option value={1}>1 hour</option>
                  <option value={3}>3 hours</option>
                  <option value={6}>6 hours</option>
                  <option value={12}>12 hours</option>
                  <option value={24}>1 day</option>
                  <option value={48}>2 days</option>
                  <option value={72}>3 days</option>
                  <option value={168}>1 week</option>
                </select>
              </div>

              {/* Quiet Hours */}
              <div className="rounded-xl bg-surface-50/50 border border-surface-200/60 p-4 mt-2">
                <Toggle
                  label="Quiet Hours"
                  desc="Don't send notifications during certain hours"
                  enabled={preferences.quiet_hours_enabled}
                  onChange={() => handleToggle('quiet_hours_enabled')}
                />
                {preferences.quiet_hours_enabled && (
                  <div className="mt-4 flex items-center gap-4 pl-1">
                    <div>
                      <label className="text-[10px] font-semibold text-surface-400 uppercase tracking-wider mb-1 block">From</label>
                      <input
                        type="time"
                        value={preferences.quiet_hours_start || '22:00'}
                        onChange={(e) => handleInputChange('quiet_hours_start', e.target.value)}
                        className={inputCls}
                      />
                    </div>
                    <div>
                      <label className="text-[10px] font-semibold text-surface-400 uppercase tracking-wider mb-1 block">To</label>
                      <input
                        type="time"
                        value={preferences.quiet_hours_end || '08:00'}
                        onChange={(e) => handleInputChange('quiet_hours_end', e.target.value)}
                        className={inputCls}
                      />
                    </div>
                  </div>
                )}
              </div>
            </Section>

            {/* Smart Behavior */}
            <Section title="Smart Notification Behavior">
              <p className="text-[11px] text-surface-400 -mt-1 mb-2">Shadow can adjust notifications based on your current mood</p>
              <Toggle label="Reduce when stressed" desc="Send fewer notifications when you're feeling stressed" enabled={preferences.reduce_when_stressed} onChange={() => handleToggle('reduce_when_stressed')} />
              <Toggle label="Motivate when low energy" desc="Add encouraging messages when your energy is low" enabled={preferences.motivate_when_low_energy} onChange={() => handleToggle('motivate_when_low_energy')} />
            </Section>

            {/* Email Digests */}
            <Section title="Email Digests">
              <Toggle label="Daily Digest" desc="Receive a daily summary of your notifications" enabled={preferences.daily_digest} onChange={() => handleToggle('daily_digest')} />
              <Toggle label="Weekly Digest" desc="Receive a weekly summary every Monday" enabled={preferences.weekly_digest} onChange={() => handleToggle('weekly_digest')} />
            </Section>
          </div>
        )}

        {/* Footer */}
        {preferences && (
          <div className="flex-shrink-0 flex items-center justify-between px-6 py-4 border-t border-surface-100">
            <div className="flex-1 min-w-0">
              {error && <p className="text-[12px] font-medium text-red-600 truncate">{error}</p>}
              {successMessage && (
                <div className="flex items-center gap-1.5">
                  <svg className="w-3.5 h-3.5 text-emerald-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                  </svg>
                  <p className="text-[12px] font-medium text-emerald-600">{successMessage}</p>
                </div>
              )}
              {!error && !successMessage && <p className="text-[11px] text-surface-300">Changes are saved when you click Save</p>}
            </div>
            <button
              onClick={handleSave}
              disabled={saving}
              className="ml-4 px-5 py-2.5 bg-navy-800 hover:bg-navy-900 text-white rounded-xl text-[13px] font-semibold transition-all disabled:opacity-40 flex items-center justify-center gap-2"
            >
              {saving ? (
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : 'Save Changes'}
            </button>
          </div>
        )}
      </>
    )
  }
}


/* ─── Section wrapper ─── */
function Section({ title, children }) {
  return (
    <div>
      <h3 className="text-[12px] font-semibold text-navy-800 uppercase tracking-wider mb-3">{title}</h3>
      <div className="space-y-1">{children}</div>
    </div>
  )
}

/* ─── Toggle switch row ─── */
function Toggle({ label, desc, enabled, onChange, Icon }) {
  return (
    <div className="flex items-center justify-between py-2.5 px-2 rounded-lg hover:bg-surface-50 transition-colors -mx-2">
      <div className="flex items-center gap-3 flex-1 min-w-0">
        {Icon && (
          <div className="w-7 h-7 rounded-lg bg-navy-800/[0.05] flex items-center justify-center flex-shrink-0">
            <Icon className="w-3.5 h-3.5 text-navy-600" />
          </div>
        )}
        <div className="min-w-0">
          <p className="text-[13px] font-semibold text-navy-900">{label}</p>
          <p className="text-[11px] text-surface-400 mt-0.5">{desc}</p>
        </div>
      </div>
      <button
        onClick={onChange}
        className={`relative flex-shrink-0 ml-4 w-10 h-[22px] rounded-full transition-colors ${
          enabled ? 'bg-navy-800' : 'bg-surface-200'
        }`}
        role="switch"
        aria-checked={enabled}
      >
        <span
          className={`absolute top-[3px] left-[3px] w-4 h-4 rounded-full bg-white shadow-sm transition-transform ${
            enabled ? 'translate-x-[18px]' : 'translate-x-0'
          }`}
        />
      </button>
    </div>
  )
}


/* ─── SVG Icon components ─── */
function ClipboardIcon({ className }) {
  return <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8"><path strokeLinecap="round" strokeLinejoin="round" d="M9 12h3.75M9 15h3.75M9 18h3.75m3 .75H18a2.25 2.25 0 002.25-2.25V6.108c0-1.135-.845-2.098-1.976-2.192a48.424 48.424 0 00-1.123-.08m-5.801 0c-.065.21-.1.433-.1.664 0 .414.336.75.75.75h4.5a.75.75 0 00.75-.75 2.25 2.25 0 00-.1-.664m-5.8 0A2.251 2.251 0 0113.5 2.25H15c1.012 0 1.867.668 2.15 1.586m-5.8 0c-.376.023-.75.05-1.124.08C9.095 4.01 8.25 4.973 8.25 6.108V8.25m0 0H4.875c-.621 0-1.125.504-1.125 1.125v11.25c0 .621.504 1.125 1.125 1.125h9.75c.621 0 1.125-.504 1.125-1.125V9.375c0-.621-.504-1.125-1.125-1.125H8.25z" /></svg>
}
function AlertIcon({ className }) {
  return <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8"><path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" /></svg>
}
function BookIcon({ className }) {
  return <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8"><path strokeLinecap="round" strokeLinejoin="round" d="M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 016-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0018 18a8.967 8.967 0 00-6 2.292m0-14.25v14.25" /></svg>
}
function SmileIcon({ className }) {
  return <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8"><path strokeLinecap="round" strokeLinejoin="round" d="M15.182 15.182a4.5 4.5 0 01-6.364 0M21 12a9 9 0 11-18 0 9 9 0 0118 0zM9.75 9.75c0 .414-.168.75-.375.75S9 10.164 9 9.75 9.168 9 9.375 9s.375.336.375.75zm-.375 0h.008v.015h-.008V9.75zm5.625 0c0 .414-.168.75-.375.75s-.375-.336-.375-.75.168-.75.375-.75.375.336.375.75zm-.375 0h.008v.015h-.008V9.75z" /></svg>
}
function TargetIcon({ className }) {
  return <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8"><path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
}
function TrophyIcon({ className }) {
  return <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8"><path strokeLinecap="round" strokeLinejoin="round" d="M16.5 18.75h-9m9 0a3 3 0 013 3h-15a3 3 0 013-3m9 0v-3.375c0-.621-.503-1.125-1.125-1.125h-.871M7.5 18.75v-3.375c0-.621.504-1.125 1.125-1.125h.872m5.007 0H9.497m5.007 0a7.454 7.454 0 01-.982-3.172M9.497 14.25a7.454 7.454 0 00.981-3.172M5.25 4.236c-.982.143-1.954.317-2.916.52A6.003 6.003 0 007.73 9.728M5.25 4.236V4.5c0 2.108.966 3.99 2.48 5.228M5.25 4.236V2.721C7.456 2.41 9.71 2.25 12 2.25c2.291 0 4.545.16 6.75.47v1.516M18.75 4.236c.982.143 1.954.317 2.916.52A6.003 6.003 0 0016.27 9.728M18.75 4.236V4.5c0 2.108-.966 3.99-2.48 5.228m0 0a6.042 6.042 0 01-2.77.988m-5.96 0a6.042 6.042 0 002.77.988" /></svg>
}
function SparkleIcon({ className }) {
  return <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8"><path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z" /></svg>
}
function BellIcon({ className }) {
  return <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8"><path strokeLinecap="round" strokeLinejoin="round" d="M14.857 17.082a23.848 23.848 0 005.454-1.31A8.967 8.967 0 0118 9.75v-.7V9A6 6 0 006 9v.75a8.967 8.967 0 01-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 01-5.714 0m5.714 0a3 3 0 11-5.714 0" /></svg>
}
