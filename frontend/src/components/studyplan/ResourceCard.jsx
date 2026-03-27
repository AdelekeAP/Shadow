import { useState, useEffect, memo } from 'react'
import { createVideoNote, getVideoNotes, deleteVideoNote, reportBrokenResource, API_BASE_URL } from '../../services/api'
import { linkifyText, getNoteColorClass, getNoteTypeIcon, getResourceStyle, getYouTubeVideoId } from './studyPlanHelpers.jsx'

const ResourceCard = memo(function ResourceCard({ resource, onPlayFullScreen, compact = false }) {
  const [isExpanded, setIsExpanded] = useState(!compact)
  const [isVideoLoaded, setIsVideoLoaded] = useState(false)
  const [reported, setReported] = useState(!!resource.report_reason)
  const [reporting, setReporting] = useState(false)

  // Note-taking state
  const [showNotes, setShowNotes] = useState(false)
  const [notes, setNotes] = useState([])
  const [loadingNotes, setLoadingNotes] = useState(false)
  const [newNote, setNewNote] = useState('')
  const [noteColor, setNoteColor] = useState('yellow')
  const [noteType, setNoteType] = useState('note')
  const [savingNote, setSavingNote] = useState(false)
  const [deleteConfirm, setDeleteConfirm] = useState(null)
  const [noteError, setNoteError] = useState(null)

  const videoId = resource.resource_type === 'youtube_video' ? getYouTubeVideoId(resource.resource_url) : null
  const style = getResourceStyle(resource.resource_type)

  useEffect(() => {
    if (showNotes && resource.id) loadNotes()
  }, [showNotes, resource.id])

  const loadNotes = async () => {
    try {
      setLoadingNotes(true)
      const response = await getVideoNotes(resource.id)
      setNotes(response.notes || [])
    } catch {
      setNoteError('Failed to load notes')
    } finally { setLoadingNotes(false) }
  }

  const handleAddNote = async () => {
    if (!newNote.trim()) return
    try {
      setSavingNote(true)
      setNoteError(null)
      const createdNote = await createVideoNote({
        resourceId: resource.id,
        content: newNote.trim(),
        noteType: noteType,
        color: noteColor
      })
      setNotes(prev => [...prev, createdNote])
      setNewNote('')
    } catch {
      setNoteError('Failed to save note. Please try again.')
    } finally { setSavingNote(false) }
  }

  const handleReport = async () => {
    if (reported || reporting) return
    try {
      setReporting(true)
      await reportBrokenResource(resource.study_plan_id, resource.id, 'broken_link')
      setReported(true)
    } catch {
      // Silently fail - not critical
    } finally { setReporting(false) }
  }

  const handleDeleteNote = async (noteId) => {
    try {
      await deleteVideoNote(noteId)
      setNotes(prev => prev.filter(n => n.id !== noteId))
      setDeleteConfirm(null)
    } catch {
      setNoteError('Failed to delete note.')
    }
  }

  const renderIcon = () => {
    const iconMap = {
      youtube: (
        <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 24 24">
          <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/>
        </svg>
      ),
      docs: (
        <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="1.8">
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
        </svg>
      ),
      article: (
        <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="1.8">
          <path strokeLinecap="round" strokeLinejoin="round" d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z" />
        </svg>
      ),
      practice: (
        <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="1.8">
          <path strokeLinecap="round" strokeLinejoin="round" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
        </svg>
      ),
      interactive: (
        <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="1.8">
          <path strokeLinecap="round" strokeLinejoin="round" d="M15 15l-2 5L9 9l11 4-5 2zm0 0l5 5M7.188 2.239l.777 2.897M5.136 7.965l-2.898-.777M13.95 4.05l-2.122 2.122m-5.657 5.656l-2.12 2.122" />
        </svg>
      ),
      reddit: <span className="text-white text-sm font-bold">R</span>,
      ai: (
        <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="1.8">
          <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z" />
        </svg>
      )
    }
    return iconMap[style.icon] || iconMap.ai
  }

  const getExternalLinkLabel = () => {
    const labels = { documentation: 'Read Docs', article: 'Read Article', practice: 'Start Practice', interactive: 'Open Tutorial', uploaded_slides: 'View Slides' }
    return labels[resource.resource_type] || 'View Resource'
  }

  const noteColorMap = {
    yellow: { bg: 'bg-amber-100', ring: 'ring-amber-400' },
    green: { bg: 'bg-emerald-100', ring: 'ring-emerald-400' },
    blue: { bg: 'bg-blue-100', ring: 'ring-blue-400' },
    pink: { bg: 'bg-pink-100', ring: 'ring-pink-400' },
    orange: { bg: 'bg-orange-100', ring: 'ring-orange-400' },
  }

  return (
    <div className={`bg-gradient-to-r ${style.gradient} rounded-xl border ${style.border} overflow-hidden transition-all duration-200`}>
      {/* Header */}
      <div className={compact ? "p-3" : "p-4"}>
        <div className="flex items-start gap-3">
          <div className={`w-10 h-10 ${style.iconBg} rounded-xl flex items-center justify-center flex-shrink-0 shadow-sm`}>
            {renderIcon()}
          </div>

          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between gap-2 mb-1.5">
              <h6 className="font-semibold text-navy-900 text-[13px] line-clamp-2 flex-1">
                {resource.resource_title || 'Learning Resource'}
              </h6>
              {resource.quality_score && (
                <div className={`flex-shrink-0 flex items-center gap-1 px-2 py-0.5 rounded-lg text-[10px] font-bold ${
                  resource.quality_score >= 80 ? 'bg-emerald-500/10 text-emerald-700 border border-emerald-200/60' :
                  resource.quality_score >= 60 ? 'bg-amber-500/10 text-amber-700 border border-amber-200/60' :
                  'bg-surface-100 text-surface-400 border border-surface-200/60'
                }`}>
                  <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 24 24"><path d="M11.48 3.499a.562.562 0 011.04 0l2.125 5.111a.563.563 0 00.475.345l5.518.442c.499.04.701.663.321.988l-4.204 3.602a.563.563 0 00-.182.557l1.285 5.385a.562.562 0 01-.84.61l-4.725-2.885a.563.563 0 00-.586 0L6.982 20.54a.562.562 0 01-.84-.61l1.285-5.386a.562.562 0 00-.182-.557l-4.204-3.602a.563.563 0 01.321-.988l5.518-.442a.563.563 0 00.475-.345L11.48 3.5z" /></svg>
                  {Math.round(resource.quality_score)}
                </div>
              )}
            </div>

            {resource.resource_description && (
              <p className={`text-[12px] text-surface-400 mb-3 leading-relaxed ${compact ? 'line-clamp-2' : 'line-clamp-3'}`}>
                {linkifyText(resource.resource_description)}
              </p>
            )}

            {/* Action Buttons */}
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-[10px] px-2 py-0.5 bg-white/80 text-navy-700 rounded-lg font-semibold border border-surface-200/60">
                {style.badge}
              </span>

              {resource.resource_type === 'youtube_video' && videoId && (
                <>
                  <button
                    onClick={() => { if (isExpanded) setIsVideoLoaded(false); setIsExpanded(!isExpanded) }}
                    className="text-[11px] px-3 py-1.5 bg-red-600 hover:bg-red-700 text-white rounded-lg font-semibold transition-all flex items-center gap-1.5"
                  >
                    {isExpanded ? (
                      <>
                        <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="2">
                          <path strokeLinecap="round" strokeLinejoin="round" d="M5 15l7-7 7 7" />
                        </svg>
                        Hide
                      </>
                    ) : (
                      <>
                        <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 24 24">
                          <path d="M8 5v14l11-7z"/>
                        </svg>
                        Play
                      </>
                    )}
                  </button>
                  <button
                    onClick={() => onPlayFullScreen({ url: resource.resource_url, title: resource.resource_title })}
                    className="text-[11px] px-3 py-1.5 bg-navy-800 hover:bg-navy-900 text-white rounded-lg font-semibold transition-all flex items-center gap-1.5"
                  >
                    <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="2">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
                    </svg>
                    Full Screen
                  </button>
                </>
              )}

              {resource.resource_type === 'youtube_video' && !compact && (
                <button
                  onClick={() => setShowNotes(!showNotes)}
                  className={`text-[11px] px-3 py-1.5 rounded-lg font-semibold transition-all flex items-center gap-1.5 ${
                    showNotes
                      ? 'bg-amber-500 hover:bg-amber-600 text-white'
                      : 'bg-amber-50 hover:bg-amber-100 text-amber-700 border border-amber-200/60'
                  }`}
                >
                  <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="1.8">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931z" />
                  </svg>
                  {showNotes ? 'Hide Notes' : 'Notes'}
                  {notes.length > 0 && !showNotes && (
                    <span className="bg-amber-600 text-white text-[10px] px-1.5 rounded-full font-bold">{notes.length}</span>
                  )}
                </button>
              )}

              {/* Uploaded slides — label only (inline SlideRangeViewer handles viewing) */}
              {resource.resource_type === 'uploaded_slides' && (
                <span className="text-[11px] px-3 py-1.5 bg-amber-100 text-amber-700 rounded-lg font-semibold flex items-center gap-1.5 border border-amber-200/60">
                  <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="2">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
                  </svg>
                  Your Uploaded Slides
                </span>
              )}

              {resource.resource_url && resource.resource_type !== 'youtube_video' && resource.resource_type !== 'uploaded_slides' && (() => {
                // Resolve API-relative URLs (e.g. /api/v1/library/documents/xxx/view)
                const resolvedUrl = resource.resource_url.startsWith('/api/')
                  ? `${API_BASE_URL}${resource.resource_url}`
                  : resource.resource_url
                return (
                <>
                  <a
                    href={resolvedUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-[11px] px-3 py-1.5 bg-navy-800 hover:bg-navy-900 text-white rounded-lg font-semibold transition-all flex items-center gap-1.5"
                  >
                    {getExternalLinkLabel()}
                    <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="2">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 6H5.25A2.25 2.25 0 003 8.25v10.5A2.25 2.25 0 005.25 21h10.5A2.25 2.25 0 0018 18.75V10.5m-10.5 6L21 3m0 0h-5.25M21 3v5.25" />
                    </svg>
                  </a>
                  <button
                    onClick={handleReport}
                    disabled={reported || reporting}
                    title={reported ? 'Reported' : 'Report broken link'}
                    className={`text-[11px] px-2 py-1.5 rounded-lg font-semibold transition-all flex items-center gap-1 ${
                      reported
                        ? 'bg-red-50 text-red-400 border border-red-200/60 cursor-default'
                        : 'bg-surface-100 hover:bg-red-50 text-surface-400 hover:text-red-500 border border-surface-200/60'
                    }`}
                  >
                    <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="2">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M3 3v1.5M3 21v-6m0 0l2.77-.693a9 9 0 016.208.682l.108.054a9 9 0 006.086.71l3.114-.732a48.524 48.524 0 01-.005-10.499l-3.11.732a9 9 0 01-6.085-.711l-.108-.054a9 9 0 00-6.208-.682L3 4.5M3 15V4.5" />
                    </svg>
                    {reported ? 'Reported' : reporting ? '...' : ''}
                  </button>
                </>
              )
              })()}
            </div>
          </div>
        </div>
      </div>

      {/* Embedded YouTube Player */}
      {resource.resource_type === 'youtube_video' && videoId && isExpanded && (
        <div className="border-t border-red-200/40 bg-black">
          <div className="relative w-full" style={{ paddingBottom: '56.25%' }}>
            {!isVideoLoaded && (
              <div className="absolute inset-0 flex items-center justify-center bg-[#0a0a0a]">
                <div className="w-8 h-8 border-2 border-red-500/30 border-t-red-500 rounded-full animate-spin" />
              </div>
            )}
            <iframe
              src={`https://www.youtube.com/embed/${videoId}?modestbranding=1&rel=0`}
              className="absolute top-0 left-0 w-full h-full"
              title={resource.resource_title || 'YouTube video'}
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
              allowFullScreen
              onLoad={() => setIsVideoLoaded(true)}
            />
          </div>

          <div className="bg-[#111] px-4 py-2 flex items-center justify-between">
            <div className="flex items-center gap-3 text-[11px] text-white/30">
              <span className="flex items-center gap-1.5">
                <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 24 24"><path d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>
                Watch in Shadow
              </span>
              {resource.quality_score && (
                <span>Score: {Math.round(resource.quality_score)}/100</span>
              )}
            </div>
            <a
              href={resource.resource_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-[11px] text-red-400 hover:text-red-300 transition-colors flex items-center gap-1"
            >
              YouTube
              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="2">
                <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 6H5.25A2.25 2.25 0 003 8.25v10.5A2.25 2.25 0 005.25 21h10.5A2.25 2.25 0 0018 18.75V10.5m-10.5 6L21 3m0 0h-5.25M21 3v5.25" />
              </svg>
            </a>
          </div>
        </div>
      )}

      {/* Notes Panel */}
      {showNotes && resource.resource_type === 'youtube_video' && (
        <div className="border-t border-amber-200/40 bg-amber-50/30 p-4">
          <div className="flex items-center justify-between mb-3">
            <h6 className="text-[13px] font-bold text-navy-900 flex items-center gap-2">
              <svg className="w-4 h-4 text-amber-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8">
                <path strokeLinecap="round" strokeLinejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931z" />
              </svg>
              Video Notes
              <span className="text-[10px] font-semibold bg-amber-200/60 text-amber-700 px-2 py-0.5 rounded-lg">{notes.length}</span>
            </h6>
          </div>

          {/* Note error */}
          {noteError && (
            <div className="px-3 py-2 rounded-lg bg-red-50 border border-red-100 flex items-center gap-2 mb-3">
              <svg className="w-3.5 h-3.5 text-red-400 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
              </svg>
              <span className="text-[11px] font-medium text-red-600">{noteError}</span>
              <button onClick={() => setNoteError(null)} className="ml-auto text-[10px] font-semibold text-red-500">Dismiss</button>
            </div>
          )}

          {/* Add New Note */}
          <div className="bg-white rounded-xl border border-surface-200/60 p-3 mb-3">
            <textarea
              value={newNote}
              onChange={(e) => setNewNote(e.target.value)}
              placeholder="Take a note about this video..."
              className="w-full text-[13px] text-navy-900 border-0 focus:ring-0 resize-none p-0 placeholder:text-surface-300 outline-none bg-transparent"
              rows={2}
            />

            <div className="flex items-center justify-between mt-2 pt-2 border-t border-surface-100">
              <div className="flex items-center gap-1.5">
                {['note', 'highlight', 'question', 'summary'].map((type) => (
                  <button
                    key={type}
                    onClick={() => setNoteType(type)}
                    className={`text-[10px] px-2 py-1 rounded-lg font-semibold transition-all ${
                      noteType === type ? 'bg-navy-800 text-white' : 'bg-surface-100 text-surface-400 hover:text-navy-700'
                    }`}
                  >
                    {getNoteTypeIcon(type)}
                  </button>
                ))}

                <span className="w-px h-4 bg-surface-200 mx-1" />

                {['yellow', 'green', 'blue', 'pink', 'orange'].map((color) => (
                  <button
                    key={color}
                    onClick={() => setNoteColor(color)}
                    className={`w-5 h-5 rounded-full transition-all ${noteColorMap[color].bg} ${
                      noteColor === color ? `ring-2 ${noteColorMap[color].ring} scale-110` : 'ring-1 ring-surface-200'
                    }`}
                  />
                ))}
              </div>

              <button
                onClick={handleAddNote}
                disabled={!newNote.trim() || savingNote}
                className="text-[11px] px-3 py-1.5 bg-navy-800 hover:bg-navy-900 disabled:bg-surface-200 disabled:text-surface-400 text-white rounded-lg font-semibold transition-all flex items-center gap-1"
              >
                {savingNote ? (
                  <div className="w-3 h-3 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                ) : (
                  <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
                  </svg>
                )}
                {savingNote ? 'Saving...' : 'Add'}
              </button>
            </div>
          </div>

          {/* Existing Notes */}
          {loadingNotes ? (
            <div className="flex justify-center py-4">
              <div className="w-5 h-5 border-2 border-surface-200 border-t-amber-500 rounded-full animate-spin" />
            </div>
          ) : notes.length === 0 ? (
            <div className="text-center py-4">
              <svg className="w-6 h-6 text-surface-300 mx-auto mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
                <path strokeLinecap="round" strokeLinejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931z" />
              </svg>
              <p className="text-[12px] text-surface-400">No notes yet. Start taking notes while watching!</p>
            </div>
          ) : (
            <div className="space-y-2 max-h-64 overflow-y-auto scrollbar-thin">
              {notes.map((note) => (
                <div key={note.id} className={`p-3 rounded-lg border-l-[3px] ${getNoteColorClass(note.color)} bg-white/60`}>
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-[10px] font-bold text-navy-700 bg-surface-100 px-1.5 py-0.5 rounded">{getNoteTypeIcon(note.note_type)}</span>
                        {note.formatted_timestamp && (
                          <span className="text-[10px] bg-surface-100 text-navy-600 px-1.5 py-0.5 rounded font-mono">{note.formatted_timestamp}</span>
                        )}
                        <span className="text-[10px] text-surface-300">{new Date(note.created_at).toLocaleDateString()}</span>
                      </div>
                      <p className="text-[12px] text-navy-800 leading-relaxed">{note.content}</p>
                    </div>
                    {deleteConfirm === note.id ? (
                      <div className="flex items-center gap-1 flex-shrink-0">
                        <button onClick={() => handleDeleteNote(note.id)} className="text-[10px] px-2 py-1 bg-red-500 text-white rounded-md font-semibold">Yes</button>
                        <button onClick={() => setDeleteConfirm(null)} className="text-[10px] px-2 py-1 bg-surface-200 text-navy-700 rounded-md font-semibold">No</button>
                      </div>
                    ) : (
                      <button
                        onClick={() => setDeleteConfirm(note.id)}
                        className="text-surface-300 hover:text-red-500 transition-colors p-1 flex-shrink-0"
                      >
                        <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="2">
                          <path strokeLinecap="round" strokeLinejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

    </div>
  )
})

export default ResourceCard
