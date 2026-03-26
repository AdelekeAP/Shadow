import { useState, useEffect } from 'react'
import { generateConceptDiagram } from '../../services/api'
import ConceptDiagram from './ConceptDiagram'

/* ═══════════════════════════════════════════════════════════════
   DiagramGenerator — Modal for generating AI concept diagrams
   Matches Shadow's modal, form, and overlay patterns exactly.
   ═══════════════════════════════════════════════════════════════ */

const DIAGRAM_TYPES = [
  { value: 'auto',     label: 'Auto',      icon: 'M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z', desc: 'AI picks best layout' },
  { value: 'tree',     label: 'Tree',       icon: 'M3.75 6A2.25 2.25 0 016 3.75h2.25A2.25 2.25 0 0110.5 6v2.25a2.25 2.25 0 01-2.25 2.25H6a2.25 2.25 0 01-2.25-2.25V6zM3.75 15.75A2.25 2.25 0 016 13.5h2.25a2.25 2.25 0 012.25 2.25V18a2.25 2.25 0 01-2.25 2.25H6A2.25 2.25 0 013.75 18v-2.25zM13.5 15.75a2.25 2.25 0 012.25-2.25H18a2.25 2.25 0 012.25 2.25V18A2.25 2.25 0 0118 20.25h-2.25A2.25 2.25 0 0113.5 18v-2.25z', desc: 'Hierarchical branches' },
  { value: 'flow',     label: 'Flow',       icon: 'M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z', desc: 'Step-by-step process' },
  { value: 'timeline', label: 'Timeline',   icon: 'M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z', desc: 'Sequential events' },
  { value: 'cycle',    label: 'Cycle',      icon: 'M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182', desc: 'Circular process' },
  { value: 'mindmap',  label: 'Mind Map',   icon: 'M21 12a9 9 0 11-18 0 9 9 0 0118 0z', desc: 'Radial concept map' },
]

const GENERATING_STEPS = [
  { label: 'Understanding topic', icon: 'search' },
  { label: 'Mapping concepts', icon: 'nodes' },
  { label: 'Rendering diagram', icon: 'draw' },
]

export default function DiagramGenerator({ onClose, courseCode = null, initialTopic = '' }) {
  const [topic, setTopic] = useState(initialTopic)
  const [diagramType, setDiagramType] = useState('auto')
  const [contextHint, setContextHint] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [diagram, setDiagram] = useState(null)
  const [showContext, setShowContext] = useState(false)
  const [genStep, setGenStep] = useState(0)

  // Close on Escape key
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [onClose])

  // Step cycle during generation (matches GeneratingOverlay pattern)
  useEffect(() => {
    if (!loading) return
    setGenStep(0)
    const interval = setInterval(() => setGenStep(prev => Math.min(prev + 1, 2)), 3000)
    return () => clearInterval(interval)
  }, [loading])

  const handleGenerate = async () => {
    if (!topic.trim()) return
    setLoading(true)
    setError(null)
    try {
      const result = await generateConceptDiagram({
        topic: topic.trim(), courseCode, diagramType, contextHint: contextHint.trim() || null,
      })
      setDiagram(result)
    } catch (err) {
      setError(err?.detail || err?.message || 'Failed to generate diagram. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 bg-navy-950/40 backdrop-blur-sm flex items-center justify-center p-4"
      onClick={(e) => { if (e.target === e.currentTarget) onClose() }}>
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-3xl max-h-[90vh] overflow-y-auto animate-scale-in">

        {/* ═══ Header ═══ */}
        <div className="sticky top-0 z-10 bg-white/90 backdrop-blur-xl border-b border-surface-200/80 px-6 py-4 rounded-t-2xl relative overflow-hidden">
          {/* Atmosphere orbs */}
          <div className="absolute top-0 right-12 w-32 h-32 rounded-full bg-navy-100/20 blur-3xl pointer-events-none" />
          <div className="absolute -bottom-4 left-16 w-24 h-24 rounded-full bg-amber-100/15 blur-2xl pointer-events-none" />

          <div className="flex items-center justify-between relative z-[1]">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-navy-800/[0.06] flex items-center justify-center">
                <svg className="w-5 h-5 text-navy-700" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  <circle cx="12" cy="12" r="2" fill="currentColor" opacity="0.3" />
                  <circle cx="7" cy="8" r="1.5" fill="currentColor" opacity="0.3" />
                  <circle cx="17" cy="8" r="1.5" fill="currentColor" opacity="0.3" />
                  <circle cx="7" cy="16" r="1.5" fill="currentColor" opacity="0.3" />
                  <circle cx="17" cy="16" r="1.5" fill="currentColor" opacity="0.3" />
                  <line x1="12" y1="12" x2="7" y2="8" strokeWidth="1" opacity="0.4" />
                  <line x1="12" y1="12" x2="17" y2="8" strokeWidth="1" opacity="0.4" />
                  <line x1="12" y1="12" x2="7" y2="16" strokeWidth="1" opacity="0.4" />
                  <line x1="12" y1="12" x2="17" y2="16" strokeWidth="1" opacity="0.4" />
                </svg>
              </div>
              <div>
                <h2 className="font-display text-[17px] font-bold text-navy-900">Concept Diagram</h2>
                <p className="text-[11px] text-surface-400">AI-generated visual breakdown of any topic</p>
              </div>
            </div>
            <button onClick={onClose}
              className="p-2 rounded-lg text-surface-300 hover:text-surface-500 hover:bg-surface-100 transition-all">
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* ═══ Body ═══ */}
        <div className="p-6">

          {/* ── Loading State (matches GeneratingOverlay) ── */}
          {loading ? (
            <div className="py-12 text-center animate-fade-up">
              <div className="w-16 h-16 mx-auto mb-5 relative">
                <svg className="w-16 h-16 -rotate-90" viewBox="0 0 64 64">
                  <circle cx="32" cy="32" r="28" fill="none" stroke="#e5e7ee" strokeWidth="3" />
                  <circle cx="32" cy="32" r="28" fill="none" stroke="#1e3a8a" strokeWidth="3"
                    strokeDasharray="175.93" strokeDashoffset={175.93 - (genStep + 1) / 3 * 175.93}
                    strokeLinecap="round" className="transition-all duration-700 ease-out" />
                </svg>
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="w-6 h-6 border-2 border-navy-200 border-t-navy-800 rounded-full animate-spin" />
                </div>
              </div>

              <h3 className="text-[16px] font-display font-bold text-navy-900 mb-4">Generating Diagram</h3>

              <div className="space-y-2.5 max-w-xs mx-auto">
                {GENERATING_STEPS.map((step, i) => (
                  <div key={i} className={`flex items-center gap-2.5 px-3 py-2 rounded-lg transition-all duration-500 ${
                    i === genStep ? 'bg-navy-800/[0.04] text-navy-800' :
                    i < genStep ? 'text-emerald-600' : 'text-surface-300'
                  }`}>
                    {i < genStep ? (
                      <svg className="w-4 h-4 text-emerald-500 animate-check-pop" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                      </svg>
                    ) : i === genStep ? (
                      <div className="w-4 h-4 border-2 border-navy-200 border-t-navy-700 rounded-full animate-spin" />
                    ) : (
                      <div className="w-4 h-4 rounded-full border-2 border-surface-200" />
                    )}
                    <span className="text-[13px] font-medium">{step.label}</span>
                  </div>
                ))}
              </div>
            </div>

          ) : !diagram ? (
            <>
              {/* ── Form ── */}

              {/* Topic */}
              <div className="mb-5 animate-fade-up">
                <label className="block text-[12px] font-semibold text-navy-800 mb-1.5">Topic</label>
                <input type="text" value={topic} onChange={e => setTopic(e.target.value)}
                  placeholder="e.g. Tort Law Negligence, Cell Division, Supply & Demand..."
                  className="w-full px-4 py-2.5 rounded-xl border border-surface-200/80 bg-surface-50 text-[13px] text-navy-900
                    placeholder:text-surface-300 focus:outline-none focus:border-navy-300 focus:ring-2 focus:ring-navy-100 focus:bg-white transition-all"
                  maxLength={255} autoFocus
                  onKeyDown={e => { if (e.key === 'Enter' && topic.trim()) handleGenerate() }} />
              </div>

              {/* Diagram Type */}
              <div className="mb-5 animate-fade-up-1">
                <label className="block text-[12px] font-semibold text-navy-800 mb-2">Diagram Type</label>
                <div className="grid grid-cols-3 sm:grid-cols-6 gap-2">
                  {DIAGRAM_TYPES.map(dt => (
                    <button key={dt.value} onClick={() => setDiagramType(dt.value)}
                      className={`flex flex-col items-center gap-1.5 px-2 py-3 rounded-xl text-center transition-all border ${
                        diagramType === dt.value
                          ? 'bg-navy-800 border-navy-800 text-white shadow-sm'
                          : 'bg-white border-surface-200/80 text-navy-900 hover:border-navy-300/60 hover:bg-surface-50'
                      }`}>
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                        <path d={dt.icon} />
                      </svg>
                      <span className="text-[11px] font-semibold">{dt.label}</span>
                    </button>
                  ))}
                </div>
                <p className="text-[11px] text-surface-400 mt-2">
                  {DIAGRAM_TYPES.find(dt => dt.value === diagramType)?.desc}
                </p>
              </div>

              {/* Context (collapsible) */}
              <div className="mb-6 animate-fade-up-2">
                <button onClick={() => setShowContext(!showContext)}
                  className="text-[12px] font-medium text-surface-400 hover:text-navy-600 flex items-center gap-1.5 transition-colors">
                  <svg className={`w-3.5 h-3.5 transition-transform duration-200 ${showContext ? 'rotate-90' : ''}`}
                    fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
                  </svg>
                  Add context (optional)
                </button>
                {showContext && (
                  <textarea value={contextHint} onChange={e => setContextHint(e.target.value)}
                    placeholder="e.g. 'Focus on Nigerian case law' or 'Include real-world examples'..."
                    className="mt-2 w-full px-4 py-2.5 rounded-xl border border-surface-200/80 bg-surface-50 text-[13px] text-navy-900
                      placeholder:text-surface-300 focus:outline-none focus:border-navy-300 focus:ring-2 focus:ring-navy-100 focus:bg-white transition-all resize-none"
                    rows={2} maxLength={500} />
                )}
              </div>

              {/* Error */}
              {error && (
                <div className="mb-4 bg-red-50 border border-red-200/60 rounded-xl px-4 py-3 flex items-start gap-2.5">
                  <svg className="w-4 h-4 text-red-400 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
                  </svg>
                  <span className="text-[13px] text-red-600">{error}</span>
                </div>
              )}

              {/* Generate Button */}
              <button onClick={handleGenerate} disabled={!topic.trim()}
                className="btn-glow w-full flex items-center justify-center gap-2.5 bg-gradient-to-r from-navy-800 to-navy-900
                  hover:from-navy-900 hover:to-navy-950 disabled:from-surface-200 disabled:to-surface-200
                  text-white disabled:text-surface-400 px-6 py-3 rounded-xl text-[13px] font-semibold transition-all shadow-sm animate-fade-up-3">
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z" />
                </svg>
                Generate Diagram
              </button>
            </>

          ) : (
            <>
              {/* ── Result ── */}
              <div className="animate-fade-up">
                <ConceptDiagram diagram={diagram} />
              </div>

              {/* Actions */}
              <div className="mt-5 flex items-center gap-3 animate-fade-up-1">
                <button onClick={() => { setDiagram(null); setError(null) }}
                  className="flex items-center gap-2 px-4 py-2.5 rounded-xl border border-surface-200/80 bg-white
                    text-[13px] font-semibold text-navy-700 hover:bg-surface-50 hover:border-navy-200/60 transition-all">
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182" />
                  </svg>
                  New Diagram
                </button>
                <button onClick={onClose}
                  className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-navy-800 hover:bg-navy-900
                    text-white text-[13px] font-semibold transition-all shadow-sm">
                  Done
                </button>
                {diagram.cached && (
                  <span className="text-[11px] text-surface-300 ml-auto flex items-center gap-1">
                    <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z" />
                    </svg>
                    Cached
                  </span>
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
