import { useState, useEffect } from 'react'

/**
 * YouTubePlayer - Embeds and plays YouTube videos inside the app
 * Supports both video URLs and video IDs
 */
const YouTubePlayer = ({ videoUrl, videoId, title, onClose, autoplay = false }) => {
  const [isLoading, setIsLoading] = useState(true)
  const [entering, setEntering] = useState(true)

  useEffect(() => {
    requestAnimationFrame(() => requestAnimationFrame(() => setEntering(false)))
  }, [])

  // Extract video ID from URL if provided
  const getVideoId = () => {
    if (videoId) return videoId

    if (videoUrl) {
      const patterns = [
        /(?:youtube\.com\/watch\?v=|youtu\.be\/)([^&\s]+)/,
        /youtube\.com\/embed\/([^&\s]+)/
      ]

      for (const pattern of patterns) {
        const match = videoUrl.match(pattern)
        if (match) return match[1]
      }
    }

    return null
  }

  const extractedVideoId = getVideoId()

  const handleClose = () => {
    setEntering(true)
    setTimeout(onClose, 200)
  }

  if (!extractedVideoId) {
    return (
      <div className="fixed inset-0 bg-navy-950/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
        <div className="bg-white rounded-2xl p-6 max-w-md shadow-xl">
          <p className="text-red-600 mb-4 text-sm">Invalid YouTube URL or video ID</p>
          <button
            onClick={onClose}
            className="px-4 py-2 bg-navy-800 text-white rounded-xl hover:bg-navy-900 text-sm font-medium transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    )
  }

  const embedUrl = `https://www.youtube.com/embed/${extractedVideoId}?${new URLSearchParams({
    autoplay: autoplay ? '1' : '0',
    modestbranding: '1',
    rel: '0',
    enablejsapi: '1'
  }).toString()}`

  return (
    <div className={`fixed inset-0 bg-black/90 z-50 flex items-center justify-center p-4 transition-opacity duration-200 ${entering ? 'opacity-0' : 'opacity-100'}`}>
      <div className={`bg-[#0a0a0a] rounded-2xl shadow-2xl w-full h-full max-w-7xl max-h-[90vh] flex flex-col overflow-hidden transition-all duration-300 ${entering ? 'scale-95 opacity-0' : 'scale-100 opacity-100'}`}>
        {/* Header */}
        <div className="flex items-center justify-between border-b border-white/10 px-5 py-3.5 bg-[#111]">
          <div className="flex-1 min-w-0 flex items-center gap-3">
            {/* Play icon */}
            <div className="w-8 h-8 rounded-lg bg-red-600 flex items-center justify-center flex-shrink-0">
              <svg className="w-4 h-4 text-white ml-0.5" fill="currentColor" viewBox="0 0 24 24">
                <path d="M8 5v14l11-7z" />
              </svg>
            </div>
            <div className="flex-1 min-w-0">
              <h2 className="text-[15px] font-semibold text-white truncate">
                {title || 'YouTube Video'}
              </h2>
              <p className="text-xs text-white/40">
                Shadow Learning Platform
              </p>
            </div>
          </div>

          <button
            onClick={handleClose}
            className="ml-4 p-2 hover:bg-white/10 rounded-xl transition-colors text-white/50 hover:text-white/80"
            title="Close video"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Video Player */}
        <div className="flex-1 relative bg-black">
          {isLoading && (
            <div className="absolute inset-0 flex items-center justify-center bg-black z-10">
              <div className="text-center">
                <div className="animate-spin rounded-full h-10 w-10 border-2 border-red-500 border-t-transparent mx-auto mb-4"></div>
                <p className="text-white/60 text-sm">Loading video...</p>
              </div>
            </div>
          )}

          <iframe
            src={embedUrl}
            className="w-full h-full border-0"
            title={title || 'YouTube video player'}
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
            allowFullScreen
            onLoad={() => setIsLoading(false)}
          />
        </div>

        {/* Footer */}
        <div className="border-t border-white/10 px-5 py-3 bg-[#111]">
          <div className="flex items-center justify-between text-xs text-white/30">
            <div className="flex items-center gap-4">
              <span className="flex items-center gap-1.5">
                <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                </svg>
                Powered by YouTube
              </span>
              <span className="flex items-center gap-1.5">
                <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 016-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0018 18a8.967 8.967 0 00-6 2.292m0-14.25v14.25" />
                </svg>
                Curated Learning Content
              </span>
            </div>
            <a
              href={videoUrl || `https://www.youtube.com/watch?v=${extractedVideoId}`}
              target="_blank"
              rel="noopener noreferrer"
              className="text-red-400 hover:text-red-300 transition-colors flex items-center gap-1"
            >
              Watch on YouTube
              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.5 6H5.25A2.25 2.25 0 003 8.25v10.5A2.25 2.25 0 005.25 21h10.5A2.25 2.25 0 0018 18.75V10.5m-10.5 6L21 3m0 0h-5.25M21 3v5.25" />
              </svg>
            </a>
          </div>
        </div>
      </div>
    </div>
  )
}

export default YouTubePlayer
