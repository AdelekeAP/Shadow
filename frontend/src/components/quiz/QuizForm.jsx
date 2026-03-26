import { useState, useRef } from 'react'
import { generateQuiz } from '../../services/api'

/* ─── Inline SVG Icons ─── */
const LightningIcon = ({ className }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8">
    <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z" />
  </svg>
)

const AcademicCapIcon = ({ className }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8">
    <path strokeLinecap="round" strokeLinejoin="round" d="M4.26 10.147a60.436 60.436 0 00-.491 6.347A48.627 48.627 0 0112 20.904a48.627 48.627 0 018.232-4.41 60.46 60.46 0 00-.491-6.347m-15.482 0a50.57 50.57 0 00-2.658-.813A59.905 59.905 0 0112 3.493a59.902 59.902 0 0110.399 5.84c-.896.248-1.783.52-2.658.814m-15.482 0A50.697 50.697 0 0112 13.489a50.702 50.702 0 017.74-3.342M6.75 15a.75.75 0 100-1.5.75.75 0 000 1.5zm0 0v-3.675A55.378 55.378 0 0112 8.443m-7.007 11.55A5.981 5.981 0 006.75 15.75v-1.5" />
  </svg>
)

const BookSearchIcon = ({ className }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8">
    <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 016-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0018 18a8.967 8.967 0 00-6 2.292m0-14.25v14.25" />
  </svg>
)

const UploadIcon = ({ className }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8">
    <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
  </svg>
)

const DocIcon = ({ className }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8">
    <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
  </svg>
)

const CloseIcon = ({ className }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
    <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
  </svg>
)

const SparklesIcon = ({ className }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8">
    <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 00-2.455 2.456z" />
  </svg>
)

/* ─── Quiz type presets ─── */
const QUIZ_TYPES = [
  {
    value: 'quick_quiz',
    label: 'Quick Quiz',
    subtitle: '8 questions, fast check',
    defaultCount: 8,
    defaultTimer: 15,
    icon: LightningIcon,
  },
  {
    value: 'exam_style',
    label: 'Exam Style',
    subtitle: '20 questions, comprehensive',
    defaultCount: 20,
    defaultTimer: 45,
    icon: AcademicCapIcon,
  },
  {
    value: 'topic_review',
    label: 'Topic Review',
    subtitle: '12 questions, focused',
    defaultCount: 12,
    defaultTimer: 20,
    icon: BookSearchIcon,
  },
]

const DIFFICULTIES = ['mixed', 'beginner', 'intermediate', 'advanced']

const DIFFICULTY_LABELS = {
  mixed: 'Mixed',
  beginner: 'Beginner',
  intermediate: 'Intermediate',
  advanced: 'Advanced',
}

export default function QuizForm({ onQuizGenerated, onCancel, studyPlanId, studyPlanTopic }) {
  const [topic, setTopic] = useState(studyPlanTopic || '')
  const [quizType, setQuizType] = useState('quick_quiz')
  const [questionCount, setQuestionCount] = useState(8)
  const [timeLimit, setTimeLimit] = useState(15)
  const [timerEnabled, setTimerEnabled] = useState(false)
  const [difficulty, setDifficulty] = useState('mixed')
  const [uploadedFile, setUploadedFile] = useState(null)
  const [generating, setGenerating] = useState(false)
  const [error, setError] = useState(null)
  const fileInputRef = useRef(null)

  const handleQuizTypeChange = (type) => {
    setQuizType(type.value)
    setQuestionCount(type.defaultCount)
    setTimeLimit(type.defaultTimer)
  }

  const handleFileChange = (e) => {
    const file = e.target.files[0]
    if (!file) return
    const ext = file.name.split('.').pop().toLowerCase()
    if (!['pdf', 'pptx', 'ppt'].includes(ext)) {
      setError('Invalid file type. Please upload PDF or PPTX files only.')
      e.target.value = ''
      return
    }
    if (file.size / (1024 * 1024) > 10) {
      setError(`File too large (${(file.size / (1024 * 1024)).toFixed(1)}MB). Maximum size is 10MB.`)
      e.target.value = ''
      return
    }
    setError(null)
    setUploadedFile(file)
  }

  const handleClearFile = () => {
    setUploadedFile(null)
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!topic.trim() && !uploadedFile) {
      setError('Please enter a topic or upload a file.')
      return
    }
    setError(null)
    setGenerating(true)
    try {
      const result = await generateQuiz({
        topic: topic.trim() || null,
        quizType,
        questionCount,
        timeLimitMinutes: timerEnabled ? timeLimit : null,
        difficultyLevel: difficulty,
        uploadedFile: uploadedFile || undefined,
        studyPlanId: studyPlanId || null,
      })
      onQuizGenerated(result)
    } catch (err) {
      console.error('Error generating quiz:', err)
      const detail = err?.detail || err?.response?.data?.detail || err?.message || ''
      if (typeof detail === 'string' && (detail.includes('429') || /rate.?limit/i.test(detail))) {
        setError('Too many requests — please wait a minute and try again.')
      } else if (typeof detail === 'string' && /quota|insufficient/i.test(detail)) {
        setError('AI quota reached for today. Please try again tomorrow.')
      } else if (typeof detail === 'string' && /timeout/i.test(detail)) {
        setError('Request timed out. Please try again.')
      } else {
        setError(typeof detail === 'string' && detail.length > 0 ? detail : 'Failed to generate quiz. Please try again.')
      }
    } finally {
      setGenerating(false)
    }
  }

  return (
    <div className="p-5 sm:p-6">
      <form onSubmit={handleSubmit} className="space-y-5">

        {/* ─── Error banner ─── */}
        {error && (
          <div className="flex items-start gap-2.5 bg-red-50 border border-red-200/60 rounded-xl px-4 py-3">
            <svg className="w-4 h-4 text-red-500 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
            </svg>
            <p className="text-[13px] text-red-700 flex-1">{error}</p>
            <button type="button" onClick={() => setError(null)} className="p-0.5 text-red-400 hover:text-red-600 transition-colors">
              <CloseIcon className="w-3.5 h-3.5" />
            </button>
          </div>
        )}

        {/* ─── Topic input ─── */}
        <div>
          <label className="block text-[12px] font-semibold text-navy-800 uppercase tracking-wider mb-2">
            Topic
            {!uploadedFile && <span className="text-red-500 ml-0.5">*</span>}
            {uploadedFile && (
              <span className="text-surface-400 normal-case tracking-normal font-normal ml-1">(optional with upload)</span>
            )}
          </label>
          <input
            type="text"
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            placeholder={uploadedFile ? 'e.g., Binary Trees (or leave blank)' : 'e.g., Data Structures, React Hooks, Linear Algebra...'}
            className="w-full bg-surface-50 border border-surface-200/80 rounded-xl px-4 py-2.5 text-[13px] text-navy-900 placeholder:text-surface-300 focus:border-navy-300 focus:ring-2 focus:ring-navy-100 focus:bg-white transition-all outline-none"
            disabled={generating}
          />
        </div>

        {/* ─── Quiz Type selector ─── */}
        <div>
          <label className="block text-[12px] font-semibold text-navy-800 uppercase tracking-wider mb-2">Quiz Type</label>
          <div className="grid grid-cols-3 gap-3">
            {QUIZ_TYPES.map((type) => {
              const Icon = type.icon
              const isSelected = quizType === type.value
              return (
                <button
                  key={type.value}
                  type="button"
                  onClick={() => handleQuizTypeChange(type)}
                  disabled={generating}
                  className={`p-4 rounded-xl border transition-all text-center ${
                    isSelected
                      ? 'bg-navy-800 border-navy-800 text-white shadow-sm'
                      : 'bg-white border-surface-200/80 text-navy-900 hover:border-navy-300/60'
                  }`}
                >
                  <div className={`mx-auto mb-2 w-9 h-9 rounded-lg flex items-center justify-center ${
                    isSelected ? 'bg-white/15' : 'bg-surface-100'
                  } transition-colors`}>
                    <Icon className={`w-5 h-5 ${isSelected ? 'text-white' : 'text-surface-400'}`} />
                  </div>
                  <p className={`text-[12px] font-semibold ${isSelected ? 'text-white' : 'text-navy-800'}`}>{type.label}</p>
                  <p className={`text-[10px] mt-0.5 ${isSelected ? 'text-white/70' : 'text-surface-400'}`}>{type.subtitle}</p>
                </button>
              )
            })}
          </div>
        </div>

        {/* ─── Question count + Timer ─── */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Question count */}
          <div>
            <label className="block text-[12px] font-semibold text-navy-800 uppercase tracking-wider mb-2">
              Number of Questions
            </label>
            <input
              type="number"
              min={5}
              max={50}
              value={questionCount}
              onChange={(e) => setQuestionCount(Math.max(5, Math.min(50, parseInt(e.target.value) || 5)))}
              className="w-full bg-surface-50 border border-surface-200/80 rounded-xl px-4 py-2.5 text-[13px] font-mono text-navy-900 focus:border-navy-300 focus:ring-2 focus:ring-navy-100 focus:bg-white transition-all outline-none"
              disabled={generating}
            />
          </div>

          {/* Timer toggle + input */}
          <div>
            <label className="block text-[12px] font-semibold text-navy-800 uppercase tracking-wider mb-2">
              Time Limit
            </label>
            <div className="flex items-center gap-3">
              {/* Toggle switch */}
              <button
                type="button"
                onClick={() => setTimerEnabled(!timerEnabled)}
                disabled={generating}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors flex-shrink-0 ${
                  timerEnabled ? 'bg-navy-800' : 'bg-surface-200'
                }`}
              >
                <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform shadow-sm ${
                  timerEnabled ? 'translate-x-6' : 'translate-x-1'
                }`} />
              </button>
              {timerEnabled ? (
                <div className="flex items-center gap-2 flex-1">
                  <input
                    type="number"
                    min={1}
                    max={180}
                    value={timeLimit}
                    onChange={(e) => setTimeLimit(Math.max(1, Math.min(180, parseInt(e.target.value) || 1)))}
                    className="w-full bg-surface-50 border border-surface-200/80 rounded-xl px-4 py-2.5 text-[13px] font-mono text-navy-900 focus:border-navy-300 focus:ring-2 focus:ring-navy-100 focus:bg-white transition-all outline-none"
                    disabled={generating}
                  />
                  <span className="text-[12px] text-surface-400 flex-shrink-0">min</span>
                </div>
              ) : (
                <span className="text-[13px] text-surface-400">No time limit</span>
              )}
            </div>
          </div>
        </div>

        {/* ─── Difficulty pills ─── */}
        <div>
          <label className="block text-[12px] font-semibold text-navy-800 uppercase tracking-wider mb-2">
            Difficulty
          </label>
          <div className="flex flex-wrap gap-2">
            {DIFFICULTIES.map((d) => (
              <button
                key={d}
                type="button"
                onClick={() => setDifficulty(d)}
                disabled={generating}
                className={`px-4 py-2 rounded-xl text-[12px] font-semibold transition-all ${
                  difficulty === d
                    ? 'bg-navy-800 text-white shadow-sm'
                    : 'bg-surface-50 border border-surface-200/80 text-navy-800 hover:border-navy-300/60'
                }`}
              >
                {DIFFICULTY_LABELS[d]}
              </button>
            ))}
          </div>
        </div>

        {/* ─── File upload drop zone ─── */}
        <div className="rounded-xl border border-dashed border-surface-200/80 bg-surface-50/50 p-4">
          <div className="flex items-center justify-between mb-2">
            <label className="text-[12px] font-semibold text-navy-800 uppercase tracking-wider flex items-center gap-1.5">
              <UploadIcon className="w-3.5 h-3.5" />
              Upload Study Material
              <span className="text-surface-400 normal-case tracking-normal font-normal">(optional)</span>
            </label>
            <span className="text-[11px] text-surface-400">PDF or PPTX &middot; Max 10MB</span>
          </div>

          {!uploadedFile ? (
            <div className="relative">
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.pptx,.ppt"
                onChange={handleFileChange}
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                disabled={generating}
              />
              <div className="bg-white border border-surface-200/80 rounded-xl p-5 text-center hover:border-navy-300/60 hover:bg-navy-800/[0.01] transition-all cursor-pointer">
                <UploadIcon className="w-6 h-6 text-surface-300 mx-auto mb-2" />
                <p className="text-[13px] font-medium text-navy-800">Click to upload or drag and drop</p>
                <p className="text-[11px] text-surface-400 mt-0.5">AI will generate questions from your materials</p>
              </div>
            </div>
          ) : (
            <div className="bg-emerald-50/50 border border-emerald-200/60 rounded-xl p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-lg bg-emerald-100 flex items-center justify-center">
                    <DocIcon className="w-4.5 h-4.5 text-emerald-600" />
                  </div>
                  <div>
                    <p className="text-[13px] font-semibold text-navy-900">{uploadedFile.name}</p>
                    <p className="text-[11px] text-surface-400">{(uploadedFile.size / (1024 * 1024)).toFixed(2)} MB</p>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={handleClearFile}
                  className="p-1.5 rounded-lg text-surface-300 hover:text-red-500 hover:bg-red-50 transition-all"
                  disabled={generating}
                >
                  <CloseIcon className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}
        </div>

        {/* ─── Attempt limit info ─── */}
        <div className="flex items-center gap-2 text-[12px] text-surface-400 bg-surface-50 rounded-lg px-3 py-2 border border-surface-200/60">
          <svg className="w-4 h-4 text-surface-300 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8">
            <path strokeLinecap="round" strokeLinejoin="round" d="M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z" />
          </svg>
          <span>Each quiz allows <span className="font-semibold text-navy-800">3 attempts</span>. Generate a new quiz to keep practicing.</span>
        </div>

        {/* ─── Generate button ─── */}
        <button
          type="submit"
          disabled={generating || (!topic.trim() && !uploadedFile)}
          className="w-full flex items-center justify-center gap-2.5 bg-navy-800 hover:bg-navy-900 disabled:bg-surface-200 disabled:cursor-not-allowed text-white px-5 py-3 rounded-xl text-[12px] font-semibold transition-all"
        >
          {generating ? (
            <>
              <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              Generating Quiz...
            </>
          ) : (
            <>
              <SparklesIcon className="w-4 h-4" />
              Generate Quiz
            </>
          )}
        </button>

        {/* ─── Cancel link ─── */}
        {onCancel && (
          <div className="text-center">
            <button
              type="button"
              onClick={onCancel}
              disabled={generating}
              className="text-[12px] font-semibold text-surface-400 hover:text-navy-800 transition-colors"
            >
              Cancel
            </button>
          </div>
        )}
      </form>
    </div>
  )
}
