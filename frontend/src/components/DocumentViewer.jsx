import { useState, useEffect, useRef } from 'react'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export default function DocumentViewer({ document, onClose }) {
  const [loading, setLoading] = useState(true)
  const [documentUrl, setDocumentUrl] = useState(null)
  const [error, setError] = useState(null)
  const [entering, setEntering] = useState(false)
  const backdropRef = useRef(null)

  useEffect(() => {
    window.scrollTo(0, 0)
    requestAnimationFrame(() => setEntering(true))
    loadDocument()
    return () => {
      if (documentUrl?.startsWith('blob:')) window.URL.revokeObjectURL(documentUrl)
    }
  }, [document])

  const close = () => { setEntering(false); setTimeout(onClose, 200) }

  const loadDocument = async () => {
    try {
      setLoading(true)
      setError(null)
      const token = localStorage.getItem('access_token')
      const res = await fetch(`${API_BASE}/api/v1/library/documents/${document.id}/view`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        throw new Error(data.detail || 'Failed to load document')
      }
      const blob = await res.blob()
      const pdfBlob = new Blob([blob], { type: 'application/pdf' })
      setDocumentUrl(window.URL.createObjectURL(pdfBlob))
      setLoading(false)
    } catch (err) {
      setError(err.message || 'Failed to load document.')
      setLoading(false)
    }
  }

  const handleDownload = async () => {
    try {
      const token = localStorage.getItem('access_token')
      const res = await fetch(`${API_BASE}/api/v1/library/documents/${document.id}/download`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!res.ok) throw new Error('Download failed')
      const blob = await res.blob()
      const url = window.URL.createObjectURL(blob)
      const a = window.document.createElement('a')
      a.href = url; a.download = document.file_name
      window.document.body.appendChild(a); a.click()
      window.document.body.removeChild(a)
      window.URL.revokeObjectURL(url)
    } catch {
      // silently fail — button is a secondary action
    }
  }

  if (!document) return null

  return (
    <div
      ref={backdropRef}
      onClick={(e) => e.target === backdropRef.current && close()}
      className={`fixed inset-0 z-50 bg-navy-950/50 backdrop-blur-sm flex items-center justify-center p-4 transition-opacity duration-200 ${entering ? 'opacity-100' : 'opacity-0'}`}
    >
      <div className={`bg-white rounded-2xl shadow-2xl w-full h-full max-w-6xl max-h-[90vh] flex flex-col overflow-hidden transition-all duration-300 ${
        entering ? 'scale-100 translate-y-0 opacity-100' : 'scale-95 translate-y-4 opacity-0'
      }`}>

        {/* Header */}
        <div className="flex-shrink-0 flex items-center justify-between px-5 py-3.5 border-b border-surface-100">
          <div className="flex-1 min-w-0 mr-4">
            <h2 className="text-[14px] font-semibold text-navy-900 truncate">{document.topic}</h2>
            <p className="text-[11px] text-surface-400 truncate">{document.file_name}</p>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleDownload}
              className="flex items-center gap-1.5 px-3.5 py-2 bg-navy-800 hover:bg-navy-900 text-white rounded-xl text-[12px] font-semibold transition-all"
            >
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5M16.5 12 12 16.5m0 0L7.5 12m4.5 4.5V3" />
              </svg>
              Download
            </button>
            <button onClick={close} className="p-1.5 rounded-lg text-surface-300 hover:text-surface-400 hover:bg-surface-100 transition-all">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* Viewer */}
        <div className="flex-1 relative bg-surface-100">
          {loading && (
            <div className="absolute inset-0 flex items-center justify-center z-10">
              <div className="w-8 h-8 border-2 border-surface-200 border-t-navy-800 rounded-full animate-spin" />
            </div>
          )}

          {error && (
            <div className="absolute inset-0 flex items-center justify-center z-10">
              <div className="text-center max-w-xs">
                <div className="w-12 h-12 rounded-xl bg-red-50 border border-red-100 flex items-center justify-center mx-auto mb-3">
                  <svg className="w-5 h-5 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9 3.75h.008v.008H12v-.008Z" />
                  </svg>
                </div>
                <p className="text-[13px] font-medium text-red-700 mb-3">{error}</p>
                <button onClick={handleDownload} className="px-4 py-2 bg-navy-800 hover:bg-navy-900 text-white rounded-xl text-[12px] font-semibold transition-all">
                  Download Instead
                </button>
              </div>
            </div>
          )}

          {documentUrl && !error && (
            <iframe src={documentUrl} className="w-full h-full border-0" title={document.file_name} />
          )}
        </div>

        {/* Footer */}
        <div className="flex-shrink-0 flex items-center justify-between px-5 py-2.5 border-t border-surface-100 bg-surface-50/50">
          <div className="flex items-center gap-3 text-[11px] text-surface-400">
            <span>{document.view_count || 0} views</span>
            <span className="w-px h-3 bg-surface-200" />
            <span>{document.download_count || 0} downloads</span>
            <span className="w-px h-3 bg-surface-200" />
            <span>{document.helpful_votes || 0} votes</span>
          </div>
          <div className="flex items-center gap-1.5">
            {document.file_type && (
              <span className="px-2 py-0.5 rounded-md text-[10px] font-semibold bg-surface-100 text-surface-400 border border-surface-200/60 uppercase">{document.file_type}</span>
            )}
            {document.week_number && (
              <span className="px-2 py-0.5 rounded-md text-[10px] font-semibold bg-navy-800/[0.06] text-navy-700">Week {document.week_number}</span>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
