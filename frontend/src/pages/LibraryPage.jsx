import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import LibraryBrowser from '../components/LibraryBrowser'
import NotificationBell from '../components/NotificationBell'
import { uploadToLibrary, getEnrolledCourses } from '../services/api'

export default function LibraryPage() {
  const navigate = useNavigate()
  const { logout: doLogout } = useAuth()
  const [showUpload, setShowUpload] = useState(false)
  const [browserKey, setBrowserKey] = useState(0)

  return (
    <div className="min-h-screen bg-surface-50">

      {/* ══════════ NAV ══════════ */}
      <nav className="sticky top-0 z-40 border-b border-surface-200/80 bg-white/80 backdrop-blur-xl">
        <div className="mx-auto flex h-14 max-w-[1360px] items-center justify-between px-5">
          <div className="flex items-center gap-6">
            <button onClick={() => navigate('/dashboard')} className="flex items-center gap-2 group">
              <div className="w-7 h-7 rounded-lg bg-navy-800 flex items-center justify-center">
                <span className="text-white font-display text-sm font-bold">S</span>
              </div>
              <span className="text-[15px] font-bold text-navy-900 group-hover:text-navy-700 transition-colors">Shadow</span>
            </button>
            <div className="hidden md:flex items-center gap-1">
              {[
                { label: 'Dashboard', path: '/dashboard' },
                { label: 'Courses', path: '/courses' },
                { label: 'CGPA', path: '/cgpa' },
                { label: 'Library', path: '/library', active: true },
                { label: 'SmartStudy', path: '/smartstudy' },
              ].map(link => (
                <button
                  key={link.path}
                  onClick={() => navigate(link.path)}
                  className={`px-3 py-1.5 rounded-lg text-[13px] font-medium transition-colors ${
                    link.active
                      ? 'bg-navy-800/[0.06] text-navy-800'
                      : 'text-surface-400 hover:text-navy-800 hover:bg-surface-100'
                  }`}
                >
                  {link.label}
                </button>
              ))}
            </div>
          </div>
          <div className="flex items-center gap-2">
            <NotificationBell />
            <button
              onClick={() => { doLogout() }}
              className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-[13px] font-medium text-surface-400 hover:text-navy-800 hover:bg-surface-100 transition-colors"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
                <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 9V5.25A2.25 2.25 0 0013.5 3h-6a2.25 2.25 0 00-2.25 2.25v13.5A2.25 2.25 0 007.5 21h6a2.25 2.25 0 002.25-2.25V15m3 0l3-3m0 0l-3-3m3 3H9" />
              </svg>
              <span className="hidden sm:inline">Sign out</span>
            </button>
          </div>
        </div>
      </nav>

      {/* ══════════ HERO HEADER ══════════ */}
      <div className="border-b border-surface-200/60 bg-white hero-atmosphere">
        <div className="mx-auto max-w-[1360px] px-5 py-8 relative">
          <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4">
            <div>
              <div className="flex items-center gap-2.5 mb-2">
                <h1 className="font-display text-[28px] font-bold text-navy-900 tracking-tight">Learning Library</h1>
                <span className="px-2 py-0.5 rounded-md bg-violet-500/[0.08] border border-violet-200/40 text-[10px] font-bold text-violet-700 uppercase tracking-wider">Shared</span>
              </div>
              <p className="text-[13px] text-surface-400 mt-1">Access and share course materials with your classmates</p>
            </div>
            <button
              onClick={() => setShowUpload(true)}
              className="flex items-center gap-2 px-4 py-2.5 bg-navy-800 hover:bg-navy-900 text-white rounded-xl text-[13px] font-semibold transition-all shadow-sm"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5m-13.5-9L12 3m0 0 4.5 4.5M12 3v13.5" />
              </svg>
              Upload Document
            </button>
          </div>
        </div>
      </div>

      {/* ══════════ CONTENT ══════════ */}
      <div className="mx-auto max-w-[1360px] px-5 py-6">
        <LibraryBrowser key={browserKey} />
      </div>

      {/* ══════════ UPLOAD MODAL ══════════ */}
      {showUpload && (
        <UploadModal
          onClose={() => setShowUpload(false)}
          onSuccess={() => { setBrowserKey(k => k + 1) }}
        />
      )}
    </div>
  )
}


/* ═══════════════════════════════════════════
   Upload Modal
   ═══════════════════════════════════════════ */
function UploadModal({ onClose, onSuccess }) {
  const [courses, setCourses] = useState([])
  const [file, setFile] = useState(null)
  const [topic, setTopic] = useState('')
  const [courseId, setCourseId] = useState('')
  const [weekNum, setWeekNum] = useState('')
  const [isPublic, setIsPublic] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(false)
  const [scanStatus, setScanStatus] = useState(null)
  const [relevanceWarning, setRelevanceWarning] = useState(null)
  const [entering, setEntering] = useState(false)
  const [isDragging, setIsDragging] = useState(false)
  const backdropRef = useRef(null)

  useEffect(() => {
    requestAnimationFrame(() => setEntering(true))
    getEnrolledCourses(true).then(setCourses).catch(() => {})
  }, [])

  const close = () => { setEntering(false); setTimeout(onClose, 200) }

  const VALID_MIME_TYPES = ['application/pdf', 'application/vnd.ms-powerpoint', 'application/vnd.openxmlformats-officedocument.presentationml.presentation']
  const VALID_EXTENSIONS = ['.pdf', '.pptx', '.ppt']

  const suggestTopicFromFilename = (filename) => {
    // Strip extension, replace separators with spaces, clean up
    let name = filename.replace(/\.[^.]+$/, '')
    name = name.replace(/[-_]+/g, ' ').replace(/([a-z])([A-Z])/g, '$1 $2')
    // Remove common prefixes like "Week 3 -" or "CSC401_"
    name = name.replace(/^(week\s*\d+\s*[-–—]?\s*)/i, '')
    name = name.replace(/^[A-Z]{2,4}\d{3,4}[\s_-]*/i, '')
    name = name.trim()
    if (name.length < 2) return ''
    // Title case
    return name.replace(/\b\w/g, c => c.toUpperCase())
  }

  const validateAndSetFile = (f) => {
    if (!f) return
    const ext = f.name.slice(f.name.lastIndexOf('.')).toLowerCase()
    if (!VALID_MIME_TYPES.includes(f.type) && !VALID_EXTENSIONS.includes(ext)) {
      setError('Only PDF and PowerPoint files are supported.')
      return
    }
    if (f.size > 10 * 1024 * 1024) { setError('Maximum file size is 10 MB.'); return }
    setFile(f)
    setError(null)
    // Auto-suggest topic from filename if topic is empty
    if (!topic) {
      const suggested = suggestTopicFromFilename(f.name)
      if (suggested) setTopic(suggested)
    }
  }

  const handleFile = (e) => validateAndSetFile(e.target.files[0])

  const handleDrop = (e) => {
    e.preventDefault()
    setIsDragging(false)
    validateAndSetFile(e.dataTransfer.files[0])
  }

  const handleDragOver = (e) => { e.preventDefault(); setIsDragging(true) }
  const handleDragLeave = (e) => { e.preventDefault(); setIsDragging(false) }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!file || !topic || !courseId) { setError('Please fill in all required fields.'); return }
    setUploading(true)
    setUploadProgress(0)
    setError(null)
    try {
      const result = await uploadToLibrary({
        file, topic, courseId,
        weekNumber: weekNum ? parseInt(weekNum) : null,
        isPublic,
        onProgress: (pct) => setUploadProgress(pct)
      })
      setUploadProgress(100)
      setSuccess(true)
      setScanStatus(result?.scan_status || 'clean')
      if (result?.relevance_warning) {
        setRelevanceWarning(result.relevance_warning)
      }
      onSuccess()
      const isPending = result?.scan_status && result.scan_status !== 'clean'
      if (!result?.relevance_warning && !isPending) {
        setTimeout(close, 1800)
      }
    } catch (err) {
      setError(err.detail || 'Failed to upload. Please try again.')
    } finally { setUploading(false) }
  }

  const fmtSize = (b) => b < 1024 ? `${b} B` : b < 1048576 ? `${(b / 1024).toFixed(1)} KB` : `${(b / 1048576).toFixed(1)} MB`

  const inputCls = 'w-full bg-surface-50 border border-surface-200/80 rounded-xl px-3.5 py-2.5 text-[13px] text-navy-900 placeholder:text-surface-300 focus:border-navy-300 focus:ring-2 focus:ring-navy-100 focus:bg-white transition-all outline-none'

  return (
    <div
      ref={backdropRef}
      onClick={(e) => e.target === backdropRef.current && close()}
      className={`fixed inset-0 z-50 bg-navy-950/40 backdrop-blur-sm flex items-center justify-center p-4 transition-opacity duration-200 ${entering ? 'opacity-100' : 'opacity-0'}`}
    >
      <div className={`bg-white rounded-2xl shadow-2xl max-w-lg w-full max-h-[90vh] overflow-hidden flex flex-col transition-all duration-300 ${
        entering ? 'scale-100 translate-y-0 opacity-100' : 'scale-95 translate-y-4 opacity-0'
      }`}>

        {/* Header */}
        <div className="flex-shrink-0 px-6 pt-6 pb-0 flex items-start justify-between">
          <div>
            <h2 className="font-display text-[20px] font-bold text-navy-900 tracking-tight">Upload Document</h2>
            <p className="text-[12px] text-surface-400 mt-0.5">Share course materials with classmates</p>
          </div>
          <button onClick={close} className="p-1.5 rounded-lg text-surface-300 hover:text-surface-400 hover:bg-surface-100 transition-all -mt-1 -mr-1">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto px-6 py-5 space-y-4">

          {/* Success */}
          {success && scanStatus === 'clean' && (
            <div className="px-4 py-3 rounded-xl bg-emerald-50 border border-emerald-200/60 flex items-center gap-2.5">
              <svg className="w-4 h-4 text-emerald-600 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75 11.25 15 15 9.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
              </svg>
              <span className="text-[12px] font-semibold text-emerald-700">Uploaded successfully{isPublic ? ' — now available to other students' : ''}.</span>
            </div>
          )}

          {/* Pending security review */}
          {success && scanStatus && scanStatus !== 'clean' && (
            <div className="px-4 py-3 rounded-xl bg-amber-50 border border-amber-200/60 flex items-center gap-2.5">
              <svg className="w-4 h-4 text-amber-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m0 3.75h.008v.008H12v-.008Zm9-.75a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
              </svg>
              <span className="text-[12px] font-semibold text-amber-700">Uploaded successfully. Your document is pending security review and will be available to other students once verified.</span>
            </div>
          )}

          {/* Relevance Warning */}
          {relevanceWarning && (
            <div className="px-4 py-3 rounded-xl bg-amber-50 border border-amber-200/60 flex items-start gap-2.5">
              <svg className="w-4 h-4 text-amber-500 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" />
              </svg>
              <div>
                <span className="text-[12px] font-semibold text-amber-700">{relevanceWarning}</span>
                <button onClick={close} className="block mt-1.5 text-[11px] font-medium text-amber-600 underline hover:text-amber-800">Dismiss & close</button>
              </div>
            </div>
          )}

          {/* Error */}
          {error && (
            <div className="px-4 py-2.5 rounded-xl bg-red-50 border border-red-100 flex items-center gap-2">
              <svg className="w-4 h-4 text-red-400 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9 3.75h.008v.008H12v-.008Z" />
              </svg>
              <span className="text-[12px] font-medium text-red-600">{error}</span>
            </div>
          )}

          {/* File drop zone */}
          <div>
            <label className="flex items-baseline gap-1.5 mb-1.5">
              <span className="text-[12px] font-semibold text-navy-800 uppercase tracking-wider">Document</span>
              <span className="text-red-400 text-[10px]">*</span>
            </label>
            <label
              htmlFor="file-upload-input"
              onDragOver={handleDragOver}
              onDragEnter={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              className={`block cursor-pointer rounded-xl border-2 border-dashed p-6 text-center transition-all duration-200 ${
                isDragging
                  ? 'border-indigo-500 bg-indigo-50/10 scale-[1.01]'
                  : file
                    ? 'border-emerald-300 bg-emerald-50/30 hover:border-navy-300 hover:bg-navy-50/30'
                    : 'border-surface-200 hover:border-navy-300 hover:bg-navy-50/30'
              }`}
            >
              <input type="file" id="file-upload-input" accept=".pdf,.ppt,.pptx" onChange={handleFile} className="hidden" />
              {isDragging ? (
                <>
                  <svg className="w-8 h-8 text-indigo-500 mx-auto mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5m-13.5-9L12 3m0 0 4.5 4.5M12 3v13.5" />
                  </svg>
                  <p className="text-[13px] font-semibold text-indigo-600">Drop your file here</p>
                  <p className="text-[11px] text-indigo-400 mt-0.5">PDF or PowerPoint, max 10 MB</p>
                </>
              ) : file ? (
                <>
                  <svg className="w-8 h-8 text-emerald-500 mx-auto mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75 11.25 15 15 9.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
                  </svg>
                  <p className="text-[13px] font-semibold text-navy-900">{file.name}</p>
                  <p className="text-[11px] text-surface-400 mt-0.5">{fmtSize(file.size)} — click or drop to replace</p>
                </>
              ) : (
                <>
                  <svg className="w-8 h-8 text-surface-300 mx-auto mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5m-13.5-9L12 3m0 0 4.5 4.5M12 3v13.5" />
                  </svg>
                  <p className="text-[13px] font-medium text-navy-800">Drag & drop or click to upload</p>
                  <p className="text-[11px] text-surface-300 mt-0.5">PDF or PowerPoint, max 10 MB</p>
                </>
              )}
            </label>
          </div>

          {/* Topic */}
          <div>
            <label className="flex items-baseline gap-1.5 mb-1.5">
              <span className="text-[12px] font-semibold text-navy-800 uppercase tracking-wider">Topic</span>
              <span className="text-red-400 text-[10px]">*</span>
              {file && topic && <span className="text-[10px] text-surface-300 normal-case tracking-normal font-normal ml-1">suggested from filename — edit if needed</span>}
            </label>
            <input type="text" value={topic} onChange={(e) => setTopic(e.target.value)} placeholder="e.g., Binary Search Trees" className={inputCls} required />
          </div>

          {/* Course + Week row */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="flex items-baseline gap-1.5 mb-1.5">
                <span className="text-[12px] font-semibold text-navy-800 uppercase tracking-wider">Course</span>
                <span className="text-red-400 text-[10px]">*</span>
              </label>
              <select value={courseId} onChange={(e) => setCourseId(e.target.value)} className={inputCls} required>
                <option value="">Select course</option>
                {courses.map(en => (
                  <option key={en.course.id} value={en.course.id}>{en.course.code}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="flex items-baseline gap-1.5 mb-1.5">
                <span className="text-[12px] font-semibold text-navy-800 uppercase tracking-wider">Week</span>
                <span className="text-[10px] text-surface-300 normal-case tracking-normal font-normal">optional</span>
              </label>
              <select value={weekNum} onChange={(e) => setWeekNum(e.target.value)} className={inputCls}>
                <option value="">—</option>
                {Array.from({ length: 15 }, (_, i) => (
                  <option key={i + 1} value={i + 1}>Week {i + 1}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Public toggle */}
          <div className="border-t border-surface-100 pt-4">
            <label className="flex items-center gap-3 cursor-pointer group">
              <div
                onClick={() => setIsPublic(!isPublic)}
                className={`w-5 h-5 rounded-md border-2 flex items-center justify-center transition-all ${
                  isPublic ? 'bg-emerald-500 border-emerald-500' : 'border-surface-300 group-hover:border-surface-400'
                }`}
              >
                {isPublic && (
                  <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="3">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                  </svg>
                )}
              </div>
              <div>
                <p className="text-[13px] font-semibold text-navy-900">Make public</p>
                <p className="text-[11px] text-surface-400">
                  {isPublic ? 'Other students in this course can view and download' : 'Only you can access this document'}
                </p>
              </div>
            </label>
          </div>
        </form>

        {/* Footer */}
        <div className="flex-shrink-0 flex gap-3 px-6 py-4 border-t border-surface-100">
          <button type="button" onClick={close} disabled={uploading} className="flex-1 px-5 py-2.5 border border-surface-200 text-navy-700 rounded-xl text-[13px] font-semibold hover:bg-surface-50 transition-all disabled:opacity-40">
            Cancel
          </button>
          <button onClick={handleSubmit} disabled={uploading || !file || !topic || !courseId} className="flex-1 px-5 py-2.5 bg-navy-800 hover:bg-navy-900 text-white rounded-xl text-[13px] font-semibold transition-all disabled:opacity-40 flex flex-col items-center justify-center gap-1 relative overflow-hidden">
            {uploading ? (
              <>
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  <span>Uploading{uploadProgress > 0 ? ` ${uploadProgress}%` : '...'}</span>
                </div>
                <div className="absolute bottom-0 left-0 h-1 bg-white/40 transition-all duration-300" style={{ width: `${uploadProgress}%` }} />
              </>
            ) : (
              <div className="flex items-center gap-2">
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5m-13.5-9L12 3m0 0 4.5 4.5M12 3v13.5" />
                </svg>
                Upload
              </div>
            )}
          </button>
        </div>
      </div>
    </div>
  )
}
