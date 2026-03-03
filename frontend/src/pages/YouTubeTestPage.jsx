import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { PlayIcon, ArrowLeftIcon } from '@heroicons/react/24/outline'
import YouTubePlayer from '../components/YouTubePlayer'
import api from '../services/api'

/**
 * YouTubeTestPage - Test page to verify YouTube integration and video playback
 */
const YouTubeTestPage = () => {
  const navigate = useNavigate()
  const [selectedVideo, setSelectedVideo] = useState(null)
  const [searchTopic, setSearchTopic] = useState('')
  const [videos, setVideos] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  // Sample curated videos for testing
  const sampleVideos = [
    {
      video_id: 'R-HLU9Fl5ug',
      title: 'Python: Data Structures - Lists, Tuples, Sets & Dictionaries',
      channel_title: 'Programming and Math Tutorials',
      view_count: 372109,
      like_count: 8625,
      like_view_ratio: 2.32,
      url: 'https://www.youtube.com/watch?v=R-HLU9Fl5ug',
      thumbnail_url: `https://img.youtube.com/vi/R-HLU9Fl5ug/hqdefault.jpg`
    },
    {
      video_id: '_t2GVaQasRY',
      title: 'Data Structures & Algorithms Tutorial in Python #1',
      channel_title: 'codebasics',
      view_count: 1242985,
      like_count: 19243,
      like_view_ratio: 1.55,
      url: 'https://www.youtube.com/watch?v=_t2GVaQasRY',
      thumbnail_url: `https://img.youtube.com/vi/_t2GVaQasRY/hqdefault.jpg`
    },
    {
      video_id: 'O9v10jQkm5c',
      title: 'Data Structures Explained for Beginners',
      channel_title: 'Sajjaad Khader',
      view_count: 651775,
      like_count: 25759,
      like_view_ratio: 3.95,
      url: 'https://www.youtube.com/watch?v=O9v10jQkm5c',
      thumbnail_url: `https://img.youtube.com/vi/O9v10jQkm5c/hqdefault.jpg`
    }
  ]

  const searchYouTubeVideos = async () => {
    if (!searchTopic.trim()) return

    setLoading(true)
    setError(null)

    try {
      const response = await api.get('/api/v1/content/youtube/videos', {
        params: {
          topic: searchTopic,
          max_results: 5,
          duration: 'medium'
        }
      })

      setVideos(response.data.videos || [])
    } catch (err) {
      console.error('Error searching YouTube:', err)
      setError(err.response?.data?.detail || err.message || 'Failed to fetch videos')
      // Fallback to sample videos if API fails
      setVideos(sampleVideos)
    } finally {
      setLoading(false)
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      searchYouTubeVideos()
    }
  }

  const formatNumber = (num) => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`
    return num.toString()
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-stone-50 to-stone-100">
      {/* Header */}
      <div className="bg-white border-b border-stone-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center gap-4">
            <button
              onClick={() => navigate('/dashboard')}
              className="p-2 hover:bg-stone-100 rounded-lg transition-colors"
            >
              <ArrowLeftIcon className="h-5 w-5 text-stone-600" />
            </button>
            <div>
              <h1 className="text-2xl font-bold text-stone-900">YouTube Integration Test</h1>
              <p className="text-sm text-stone-600">Test curated video search and playback</p>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Search Section */}
        <div className="bg-white rounded-xl shadow-sm border border-stone-200 p-6 mb-8">
          <h2 className="text-lg font-bold text-stone-900 mb-4">🔍 Search for Learning Videos</h2>

          <div className="flex gap-3">
            <input
              type="text"
              value={searchTopic}
              onChange={(e) => setSearchTopic(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="e.g., React hooks, Python data structures, Machine learning..."
              className="flex-1 px-4 py-3 border border-stone-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-navy-500"
            />
            <button
              onClick={searchYouTubeVideos}
              disabled={loading || !searchTopic.trim()}
              className="px-6 py-3 bg-red-600 hover:bg-red-700 text-white font-medium rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {loading ? (
                <>
                  <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  Searching...
                </>
              ) : (
                <>
                  <PlayIcon className="h-5 w-5" />
                  Search Videos
                </>
              )}
            </button>
          </div>

          {error && (
            <div className="mt-4 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
              <p className="text-sm text-yellow-800">
                ⚠️ {error} - Showing sample videos instead
              </p>
            </div>
          )}
        </div>

        {/* Sample Videos Section */}
        {videos.length === 0 && !loading && (
          <div className="bg-white rounded-xl shadow-sm border border-stone-200 p-6 mb-8">
            <h2 className="text-lg font-bold text-stone-900 mb-4">📺 Sample Curated Videos</h2>
            <p className="text-stone-600 mb-6">Click on any video to play it inside the app</p>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {sampleVideos.map((video) => (
                <div
                  key={video.video_id}
                  className="bg-white border border-stone-200 rounded-lg overflow-hidden hover:shadow-lg transition-shadow cursor-pointer group"
                  onClick={() => setSelectedVideo(video)}
                >
                  <div className="relative">
                    <img
                      src={video.thumbnail_url}
                      alt={video.title}
                      className="w-full aspect-video object-cover"
                    />
                    <div className="absolute inset-0 bg-black/40 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                      <PlayIcon className="h-16 w-16 text-white" />
                    </div>
                  </div>

                  <div className="p-4">
                    <h3 className="font-bold text-stone-900 mb-2 line-clamp-2">
                      {video.title}
                    </h3>
                    <p className="text-sm text-stone-600 mb-3">{video.channel_title}</p>

                    <div className="flex items-center justify-between text-xs text-stone-500">
                      <span>👁️ {formatNumber(video.view_count)} views</span>
                      <span>👍 {formatNumber(video.like_count)} likes</span>
                      <span>📊 {video.like_view_ratio}%</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Search Results */}
        {videos.length > 0 && (
          <div className="bg-white rounded-xl shadow-sm border border-stone-200 p-6">
            <h2 className="text-lg font-bold text-stone-900 mb-4">
              🎯 Found {videos.length} Videos
            </h2>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {videos.map((video) => (
                <div
                  key={video.video_id}
                  className="bg-white border border-stone-200 rounded-lg overflow-hidden hover:shadow-lg transition-shadow cursor-pointer group"
                  onClick={() => setSelectedVideo(video)}
                >
                  <div className="relative">
                    <img
                      src={video.thumbnail_url || `https://img.youtube.com/vi/${video.video_id}/hqdefault.jpg`}
                      alt={video.title}
                      className="w-full aspect-video object-cover"
                    />
                    <div className="absolute inset-0 bg-black/40 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                      <PlayIcon className="h-16 w-16 text-white" />
                    </div>
                  </div>

                  <div className="p-4">
                    <h3 className="font-bold text-stone-900 mb-2 line-clamp-2">
                      {video.title}
                    </h3>
                    <p className="text-sm text-stone-600 mb-3">{video.channel_title}</p>

                    <div className="flex items-center justify-between text-xs text-stone-500">
                      <span>👁️ {formatNumber(video.view_count)} views</span>
                      <span>👍 {formatNumber(video.like_count)} likes</span>
                      <span>📊 {video.like_view_ratio}%</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* YouTube Player Modal */}
      {selectedVideo && (
        <YouTubePlayer
          videoUrl={selectedVideo.url}
          videoId={selectedVideo.video_id}
          title={selectedVideo.title}
          onClose={() => setSelectedVideo(null)}
        />
      )}
    </div>
  )
}

export default YouTubeTestPage
