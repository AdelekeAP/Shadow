import { useState, useEffect } from 'react'
import { browseLibrary, voteOnDocument, downloadLibraryDocument, getLibraryStats, getMyCourses } from '../services/api'
import DocumentViewer from './DocumentViewer'

export default function LibraryBrowser() {
  const [documents, setDocuments] = useState([])
  const [courses, setCourses] = useState([])
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [search, setSearch] = useState('')
  const [selCourse, setSelCourse] = useState('')
  const [selWeek, setSelWeek] = useState('')
  const [showFilters, setShowFilters] = useState(false)
  const [votingId, setVotingId] = useState(null)
  const [downloadingId, setDownloadingId] = useState(null)
  const [viewingDoc, setViewingDoc] = useState(null)
  const [toast, setToast] = useState(null)

  useEffect(() => { loadData() }, [])
  useEffect(() => { applyFilters() }, [search, selCourse, selWeek])

  const showToast = (msg, type = 'error') => { setToast({ msg, type }); setTimeout(() => setToast(null), 3000) }

  const loadData = async () => {
    try {
      setLoading(true)
      const [docs, st, cr] = await Promise.all([browseLibrary(), getLibraryStats(), getMyCourses(true)])
      setDocuments(docs); setStats(st); setCourses(cr); setError(null)
    } catch { setError('Failed to load library.') }
    finally { setLoading(false) }
  }

  const applyFilters = async () => {
    try {
      setLoading(true)
      const docs = await browseLibrary({
        search: search || undefined,
        courseId: selCourse || undefined,
        weekNumber: selWeek ? parseInt(selWeek) : undefined,
      })
      setDocuments(docs); setError(null)
    } catch { setError('Failed to filter.') }
    finally { setLoading(false) }
  }

  const handleVote = async (id, val) => {
    try {
      setVotingId(id)
      await voteOnDocument(id, val)
      setDocuments(d => d.map(doc => doc.id === id ? { ...doc, helpful_votes: doc.helpful_votes + val } : doc))
    } catch (err) { showToast(err.detail || 'Failed to record vote') }
    finally { setVotingId(null) }
  }

  const handleDownload = async (doc) => {
    try {
      setDownloadingId(doc.id)
      const blob = await downloadLibraryDocument(doc.id)
      const url = window.URL.createObjectURL(blob)
      const a = window.document.createElement('a')
      a.href = url; a.download = doc.file_name
      window.document.body.appendChild(a); a.click()
      window.document.body.removeChild(a)
      window.URL.revokeObjectURL(url)
      setDocuments(d => d.map(dd => dd.id === doc.id ? { ...dd, download_count: dd.download_count + 1 } : dd))
    } catch { showToast('Failed to download') }
    finally { setDownloadingId(null) }
  }

  const clearFilters = () => { setSearch(''); setSelCourse(''); setSelWeek('') }
  const hasFilters = search || selCourse || selWeek

  const fmtSize = (b) => b < 1024 ? `${b} B` : b < 1048576 ? `${(b / 1024).toFixed(1)} KB` : `${(b / 1048576).toFixed(1)} MB`

  const fileTypeStyle = (t) => {
    if (t === 'pdf') return 'bg-red-500/10 text-red-600 border-red-200/60'
    if (t === 'pptx' || t === 'ppt') return 'bg-amber-500/10 text-amber-700 border-amber-200/60'
    return 'bg-surface-100 text-surface-400 border-surface-200/60'
  }

  /* ── Loading skeleton ── */
  if (loading && !documents.length) return (
    <div className="space-y-4">
      {/* Stats skeleton */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {[1, 2, 3, 4].map(i => (
          <div key={i} className="rounded-xl border border-surface-200/60 bg-white p-4 animate-pulse">
            <div className="h-3 w-16 bg-surface-100 rounded mb-2" />
            <div className="h-6 w-10 bg-surface-100/60 rounded" />
          </div>
        ))}
      </div>
      {/* Card skeletons */}
      {[1, 2, 3].map(i => (
        <div key={i} className="rounded-2xl border border-surface-200/60 bg-white p-5 animate-pulse">
          <div className="h-4 w-48 bg-surface-100 rounded-lg mb-2" />
          <div className="h-3 w-32 bg-surface-100/60 rounded-lg mb-3" />
          <div className="flex gap-2">
            <div className="h-5 w-12 bg-surface-100 rounded-full" />
            <div className="h-5 w-16 bg-surface-100 rounded-full" />
          </div>
        </div>
      ))}
    </div>
  )

  return (
    <div className="space-y-5">

      {/* ── Stats strip ── */}
      {stats && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[
            { label: 'Documents', value: stats.total_documents, icon: DocIcon },
            { label: 'Contributors', value: stats.total_contributors, icon: UsersIcon },
            { label: 'Downloads', value: stats.total_downloads || 0, icon: DownloadIcon },
            { label: 'Courses', value: stats.courses_covered || courses.length, icon: BookIcon },
          ].map(s => (
            <div key={s.label} className="rounded-xl border border-surface-200/60 bg-white p-4">
              <div className="flex items-center gap-1.5 mb-1.5">
                <s.icon className="w-3.5 h-3.5 text-surface-300" />
                <span className="text-[10px] font-semibold uppercase tracking-wider text-surface-400">{s.label}</span>
              </div>
              <p className="font-display text-[22px] font-bold text-navy-900 leading-none">{s.value ?? '—'}</p>
            </div>
          ))}
        </div>
      )}

      {/* ── Search + Filters ── */}
      <div className="rounded-xl border border-surface-200/60 bg-white">
        <div className="flex items-center gap-3 p-3">
          {/* Search */}
          <div className="relative flex-1">
            <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-surface-300" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
              <path strokeLinecap="round" strokeLinejoin="round" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z" />
            </svg>
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search topics or files..."
              className="w-full bg-surface-50 border border-surface-200/80 rounded-xl pl-9 pr-3 py-2 text-[12px] text-navy-900 placeholder:text-surface-300 focus:border-navy-300 focus:ring-2 focus:ring-navy-100 focus:bg-white transition-all outline-none"
            />
          </div>
          {/* Filter toggle */}
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`flex items-center gap-1.5 px-3 py-2 rounded-xl text-[12px] font-semibold transition-all border ${
              showFilters || hasFilters
                ? 'bg-navy-800/[0.06] text-navy-800 border-navy-200/40'
                : 'bg-surface-50 text-surface-400 border-surface-200/80 hover:text-navy-700'
            }`}
          >
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 3c2.755 0 5.455.232 8.083.678.533.09.917.556.917 1.096v1.044a2.25 2.25 0 0 1-.659 1.591l-5.432 5.432a2.25 2.25 0 0 0-.659 1.591v2.927a2.25 2.25 0 0 1-1.244 2.013L9.75 21v-6.568a2.25 2.25 0 0 0-.659-1.591L3.659 7.409A2.25 2.25 0 0 1 3 5.818V4.774c0-.54.384-1.006.917-1.096A48.32 48.32 0 0 1 12 3Z" />
            </svg>
            Filters
            {hasFilters && <span className="w-1.5 h-1.5 rounded-full bg-navy-600" />}
          </button>
        </div>

        {/* Filter panel */}
        {showFilters && (
          <div className="border-t border-surface-100 px-3 py-3 flex flex-wrap items-end gap-3">
            <div className="flex-1 min-w-[140px]">
              <label className="text-[10px] font-semibold uppercase tracking-wider text-surface-400 mb-1 block">Course</label>
              <select value={selCourse} onChange={(e) => setSelCourse(e.target.value)}
                className="w-full bg-surface-50 border border-surface-200/80 rounded-xl px-3 py-2 text-[12px] text-navy-900 focus:border-navy-300 focus:ring-2 focus:ring-navy-100 outline-none transition-all"
              >
                <option value="">All Courses</option>
                {courses.map(c => (
                  <option key={c.id} value={c.id}>{c.code || c.course?.code} — {c.title || c.course?.title}</option>
                ))}
              </select>
            </div>
            <div className="w-28">
              <label className="text-[10px] font-semibold uppercase tracking-wider text-surface-400 mb-1 block">Week</label>
              <select value={selWeek} onChange={(e) => setSelWeek(e.target.value)}
                className="w-full bg-surface-50 border border-surface-200/80 rounded-xl px-3 py-2 text-[12px] text-navy-900 focus:border-navy-300 focus:ring-2 focus:ring-navy-100 outline-none transition-all"
              >
                <option value="">All</option>
                {Array.from({ length: 15 }, (_, i) => (
                  <option key={i + 1} value={i + 1}>Week {i + 1}</option>
                ))}
              </select>
            </div>
            {hasFilters && (
              <button onClick={clearFilters} className="text-[11px] font-semibold text-red-600 hover:text-red-700 transition-colors pb-2">
                Clear
              </button>
            )}
          </div>
        )}
      </div>

      {/* ── Error ── */}
      {error && (
        <div className="rounded-xl border border-red-200/60 bg-red-50 p-4 flex items-center gap-2.5">
          <svg className="w-4 h-4 text-red-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9 3.75h.008v.008H12v-.008Z" />
          </svg>
          <span className="text-[12px] font-medium text-red-700">{error}</span>
          <button onClick={loadData} className="ml-auto text-[11px] font-semibold text-red-600 hover:text-red-800 transition-colors">Retry</button>
        </div>
      )}

      {/* ── Empty state ── */}
      {!loading && documents.length === 0 && (
        <div className="flex flex-col items-center py-16">
          <div className="w-14 h-14 rounded-2xl bg-surface-100 flex items-center justify-center mb-4">
            <svg className="w-6 h-6 text-surface-300" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
              <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z" />
            </svg>
          </div>
          <p className="text-[14px] font-semibold text-navy-900 mb-1">No documents found</p>
          <p className="text-[12px] text-surface-400">
            {hasFilters ? 'Try adjusting your filters' : 'Be the first to contribute!'}
          </p>
          {hasFilters && (
            <button onClick={clearFilters} className="mt-3 text-[12px] font-semibold text-navy-700 hover:text-navy-900 transition-colors">Clear filters</button>
          )}
        </div>
      )}

      {/* ── Document cards ── */}
      {documents.length > 0 && (
        <div className="space-y-3">
          {documents.map(doc => (
            <div key={doc.id} className="group rounded-2xl border border-surface-200/60 bg-white hover:border-surface-300/80 hover:shadow-lg hover:shadow-navy-900/[0.04] transition-all duration-300 p-5">
              <div className="flex flex-col md:flex-row md:items-start gap-4">
                {/* Info */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-start gap-3 mb-2.5">
                    {/* File type icon */}
                    <div className={`w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0 border ${fileTypeStyle(doc.file_type)}`}>
                      <span className="text-[9px] font-bold uppercase">{doc.file_type}</span>
                    </div>
                    <div className="flex-1 min-w-0">
                      <h3 className="text-[14px] font-semibold text-navy-900 mb-0.5 truncate">{doc.topic}</h3>
                      <p className="text-[11px] text-surface-400 truncate">{doc.file_name}</p>
                    </div>
                  </div>

                  {/* Badges */}
                  <div className="flex flex-wrap gap-1.5 mb-3 ml-12">
                    {doc.course_code && (
                      <span className="px-2 py-0.5 text-[10px] font-semibold rounded-md bg-navy-800/[0.06] text-navy-700">{doc.course_code}</span>
                    )}
                    {doc.week_number && (
                      <span className="px-2 py-0.5 text-[10px] font-semibold rounded-md bg-surface-100 text-surface-400">Week {doc.week_number}</span>
                    )}
                    <span className="px-2 py-0.5 text-[10px] rounded-md bg-surface-100/60 text-surface-300">{fmtSize(doc.file_size)}</span>
                  </div>

                  {/* Meta */}
                  <div className="flex items-center gap-3 ml-12 text-[11px] text-surface-400">
                    <span className="flex items-center gap-1">
                      <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2"><path strokeLinecap="round" strokeLinejoin="round" d="M2.036 12.322a1.012 1.012 0 0 1 0-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178Z" /><path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" /></svg>
                      {doc.view_count}
                    </span>
                    <span className="flex items-center gap-1">
                      <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2"><path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5M16.5 12 12 16.5m0 0L7.5 12m4.5 4.5V3" /></svg>
                      {doc.download_count}
                    </span>
                    <span className="w-px h-3 bg-surface-200" />
                    <span>{doc.uploader_name || 'Anonymous'}</span>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex md:flex-col items-center gap-2 flex-shrink-0">
                  {/* View */}
                  <button
                    onClick={() => setViewingDoc(doc)}
                    className="px-3.5 py-2 rounded-xl border border-surface-200/80 text-[12px] font-semibold text-navy-700 hover:bg-surface-50 hover:border-surface-300 transition-all flex items-center gap-1.5"
                  >
                    <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2"><path strokeLinecap="round" strokeLinejoin="round" d="M2.036 12.322a1.012 1.012 0 0 1 0-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178Z" /><path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" /></svg>
                    View
                  </button>
                  {/* Download */}
                  <button
                    onClick={() => handleDownload(doc)}
                    disabled={downloadingId === doc.id}
                    className="px-3.5 py-2 rounded-xl bg-navy-800 hover:bg-navy-900 text-white text-[12px] font-semibold transition-all disabled:opacity-40 flex items-center gap-1.5"
                  >
                    {downloadingId === doc.id ? (
                      <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    ) : (
                      <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2"><path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5M16.5 12 12 16.5m0 0L7.5 12m4.5 4.5V3" /></svg>
                    )}
                    {downloadingId === doc.id ? 'Saving...' : 'Download'}
                  </button>
                  {/* Voting */}
                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => handleVote(doc.id, 1)}
                      disabled={votingId === doc.id}
                      className="p-1.5 rounded-lg bg-emerald-50 hover:bg-emerald-100 text-emerald-600 transition-all disabled:opacity-40"
                      title="Helpful"
                    >
                      <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2"><path strokeLinecap="round" strokeLinejoin="round" d="M6.633 10.25c.806 0 1.533-.446 2.031-1.08a9.041 9.041 0 0 1 2.861-2.4c.723-.384 1.35-.956 1.653-1.715a4.498 4.498 0 0 0 .322-1.672V3a.75.75 0 0 1 .75-.75 2.25 2.25 0 0 1 2.25 2.25c0 1.152-.26 2.243-.723 3.218-.266.558.107 1.282.725 1.282m0 0h3.126c1.026 0 1.945.694 2.054 1.715.045.422.068.85.068 1.285a11.95 11.95 0 0 1-2.649 7.521c-.388.482-.987.729-1.605.729H13.48c-.483 0-.964-.078-1.423-.23l-3.114-1.04a4.501 4.501 0 0 0-1.423-.23H5.904m7.594 0H5.904m7.594 0a.75.75 0 0 1 .75.75v.008a.75.75 0 0 1-.75.75h-7.594" /></svg>
                    </button>
                    <span className="min-w-[24px] text-center font-mono text-[11px] font-bold text-navy-800">{doc.helpful_votes}</span>
                    <button
                      onClick={() => handleVote(doc.id, -1)}
                      disabled={votingId === doc.id}
                      className="p-1.5 rounded-lg bg-red-50 hover:bg-red-100 text-red-500 transition-all disabled:opacity-40"
                      title="Not helpful"
                    >
                      <svg className="w-3.5 h-3.5 rotate-180" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2"><path strokeLinecap="round" strokeLinejoin="round" d="M6.633 10.25c.806 0 1.533-.446 2.031-1.08a9.041 9.041 0 0 1 2.861-2.4c.723-.384 1.35-.956 1.653-1.715a4.498 4.498 0 0 0 .322-1.672V3a.75.75 0 0 1 .75-.75 2.25 2.25 0 0 1 2.25 2.25c0 1.152-.26 2.243-.723 3.218-.266.558.107 1.282.725 1.282m0 0h3.126c1.026 0 1.945.694 2.054 1.715.045.422.068.85.068 1.285a11.95 11.95 0 0 1-2.649 7.521c-.388.482-.987.729-1.605.729H13.48c-.483 0-.964-.078-1.423-.23l-3.114-1.04a4.501 4.501 0 0 0-1.423-.23H5.904m7.594 0H5.904m7.594 0a.75.75 0 0 1 .75.75v.008a.75.75 0 0 1-.75.75h-7.594" /></svg>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* ── Toast ── */}
      {toast && (
        <div className={`fixed bottom-6 left-1/2 -translate-x-1/2 z-50 flex items-center gap-2.5 px-4 py-2.5 rounded-xl shadow-lg border animate-fade-in ${
          toast.type === 'error' ? 'bg-red-50 border-red-200/60 text-red-700' : 'bg-emerald-50 border-emerald-200/60 text-emerald-700'
        }`}>
          <svg className="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9 3.75h.008v.008H12v-.008Z" />
          </svg>
          <span className="text-[12px] font-semibold">{toast.msg}</span>
        </div>
      )}

      {/* ── Document Viewer ── */}
      {viewingDoc && <DocumentViewer document={viewingDoc} onClose={() => setViewingDoc(null)} />}
    </div>
  )
}


/* ─── Mini icon components ─── */
function DocIcon({ className }) {
  return <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5"><path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z" /></svg>
}
function UsersIcon({ className }) {
  return <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5"><path strokeLinecap="round" strokeLinejoin="round" d="M18 18.72a9.094 9.094 0 0 0 3.741-.479 3 3 0 0 0-4.682-2.72m.94 3.198.001.031c0 .225-.012.447-.037.666A11.944 11.944 0 0 1 12 21c-2.17 0-4.207-.576-5.963-1.584A6.062 6.062 0 0 1 6 18.719m12 0a5.971 5.971 0 0 0-.941-3.197m0 0A5.995 5.995 0 0 0 12 12.75a5.995 5.995 0 0 0-5.058 2.772m0 0a3 3 0 0 0-4.681 2.72 8.986 8.986 0 0 0 3.74.477m.94-3.197a5.971 5.971 0 0 0-.94 3.197M15 6.75a3 3 0 1 1-6 0 3 3 0 0 1 6 0Zm6 3a2.25 2.25 0 1 1-4.5 0 2.25 2.25 0 0 1 4.5 0Zm-13.5 0a2.25 2.25 0 1 1-4.5 0 2.25 2.25 0 0 1 4.5 0Z" /></svg>
}
function DownloadIcon({ className }) {
  return <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5"><path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5M16.5 12 12 16.5m0 0L7.5 12m4.5 4.5V3" /></svg>
}
function BookIcon({ className }) {
  return <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5"><path strokeLinecap="round" strokeLinejoin="round" d="M12 6.042A8.967 8.967 0 0 0 6 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 0 1 6 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 0 1 6-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0 0 18 18a8.967 8.967 0 0 0-6 2.292m0-14.25v14.25" /></svg>
}
