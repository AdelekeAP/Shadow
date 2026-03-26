import { useEffect, useRef, useState, useCallback } from 'react'
import { EditorView, basicSetup } from 'codemirror'
import { EditorState, Compartment } from '@codemirror/state'
import { oneDark } from '@codemirror/theme-one-dark'
import { javascript } from '@codemirror/lang-javascript'
import { python } from '@codemirror/lang-python'
import { java } from '@codemirror/lang-java'
import { cpp } from '@codemirror/lang-cpp'

/* ─── Language Config ─── */
// Extensible language registry — add new languages here, everything else adapts
const SUPPORTED_LANGUAGES = {
  python:     { label: 'Python',      ext: () => python(),     bg: 'bg-sky-500/20',    text: 'text-sky-300',    dot: 'bg-sky-400' },
  javascript: { label: 'JavaScript',  ext: () => javascript(), bg: 'bg-amber-500/20',  text: 'text-amber-300',  dot: 'bg-amber-400' },
  java:       { label: 'Java',        ext: () => java(),       bg: 'bg-orange-500/20', text: 'text-orange-300', dot: 'bg-orange-400' },
  cpp:        { label: 'C++',         ext: () => cpp(),        bg: 'bg-blue-500/20',   text: 'text-blue-300',   dot: 'bg-blue-400' },
  c:          { label: 'C',           ext: () => cpp(),        bg: 'bg-blue-500/20',   text: 'text-blue-300',   dot: 'bg-blue-400' },
  sql:        { label: 'SQL',         ext: () => javascript(), bg: 'bg-emerald-500/20',text: 'text-emerald-300',dot: 'bg-emerald-400' },
  r:          { label: 'R',           ext: () => javascript(), bg: 'bg-indigo-500/20', text: 'text-indigo-300', dot: 'bg-indigo-400' },
}

// Fallback keyword detection — only used when backend doesn't provide language
const FALLBACK_KEYWORDS = {
  python: ['python', 'django', 'flask', 'pandas', 'numpy', 'pytorch', 'tensorflow',
           'machine learning', 'deep learning', 'data science', 'scikit', 'sklearn',
           'neural network', 'nlp', 'artificial intelligence', 'ai '],
  javascript: ['javascript', 'react', 'node', 'express', 'vue', 'angular', 'typescript'],
  java: ['java ', 'spring', 'hibernate', 'maven', 'jvm'],
  cpp: ['c++', 'cpp', 'pointer', 'malloc', 'iostream'],
}

function detectLanguageFallback(topic) {
  if (!topic) return 'python'
  const lower = topic.toLowerCase()
  for (const [lang, keywords] of Object.entries(FALLBACK_KEYWORDS)) {
    if (keywords.some(kw => lower.includes(kw))) return lang
  }
  return 'python'
}

/**
 * Resolve language: backend-provided > keyword fallback
 * Normalizes aliases (e.g., "c++" -> "cpp")
 */
function resolveLanguage(backendLang, topic) {
  if (backendLang) {
    const normalized = backendLang.toLowerCase().replace('+', 'p').replace('#', 'sharp')
    if (SUPPORTED_LANGUAGES[normalized]) return normalized
    // Try partial match (e.g., "python3" -> "python")
    for (const key of Object.keys(SUPPORTED_LANGUAGES)) {
      if (normalized.startsWith(key) || key.startsWith(normalized)) return key
    }
  }
  return detectLanguageFallback(topic)
}

function getLangConfig(lang) {
  return SUPPORTED_LANGUAGES[lang] || SUPPORTED_LANGUAGES.python
}

/* ─── Starter Templates ─── */
function getStarterCode(lang, exerciseTitle) {
  switch (lang) {
    case 'python':
      return `# ${exerciseTitle || 'Your solution here'}\n\ndef solution():\n    # Write your code here\n    pass\n\n# Test your solution\nsolution()\n`
    case 'java':
      return `// ${exerciseTitle || 'Your solution here'}\n\npublic class Solution {\n    public static void main(String[] args) {\n        // Write your code here\n    }\n}\n`
    case 'cpp':
      return `// ${exerciseTitle || 'Your solution here'}\n\n#include <iostream>\nusing namespace std;\n\nint main() {\n    // Write your code here\n    \n    return 0;\n}\n`
    case 'javascript':
    default:
      return `// ${exerciseTitle || 'Your solution here'}\n\nfunction solution() {\n  // Write your code here\n}\n\n// Test your solution\nsolution()\n`
  }
}

/**
 * CodeEditor — Embedded CodeMirror 6 editor for kinesthetic code exercises.
 * Elevated Shadow design: navy-dark theme, glass toolbar, animated feedback, glow button.
 */
export default function CodeEditor({ topic, exerciseTitle, onCheckCode, initialCode, language: backendLanguage }) {
  const editorRef = useRef(null)
  const viewRef = useRef(null)
  const [checking, setChecking] = useState(false)
  const [feedback, setFeedback] = useState(null)

  // Backend-provided language takes priority, keyword detection is fallback
  const lang = resolveLanguage(backendLanguage, topic)
  const langConfig = getLangConfig(lang)

  const langCompartment = useRef(new Compartment())

  // Initialize CodeMirror once
  useEffect(() => {
    if (!editorRef.current) return

    const startDoc = initialCode || getStarterCode(lang, exerciseTitle)

    const state = EditorState.create({
      doc: startDoc,
      extensions: [
        basicSetup,
        langCompartment.current.of(langConfig.ext()),
        oneDark,
        EditorView.theme({
          '&': { fontSize: '13px' },
          '.cm-content': {
            fontFamily: '"JetBrains Mono", "Fira Code", "Cascadia Code", monospace',
            padding: '12px 0',
            caretColor: '#a78bfa',
          },
          '.cm-gutters': {
            borderRight: '1px solid rgba(99, 102, 241, 0.1)',
            background: '#141422',
          },
          '.cm-scroller': { overflow: 'auto', maxHeight: '320px' },
          '.cm-activeLine': { background: 'rgba(99, 102, 241, 0.06)' },
          '.cm-activeLineGutter': { background: 'rgba(99, 102, 241, 0.06)' },
          '&.cm-focused': { outline: 'none' },
          '.cm-cursor': { borderLeftColor: '#a78bfa' },
          '.cm-selectionBackground': { background: 'rgba(99, 102, 241, 0.2) !important' },
        }),
      ],
    })

    const view = new EditorView({ state, parent: editorRef.current })
    viewRef.current = view
    return () => view.destroy()
  }, []) // init once — language changes handled below

  // Reconfigure language without destroying the editor (preserves user code)
  useEffect(() => {
    if (!viewRef.current) return
    viewRef.current.dispatch({
      effects: langCompartment.current.reconfigure(langConfig.ext()),
    })
  }, [lang])

  const getCurrentCode = useCallback(() => {
    return viewRef.current?.state.doc.toString() || ''
  }, [])

  const handleCheck = async () => {
    if (!onCheckCode || checking) return
    const code = getCurrentCode()
    if (!code.trim()) return

    setChecking(true)
    setFeedback(null)
    try {
      const result = await onCheckCode(code)
      setFeedback(result)
    } catch {
      setFeedback({
        correct: null,
        feedback: 'Could not validate code. Check your logic manually.',
        hint: null,
      })
    } finally {
      setChecking(false)
    }
  }

  return (
    <div className="rounded-xl overflow-hidden shadow-lg animate-fade-up-0" style={{ background: '#141422' }}>
      {/* ─── Glass Toolbar ─── */}
      <div
        className="flex items-center justify-between px-4 py-2.5"
        style={{
          background: 'rgba(20, 20, 34, 0.9)',
          backdropFilter: 'blur(12px)',
          borderBottom: '1px solid rgba(99, 102, 241, 0.12)',
        }}
      >
        <div className="flex items-center gap-2.5">
          {/* Terminal dots */}
          <div className="flex items-center gap-1.5">
            <div className="w-[10px] h-[10px] rounded-full bg-red-400/70" />
            <div className="w-[10px] h-[10px] rounded-full bg-amber-400/70" />
            <div className="w-[10px] h-[10px] rounded-full bg-emerald-400/70" />
          </div>

          <div className="w-px h-4 bg-slate-700/50 mx-0.5" />

          {/* Code editor label */}
          <svg className="w-3.5 h-3.5 text-violet-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8">
            <path strokeLinecap="round" strokeLinejoin="round" d="M17.25 6.75L22.5 12l-5.25 5.25m-10.5 0L1.5 12l5.25-5.25m7.5-3l-4.5 16.5" />
          </svg>
          <span className="text-[11px] font-semibold text-slate-300/90 tracking-wide">CODE EDITOR</span>

          {/* Language badge */}
          <span className={`flex items-center gap-1 text-[10px] font-mono font-semibold px-2 py-0.5 rounded-full ${langConfig.bg} ${langConfig.text}`}>
            <span className={`w-1.5 h-1.5 rounded-full ${langConfig.dot}`} />
            {langConfig.label}
          </span>
        </div>

        {/* Check button with glow effect */}
        <div className="relative">
          <button
            onClick={handleCheck}
            disabled={checking}
            className={`relative flex items-center gap-1.5 px-4 py-1.5 rounded-lg text-[11px] font-bold transition-all ${
              checking
                ? 'bg-violet-800/30 text-violet-300/50 cursor-wait'
                : 'bg-gradient-to-r from-violet-600 to-violet-500 hover:from-violet-500 hover:to-violet-400 text-white shadow-md shadow-violet-900/30 hover:shadow-violet-800/40 active:scale-[0.97]'
            }`}
          >
            {checking ? (
              <>
                <div className="w-3 h-3 border-2 border-violet-300/20 border-t-violet-300 rounded-full animate-spin" />
                Checking...
              </>
            ) : (
              <>
                <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M5.25 5.653c0-.856.917-1.398 1.667-.986l11.54 6.348a1.125 1.125 0 010 1.971l-11.54 6.347a1.125 1.125 0 01-1.667-.985V5.653z" />
                </svg>
                Check My Code
              </>
            )}
          </button>
        </div>
      </div>

      {/* ─── Editor Mount ─── */}
      <div ref={editorRef} />

      {/* ─── Feedback Panel ─── */}
      {feedback && (
        <div
          className={`px-4 py-3 text-[12px] animate-fade-up-0 ${
            feedback.correct === true
              ? 'bg-emerald-500/[0.08]'
              : feedback.correct === false
                ? 'bg-red-500/[0.08]'
                : 'bg-slate-500/[0.06]'
          }`}
          style={{
            borderTop: `1px solid ${
              feedback.correct === true ? 'rgba(52, 211, 153, 0.2)'
              : feedback.correct === false ? 'rgba(248, 113, 113, 0.2)'
              : 'rgba(148, 163, 184, 0.15)'
            }`,
          }}
        >
          <div className="flex items-start gap-2.5">
            {/* Result icon */}
            {feedback.correct === true && (
              <div className="w-6 h-6 rounded-lg bg-emerald-500/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                <svg className="w-3.5 h-3.5 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                </svg>
              </div>
            )}
            {feedback.correct === false && (
              <div className="w-6 h-6 rounded-lg bg-red-500/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                <svg className="w-3.5 h-3.5 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </div>
            )}
            {feedback.correct === null && (
              <div className="w-6 h-6 rounded-lg bg-slate-500/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                <svg className="w-3.5 h-3.5 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
                </svg>
              </div>
            )}

            <div className="flex-1">
              <p className={`font-semibold leading-relaxed ${
                feedback.correct === true ? 'text-emerald-300'
                : feedback.correct === false ? 'text-red-300'
                : 'text-slate-300'
              }`}>
                {feedback.feedback}
              </p>
              {feedback.hint && (
                <p className="mt-1.5 text-[11px] text-slate-400/80 flex items-start gap-1.5">
                  <svg className="w-3 h-3 text-amber-400/80 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 18v-5.25m0 0a6.01 6.01 0 001.5-.189m-1.5.189a6.01 6.01 0 01-1.5-.189m3.75 7.478a12.06 12.06 0 01-4.5 0m3.75 2.383a14.406 14.406 0 01-3 0M14.25 18v-.192c0-.983.658-1.823 1.508-2.316a7.5 7.5 0 10-7.517 0c.85.493 1.509 1.333 1.509 2.316V18" />
                  </svg>
                  {feedback.hint}
                </p>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
