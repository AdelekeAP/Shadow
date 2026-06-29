import { useState, useCallback, useMemo } from 'react'
import { Document, Page, pdfjs } from 'react-pdf'
// Text + annotation layers are disabled on <Page> (renderTextLayer/renderAnnotationLayer=false)
// to prevent the text-layer doubling bug, so their CSS is intentionally NOT imported.

// Configure pdf.js worker
pdfjs.GlobalWorkerOptions.workerSrc = new URL(
  'pdfjs-dist/build/pdf.worker.min.mjs',
  import.meta.url
).toString()

/* ─── Icons ─── */
const ChevronLeft = ({ className }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5">
    <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 19.5L8.25 12l7.5-7.5" />
  </svg>
)
const ChevronRight = ({ className }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5">
    <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
  </svg>
)
const ZoomIn = ({ className }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8">
    <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607zM10.5 7.5v6m3-3h-6" />
  </svg>
)
const ZoomOut = ({ className }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8">
    <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607zM13.5 10.5h-6" />
  </svg>
)
const DocumentIcon = ({ className }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8">
    <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
  </svg>
)

/**
 * SlideRangeViewer — renders specific PDF pages inline using react-pdf.
 * Elevated Shadow design system with glass toolbar, navy atmosphere, and smooth transitions.
 */
export default function SlideRangeViewer({ documentUrl, pageRange, onClose }) {
  const [numPages, setNumPages] = useState(null)
  const [loadError, setLoadError] = useState(null)
  const [scale, setScale] = useState(1.0)

  // Parse page range into [start, end] (1-indexed)
  const { startPage, endPage } = useMemo(() => {
    if (!pageRange) return { startPage: 1, endPage: 1 }
    const match = String(pageRange).match(/^(\d+)\s*[-–]?\s*(\d*)$/)
    if (!match) return { startPage: 1, endPage: 1 }
    const s = parseInt(match[1], 10)
    const e = match[2] ? parseInt(match[2], 10) : s
    return { startPage: Math.max(1, s), endPage: Math.max(s, e) }
  }, [pageRange])

  const [currentPage, setCurrentPage] = useState(startPage)

  const clampedEnd = numPages ? Math.min(endPage, numPages) : endPage
  const clampedStart = numPages ? Math.min(startPage, numPages) : startPage
  const totalPagesInRange = clampedEnd - clampedStart + 1
  const progressPercent = totalPagesInRange > 1
    ? ((currentPage - clampedStart) / (totalPagesInRange - 1)) * 100
    : 100

  const onDocumentLoadSuccess = useCallback(({ numPages: total }) => {
    setNumPages(total)
    setCurrentPage(prev => Math.max(clampedStart, Math.min(prev, Math.min(endPage, total))))
  }, [clampedStart, endPage])

  const onDocumentLoadError = useCallback((error) => {
    console.error('PDF load error:', error)
    setLoadError('Failed to load document. The file may not be a valid PDF.')
  }, [])

  const goPrev = () => setCurrentPage(p => Math.max(clampedStart, p - 1))
  const goNext = () => setCurrentPage(p => Math.min(clampedEnd, p + 1))
  const zoomIn = () => setScale(s => Math.min(2.0, +(s + 0.25).toFixed(2)))
  const zoomOut = () => setScale(s => Math.max(0.5, +(s - 0.25).toFixed(2)))

  const fileOptions = useMemo(() => ({
    url: documentUrl,
    httpHeaders: {
      Authorization: `Bearer ${localStorage.getItem('access_token')}`,
    },
  }), [documentUrl])

  if (!documentUrl) {
    return (
      <div className="bg-surface-50 border border-surface-200/60 rounded-xl p-5 text-center">
        <DocumentIcon className="w-6 h-6 text-surface-300 mx-auto mb-2" />
        <p className="text-[12px] text-surface-400 font-medium">No document available to view.</p>
      </div>
    )
  }

  return (
    <div className="relative rounded-2xl overflow-hidden border border-navy-200/50 bg-gradient-to-b from-navy-50/40 to-surface-50/60 shadow-sm animate-fade-up-0">
      {/* ─── Atmospheric Background Orb ─── */}
      <div
        className="absolute top-0 right-0 w-40 h-40 pointer-events-none opacity-40"
        style={{
          background: 'radial-gradient(ellipse at 100% 0%, rgba(30, 58, 138, 0.08), transparent 70%)',
        }}
      />

      {/* ─── Glass Toolbar ─── */}
      <div
        className="relative flex items-center justify-between px-4 py-2.5 border-b border-navy-200/40"
        style={{
          background: 'rgba(240, 244, 255, 0.72)',
          backdropFilter: 'blur(12px) saturate(160%)',
        }}
      >
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-lg bg-navy-800 flex items-center justify-center shadow-sm">
            <DocumentIcon className="w-3.5 h-3.5 text-white" />
          </div>
          <div>
            <span className="text-[12px] font-bold text-navy-900 tracking-tight">
              Pages {pageRange}
            </span>
            {numPages && (
              <span className="ml-2 text-[10px] text-surface-400 font-medium">
                {currentPage} of {numPages}
              </span>
            )}
          </div>
        </div>

        <div className="flex items-center gap-0.5">
          {/* Zoom */}
          <button
            onClick={zoomOut}
            disabled={scale <= 0.5}
            className="p-1.5 rounded-lg hover:bg-navy-100/80 disabled:opacity-25 transition-all active:scale-95"
            title="Zoom out"
          >
            <ZoomOut className="w-4 h-4 text-navy-600" />
          </button>
          <span className="text-[10px] font-mono text-navy-500 min-w-[3.5ch] text-center tabular-nums font-semibold">
            {Math.round(scale * 100)}%
          </span>
          <button
            onClick={zoomIn}
            disabled={scale >= 2.0}
            className="p-1.5 rounded-lg hover:bg-navy-100/80 disabled:opacity-25 transition-all active:scale-95"
            title="Zoom in"
          >
            <ZoomIn className="w-4 h-4 text-navy-600" />
          </button>

          <div className="w-px h-5 bg-navy-200/50 mx-1.5" />

          {/* Page Nav */}
          <button
            onClick={goPrev}
            disabled={currentPage <= clampedStart}
            className="p-1.5 rounded-lg hover:bg-navy-100/80 disabled:opacity-25 transition-all active:scale-95"
            title="Previous page"
          >
            <ChevronLeft className="w-4 h-4 text-navy-700" />
          </button>
          <button
            onClick={goNext}
            disabled={currentPage >= clampedEnd}
            className="p-1.5 rounded-lg hover:bg-navy-100/80 disabled:opacity-25 transition-all active:scale-95"
            title="Next page"
          >
            <ChevronRight className="w-4 h-4 text-navy-700" />
          </button>

          <div className="w-px h-5 bg-navy-200/50 mx-1.5" />

          {/* Close */}
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg hover:bg-red-50 active:bg-red-100 transition-all group"
            title="Close viewer"
          >
            <svg className="w-4 h-4 text-surface-400 group-hover:text-red-500 transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>

      {/* ─── Progress Bar ─── */}
      <div className="h-[2px] bg-navy-100/60">
        <div
          className="h-full bg-gradient-to-r from-navy-500 to-emerald-500 rounded-full transition-all duration-300 ease-out"
          style={{ width: `${progressPercent}%` }}
        />
      </div>

      {/* ─── PDF Render Area ─── */}
      <div
        className="relative flex justify-center overflow-auto p-5"
        style={{
          maxHeight: '520px',
          background: 'linear-gradient(135deg, rgba(241, 243, 246, 0.6) 0%, rgba(248, 249, 251, 0.8) 100%)',
        }}
      >
        {loadError ? (
          <div className="text-center py-10 animate-fade-up-0">
            <div className="w-12 h-12 rounded-2xl bg-red-50 border border-red-200/60 flex items-center justify-center mx-auto mb-3">
              <svg className="w-6 h-6 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
              </svg>
            </div>
            <p className="text-[13px] text-red-600 font-semibold mb-1">Could not load slides</p>
            <p className="text-[11px] text-surface-400 mb-3">{loadError}</p>
            <button
              onClick={onClose}
              className="text-[12px] text-navy-600 hover:text-navy-800 font-semibold transition-colors"
            >
              Close viewer
            </button>
          </div>
        ) : (
          <Document
            file={fileOptions}
            onLoadSuccess={onDocumentLoadSuccess}
            onLoadError={onDocumentLoadError}
            loading={
              <div className="flex flex-col items-center gap-3 py-16 animate-fade-up-0">
                <div className="w-10 h-10 rounded-xl bg-navy-50 border border-navy-200/60 flex items-center justify-center">
                  <div className="w-5 h-5 border-2 border-navy-300 border-t-navy-600 rounded-full animate-spin" />
                </div>
                <div className="text-center">
                  <p className="text-[12px] text-navy-700 font-semibold">Loading slides</p>
                  <p className="text-[10px] text-surface-400 mt-0.5">Pages {pageRange}</p>
                </div>
              </div>
            }
          >
            <div className="transition-all duration-200" key={currentPage}>
              <Page
                pageNumber={currentPage}
                scale={scale}
                /* Render the slide as an image-only canvas. The selectable pdf.js
                   text layer was inheriting the app's navy text color (its
                   `color: transparent` rule was being overridden), painting a
                   second visible copy of the text over the canvas — the doubling
                   bug. We don't need text selection in the viewer, so disabling
                   both overlays makes the doubling impossible. */
                renderTextLayer={false}
                renderAnnotationLayer={false}
                loading={
                  <div className="flex items-center gap-2 py-12">
                    <div className="w-4 h-4 border-2 border-navy-300 border-t-navy-600 rounded-full animate-spin" />
                    <span className="text-[11px] text-navy-400 font-medium">Rendering page {currentPage}...</span>
                  </div>
                }
                className="shadow-lg rounded-lg"
              />
            </div>
          </Document>
        )}
      </div>

      {/* ─── Page Navigation Dots ─── */}
      {totalPagesInRange > 1 && totalPagesInRange <= 20 && (
        <div
          className="flex items-center justify-center gap-1.5 py-2.5 border-t border-navy-200/30"
          style={{
            background: 'rgba(240, 244, 255, 0.5)',
            backdropFilter: 'blur(8px)',
          }}
        >
          {Array.from({ length: totalPagesInRange }, (_, i) => {
            const pageNum = clampedStart + i
            const isCurrent = pageNum === currentPage
            return (
              <button
                key={pageNum}
                onClick={() => setCurrentPage(pageNum)}
                className={`rounded-full transition-all duration-200 ${
                  isCurrent
                    ? 'w-6 h-2 bg-gradient-to-r from-navy-600 to-emerald-500'
                    : 'w-2 h-2 bg-navy-300/40 hover:bg-navy-400/60 hover:scale-110'
                }`}
                title={`Page ${pageNum}`}
              />
            )
          })}
        </div>
      )}
    </div>
  )
}
