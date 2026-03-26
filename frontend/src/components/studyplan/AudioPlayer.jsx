import { useState, useRef } from 'react'
import { generateAudioSummary, API_BASE_URL } from '../../services/api'
import { getNotebookLMLink } from './studyPlanHelpers.jsx'

export default function AudioPlayer({ planId, resource, topic, activityDescription, pageRange, isPrimary = true }) {
  const hasExistingAudio = !!(resource?.audio_url)
  const [state, setState] = useState(hasExistingAudio ? 'ready' : 'idle') // idle | loading | ready | error
  const [audioUrl, setAudioUrl] = useState(resource?.audio_url || null)
  const [script, setScript] = useState(null)
  const [showScript, setShowScript] = useState(false)
  const [durationEstimate, setDurationEstimate] = useState(null)
  const audioRef = useRef(null)

  const canGenerateAudio = resource && resource.id

  const [errorMsg, setErrorMsg] = useState(null)
  const [audioPageRange, setAudioPageRange] = useState(null)

  const handleGenerate = async () => {
    if (!canGenerateAudio || state === 'loading') return

    // If already have audio, just play
    if (audioUrl && state === 'ready') {
      if (audioRef.current) {
        audioRef.current.paused ? audioRef.current.play() : audioRef.current.pause()
      }
      return
    }

    setState('loading')
    setErrorMsg(null)
    try {
      const result = await generateAudioSummary(planId, resource.id, activityDescription, pageRange, isPrimary)

      // Script-only fallback: TTS failed but script was generated
      if (result.script_only && !result.audio_url) {
        setScript(result.script)
        setShowScript(true)
        setDurationEstimate(result.duration_estimate)
        setErrorMsg('Audio unavailable — read the script below instead')
        setState('error')
        return
      }

      setAudioUrl(result.audio_url)
      setScript(result.script)
      setDurationEstimate(result.duration_estimate)
      setAudioPageRange(result.page_range || pageRange)
      setState('ready')
    } catch (err) {
      console.error('Audio generation failed:', err)
      const detail = err?.detail || err?.response?.data?.detail || ''
      if (detail.includes('insufficient_quota') || detail.includes('quota')) {
        setErrorMsg('API quota exceeded. Please try again tomorrow or contact your administrator.')
      } else if (detail.includes('429') || detail.includes('rate limit')) {
        setErrorMsg('Too many requests. Please wait a minute and try again.')
      } else if (detail.includes('ElevenLabs') || detail.includes('TTS')) {
        setErrorMsg('Voice synthesis unavailable. Try "Show Script" to read instead.')
      } else if (detail.includes('not configured') || detail.includes('503')) {
        setErrorMsg('Audio service not configured. Use "Show Script" or NotebookLM instead.')
      } else {
        setErrorMsg('Audio generation failed. Please try again in a few minutes.')
      }
      setState('error')
    }
  }

  const fullAudioUrl = audioUrl ? `${API_BASE_URL}${audioUrl}` : null

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center gap-2 flex-wrap">
        {/* Generate/Play audio button — only if we have a real resource */}
        {canGenerateAudio && (
          <button
            onClick={handleGenerate}
            disabled={state === 'loading'}
            className={`inline-flex items-center gap-1.5 px-2.5 py-1 text-[11px] font-semibold rounded-lg transition-all ${
              state === 'loading'
                ? 'bg-navy-700 text-white/70 cursor-wait'
                : state === 'error'
                  ? 'bg-red-100 text-red-600 border border-red-200/60 hover:bg-red-50'
                  : state === 'ready'
                    ? 'bg-emerald-600 hover:bg-emerald-700 text-white'
                    : 'bg-surface-100 hover:bg-surface-200 text-navy-700 border border-surface-200/60'
            }`}
          >
            {state === 'loading' ? (
              <>
                <div className="w-3 h-3 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Generating...
              </>
            ) : state === 'error' ? (
              <>
                <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
                </svg>
                Retry Audio
              </>
            ) : (
              <>
                <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M19.114 5.636a9 9 0 010 12.728M16.463 8.288a5.25 5.25 0 010 7.424M6.75 8.25l4.72-4.72a.75.75 0 011.28.53v15.88a.75.75 0 01-1.28.53l-4.72-4.72H4.51c-.88 0-1.704-.507-1.938-1.354A9.01 9.01 0 012.25 12c0-.83.112-1.633.322-2.396C2.806 8.756 3.63 8.25 4.51 8.25H6.75z" />
                </svg>
                {state === 'ready' ? 'Play Podcast' : 'Generate Podcast'}
              </>
            )}
          </button>
        )}

        {durationEstimate && state === 'ready' && (
          <span className="text-[10px] text-surface-400 font-medium">{durationEstimate}</span>
        )}

        {audioPageRange && state === 'ready' && (
          <span className="inline-flex items-center gap-1 text-[10px] text-navy-600 font-semibold bg-gradient-to-r from-navy-50 to-surface-50 border border-navy-200/40 px-2 py-0.5 rounded-lg shadow-sm">
            <svg className="w-2.5 h-2.5 text-navy-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
              <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
            </svg>
            Pages {audioPageRange}
          </span>
        )}

        {/* Show Script toggle — available when ready or when script-only fallback */}
        {script && (state === 'ready' || state === 'error') && (
          <button
            onClick={() => setShowScript(!showScript)}
            className="text-[11px] px-2 py-1 bg-surface-100 hover:bg-surface-200 text-navy-700 rounded-lg font-semibold transition-all"
          >
            {showScript ? 'Hide Script' : 'Show Script'}
          </button>
        )}

        {/* Error message */}
        {errorMsg && state === 'error' && (
          <span className="text-[10px] text-red-500 font-medium">{errorMsg}</span>
        )}

        {/* NotebookLM fallback — only when no in-app audio is possible */}
        {!canGenerateAudio && (
          <a
            href={getNotebookLMLink(topic, activityDescription)}
            target="_blank"
            rel="noopener noreferrer"
            className="text-[10px] text-surface-400 hover:text-navy-600 transition-colors flex items-center gap-1"
          >
            NotebookLM
            <svg className="w-2.5 h-2.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
              <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 6H5.25A2.25 2.25 0 003 8.25v10.5A2.25 2.25 0 005.25 21h10.5A2.25 2.25 0 0018 18.75V10.5m-10.5 6L21 3m0 0h-5.25M21 3v5.25" />
            </svg>
          </a>
        )}
      </div>

      {/* HTML5 Audio Player */}
      {fullAudioUrl && state === 'ready' && (
        <audio
          ref={audioRef}
          controls
          src={fullAudioUrl}
          className="w-full h-8 mt-1"
          style={{ maxWidth: '100%' }}
        >
          Your browser does not support the audio element.
        </audio>
      )}

      {/* Script display — shown when toggled on (ready state or script-only fallback) */}
      {showScript && script && (
        <div className="bg-surface-50/50 border border-surface-200/60 rounded-lg p-3 mt-1">
          <h6 className="text-[11px] font-bold text-navy-800 mb-1.5">Audio Script</h6>
          <p className="text-[12px] text-surface-400 leading-relaxed whitespace-pre-wrap">{script}</p>
        </div>
      )}
    </div>
  )
}
