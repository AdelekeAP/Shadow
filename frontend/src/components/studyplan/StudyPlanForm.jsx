import { useState, useEffect, useRef } from 'react'
import { getEnrolledCourses, browseLibrary } from '../../services/api'
import { useSmartStudy } from '../../contexts/SmartStudyContext'
import GeneratingOverlay from '../GeneratingOverlay'

/* ─── SVG Icons ─── */
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
const SearchIcon = ({ className }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8">
    <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
  </svg>
)

/* ─── Learning style config ─── */
const STYLES = [
  { value: 'auto', label: 'Auto', desc: 'AI decides', icon: (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8">
      <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z" />
    </svg>
  )},
  { value: 'visual', label: 'Visual', desc: 'Diagrams & videos', icon: (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8">
      <path strokeLinecap="round" strokeLinejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z" />
      <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
    </svg>
  )},
  { value: 'audio', label: 'Audio', desc: 'Podcast summaries', icon: (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8">
      <path strokeLinecap="round" strokeLinejoin="round" d="M19.114 5.636a9 9 0 010 12.728M16.463 8.288a5.25 5.25 0 010 7.424M6.75 8.25l4.72-4.72a.75.75 0 011.28.53v15.88a.75.75 0 01-1.28.53l-4.72-4.72H4.51c-.88 0-1.704-.507-1.938-1.354A9.01 9.01 0 012.25 12c0-.83.112-1.633.322-2.396C2.806 8.756 3.63 8.25 4.51 8.25H6.75z" />
    </svg>
  )},
  { value: 'reading', label: 'Reading', desc: 'Articles & docs', icon: (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8">
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 016-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0018 18a8.967 8.967 0 00-6 2.292m0-14.25v14.25" />
    </svg>
  )},
  { value: 'kinesthetic', label: 'Hands-on', desc: 'Practice & code', icon: (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8">
      <path strokeLinecap="round" strokeLinejoin="round" d="M17.25 6.75L22.5 12l-5.25 5.25m-10.5 0L1.5 12l5.25-5.25m7.5-3l-4.5 16.5" />
    </svg>
  )},
]

export default function StudyPlanForm({ onPlanGenerated, onCancel }) {
  const { generating, startGeneration } = useSmartStudy()
  const fileInputRef = useRef(null)
  const [topic, setTopic] = useState('')
  const [duration, setDuration] = useState('auto')
  const [learningStyle, setLearningStyle] = useState('auto')
  const [uploadedFile, setUploadedFile] = useState(null)
  const [isSchoolMaterial, setIsSchoolMaterial] = useState(false)
  const [selectedCourse, setSelectedCourse] = useState('')
  const [weekNumber, setWeekNumber] = useState('')
  const [enrolledCourses, setEnrolledCourses] = useState([])
  const [showLibraryBrowser, setShowLibraryBrowser] = useState(false)
  const [selectedLibraryDoc, setSelectedLibraryDoc] = useState(null)
  const [libraryDocuments, setLibraryDocuments] = useState([])
  const [styleWarning, setStyleWarning] = useState(null)
  const [validationError, setValidationError] = useState(null)

  useEffect(() => { loadEnrolledCourses() }, [])

  const loadEnrolledCourses = async () => {
    try { setEnrolledCourses(await getEnrolledCourses(true)) }
    catch (err) { console.error('Error loading courses:', err) }
  }

  const loadLibraryDocuments = async (courseId = null) => {
    try { const res = await browseLibrary(courseId ? { courseId } : {}); setLibraryDocuments(res.documents || []) }
    catch (err) { console.error('Error loading library:', err) }
  }

  const handleGeneratePlan = async (e) => {
    e.preventDefault()
    if (!topic.trim() && !uploadedFile && !selectedLibraryDoc) {
      setValidationError('Please enter what you want to learn, upload a file, or select from library')
      return
    }
    if (uploadedFile && !selectedCourse) {
      setValidationError('Please select a course so your slides can be saved and opened later')
      return
    }
    setValidationError(null)
    // Delegate to context — generation persists across route navigation
    startGeneration({
      topic: topic.trim() || selectedLibraryDoc?.topic || null,
      durationDays: duration === 'auto' ? null : parseInt(duration),
      difficultyLevel: 'auto',
      learningStyle: learningStyle === 'auto' ? null : learningStyle,
      triggerType: 'student_request',
      uploadedFile,
      libraryDocumentId: selectedLibraryDoc?.id || null,
      courseId: (uploadedFile || isSchoolMaterial) ? selectedCourse : (selectedLibraryDoc?.course_id || null),
      isSchoolMaterial,
      weekNumber: isSchoolMaterial && weekNumber ? parseInt(weekNumber) : null,
    })
    onPlanGenerated()
  }

  const handleFileChange = (e) => {
    const file = e.target.files[0]
    if (!file) return
    const ext = file.name.split('.').pop().toLowerCase()
    if (!['pdf', 'pptx', 'ppt'].includes(ext)) {
      setValidationError('Invalid file type. Please upload PDF or PPTX files only.')
      e.target.value = ''
      return
    }
    if (file.size / (1024 * 1024) > 10) {
      setValidationError(`File too large (${(file.size / (1024 * 1024)).toFixed(1)}MB). Maximum size is 10MB.`)
      e.target.value = ''
      return
    }
    setValidationError(null)
    setUploadedFile(file)
  }

  const handleClearFile = () => {
    setUploadedFile(null)
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  return (
    <div className="p-5 sm:p-6">
      {/* Style mismatch warning banner */}
      {styleWarning && (
        <div className="mb-4 bg-amber-50 border border-amber-200/80 rounded-xl p-4">
          <div className="flex items-start gap-3">
            <svg className="w-5 h-5 text-amber-500 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
            </svg>
            <div className="flex-1">
              <p className="text-[13px] font-semibold text-amber-800 mb-1">Shadow's Recommendation</p>
              <p className="text-[12px] text-amber-700 leading-relaxed mb-2">{styleWarning.warning}</p>
              <p className="text-[11px] text-amber-600">
                Your plan was generated with <span className="font-semibold">{styleWarning.selected_style}</span> mode.
                {styleWarning.recommended_styles?.length > 0 && (
                  <> Try <span className="font-semibold">{styleWarning.recommended_styles[0]}</span> next time for better results with this type of content.</>
                )}
              </p>
            </div>
            <button
              type="button"
              onClick={() => setStyleWarning(null)}
              className="p-1 rounded-lg text-amber-400 hover:text-amber-600 hover:bg-amber-100 transition-colors"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
      )}

      <form onSubmit={handleGeneratePlan} className="space-y-5">

        {/* Topic + Duration */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="md:col-span-2">
            <label className="block text-[12px] font-semibold text-navy-800 uppercase tracking-wider mb-2">
              What do you want to master?
              {!uploadedFile && <span className="text-red-500 ml-0.5">*</span>}
              {uploadedFile && <span className="text-surface-400 normal-case tracking-normal ml-1">(optional with upload)</span>}
            </label>
            <input
              type="text"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder={uploadedFile ? 'e.g., Binary Trees (or leave blank)' : 'e.g., Binary Search Trees, React Hooks...'}
              className="w-full bg-surface-50 border border-surface-200/80 rounded-xl px-4 py-2.5 text-[13px] text-navy-900 placeholder:text-surface-300 focus:border-navy-300 focus:ring-2 focus:ring-navy-100 focus:bg-white transition-all outline-none"
              disabled={generating}
            />
          </div>
          <div>
            <label className="block text-[12px] font-semibold text-navy-800 uppercase tracking-wider mb-2">Duration</label>
            <select
              value={duration}
              onChange={(e) => setDuration(e.target.value)}
              className="w-full bg-surface-50 border border-surface-200/80 rounded-xl px-4 py-2.5 text-[13px] text-navy-900 focus:border-navy-300 focus:ring-2 focus:ring-navy-100 focus:bg-white transition-all outline-none"
              disabled={generating}
            >
              <option value="auto">Auto (AI decides)</option>
              <option value="5">5 days (Quick)</option>
              <option value="7">7 days (Standard)</option>
              <option value="10">10 days (Thorough)</option>
              <option value="14">14 days (Comprehensive)</option>
            </select>
          </div>
        </div>

        {/* File Upload */}
        <div className="rounded-xl border border-dashed border-surface-200/80 bg-surface-50/50 p-4">
          <div className="flex items-center justify-between mb-2">
            <label className="text-[12px] font-semibold text-navy-800 uppercase tracking-wider flex items-center gap-1.5">
              <UploadIcon className="w-3.5 h-3.5" />
              Upload Lecture Slides
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
                <p className="text-[11px] text-surface-400 mt-0.5">AI will extract topics from your slides</p>
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
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Library Document Selection */}
        {!uploadedFile && (
          <div className="rounded-xl border border-surface-200/80 bg-white p-4">
            <label className="block text-[12px] font-semibold text-navy-800 uppercase tracking-wider mb-2 flex items-center gap-1.5">
              <DocIcon className="w-3.5 h-3.5" />
              Or Use Document from Library
            </label>

            {!selectedLibraryDoc ? (
              <div>
                <button
                  type="button"
                  onClick={() => { setShowLibraryBrowser(!showLibraryBrowser); if (!showLibraryBrowser) loadLibraryDocuments() }}
                  className="w-full px-4 py-2.5 bg-surface-50 hover:bg-surface-100 border border-surface-200/80 text-navy-800 rounded-xl text-[13px] font-medium transition-colors flex items-center justify-center gap-2"
                  disabled={generating}
                >
                  <SearchIcon className="w-4 h-4 text-surface-400" />
                  {showLibraryBrowser ? 'Hide Library' : 'Browse Library Documents'}
                </button>

                {showLibraryBrowser && (
                  <div className="mt-3 max-h-56 overflow-y-auto space-y-1.5 border border-surface-200/80 rounded-xl p-2">
                    {libraryDocuments.length === 0 ? (
                      <p className="text-[13px] text-surface-400 text-center py-4">No documents in library yet</p>
                    ) : (
                      libraryDocuments.map(doc => (
                        <button
                          key={doc.id}
                          type="button"
                          onClick={() => { setSelectedLibraryDoc(doc); setTopic(doc.topic); setShowLibraryBrowser(false) }}
                          className="w-full text-left px-3 py-2.5 bg-white hover:bg-navy-800/[0.02] border border-surface-200/60 rounded-lg transition-colors"
                        >
                          <div className="flex items-start gap-2.5">
                            <DocIcon className="w-4 h-4 text-surface-300 mt-0.5 flex-shrink-0" />
                            <div className="flex-1 min-w-0">
                              <p className="text-[13px] font-semibold text-navy-900 truncate">{doc.topic}</p>
                              <p className="text-[11px] text-surface-400">{doc.course_code} {doc.week_number ? `· Week ${doc.week_number}` : ''}</p>
                            </div>
                            <span className="text-[10px] font-semibold bg-emerald-50 text-emerald-600 px-1.5 py-0.5 rounded-md flex-shrink-0">
                              {doc.helpful_votes} votes
                            </span>
                          </div>
                        </button>
                      ))
                    )}
                  </div>
                )}
              </div>
            ) : (
              <div className="bg-navy-800/[0.03] border border-navy-200/60 rounded-xl p-3">
                <div className="flex items-start gap-2.5">
                  <svg className="w-4 h-4 text-emerald-500 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <div className="flex-1">
                    <p className="text-[13px] font-semibold text-navy-900">{selectedLibraryDoc.topic}</p>
                    <p className="text-[11px] text-surface-400">
                      {selectedLibraryDoc.course_code} {selectedLibraryDoc.week_number ? `· Week ${selectedLibraryDoc.week_number}` : ''}
                    </p>
                  </div>
                  <button type="button" onClick={() => { setSelectedLibraryDoc(null); setTopic('') }}
                    className="text-[11px] font-semibold text-red-500 hover:text-red-600 transition-colors">Remove</button>
                </div>
              </div>
            )}

            <p className="text-[11px] text-surface-400 mt-2">
              Select a document uploaded by classmates to generate a study plan from shared course materials
            </p>
          </div>
        )}

        {/* Course Selection & Library Contribution */}
        {uploadedFile && (
          <div className="rounded-xl border border-sky-200/60 bg-sky-50/40 p-4 space-y-3">
            {/* Course selector — always shown when file uploaded so slides can be saved */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-[11px] font-semibold text-navy-800 uppercase tracking-wider mb-1">
                  Course <span className="text-red-500">*</span>
                </label>
                <select
                  value={selectedCourse}
                  onChange={(e) => setSelectedCourse(e.target.value)}
                  className="w-full bg-white border border-surface-200/80 rounded-lg px-3 py-2 text-[13px] text-navy-900 focus:border-navy-300 focus:ring-2 focus:ring-navy-100 transition-all outline-none"
                  disabled={generating}
                  required
                >
                  <option value="">Select course...</option>
                  {enrolledCourses.map((c) => (
                    <option key={c.course.id} value={c.course.id}>{c.course.code} - {c.course.title}</option>
                  ))}
                </select>
                <p className="text-[10px] text-surface-400 mt-1">Required so your slides remain accessible in your plan</p>
              </div>
              <div>
                <label className="block text-[11px] font-semibold text-navy-800 uppercase tracking-wider mb-1">
                  Week <span className="text-surface-400 normal-case tracking-normal font-normal">(optional)</span>
                </label>
                <select
                  value={weekNumber}
                  onChange={(e) => setWeekNumber(e.target.value)}
                  className="w-full bg-white border border-surface-200/80 rounded-lg px-3 py-2 text-[13px] text-navy-900 focus:border-navy-300 focus:ring-2 focus:ring-navy-100 transition-all outline-none"
                  disabled={generating}
                >
                  <option value="">Select week...</option>
                  {Array.from({ length: 15 }, (_, i) => i + 1).map((w) => (
                    <option key={w} value={w}>Week {w}</option>
                  ))}
                </select>
              </div>
            </div>

            {/* Share with classmates toggle */}
            <button
              type="button"
              onClick={() => setIsSchoolMaterial(!isSchoolMaterial)}
              className={`w-full flex items-center gap-3 rounded-xl border-2 p-3 transition-all ${
                isSchoolMaterial
                  ? 'bg-navy-800/5 border-navy-800'
                  : 'bg-white border-surface-200 hover:border-navy-400'
              }`}
            >
              <div className={`relative w-10 h-6 rounded-full flex-shrink-0 transition-colors ${
                isSchoolMaterial ? 'bg-navy-800' : 'bg-surface-300'
              }`}>
                <div className={`absolute top-1 w-4 h-4 rounded-full bg-white shadow transition-transform ${
                  isSchoolMaterial ? 'translate-x-5' : 'translate-x-1'
                }`} />
              </div>
              <div className="flex-1 text-left">
                <p className="text-[13px] font-semibold text-navy-900 flex items-center gap-1.5">
                  <svg className="w-4 h-4 text-navy-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" />
                  </svg>
                  Share with classmates
                </p>
                <p className="text-[11px] text-surface-400 mt-0.5">
                  Add your slides to the public library for other students
                </p>
              </div>
            </button>
          </div>
        )}

        {/* Learning Style */}
        <div>
          <label className="block text-[12px] font-semibold text-navy-800 uppercase tracking-wider mb-2">Your Learning Style</label>
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-2">
            {STYLES.map((style) => (
              <button
                key={style.value}
                type="button"
                onClick={() => setLearningStyle(style.value)}
                className={`p-3 rounded-xl border transition-all text-center ${
                  learningStyle === style.value
                    ? 'border-navy-400/60 bg-navy-800/[0.04] ring-1 ring-navy-200'
                    : 'border-surface-200/80 hover:border-navy-300/60 bg-white'
                }`}
                disabled={generating}
              >
                <div className={`mx-auto mb-1.5 w-8 h-8 rounded-lg flex items-center justify-center ${
                  learningStyle === style.value ? 'bg-navy-800 text-white' : 'bg-surface-100 text-surface-400'
                } transition-colors`}>
                  {style.icon}
                </div>
                <p className="text-[12px] font-semibold text-navy-800">{style.label}</p>
                <p className="text-[10px] text-surface-400">{style.desc}</p>
              </button>
            ))}
          </div>
        </div>

        {/* Audio learner hint */}
        {learningStyle === 'audio' && (
          <div className="flex items-center gap-2 text-[12px] text-emerald-600 bg-emerald-50/50 rounded-lg px-3 py-2 border border-emerald-200/60">
            <svg className="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8">
              <path strokeLinecap="round" strokeLinejoin="round" d="M19.114 5.636a9 9 0 010 12.728M16.463 8.288a5.25 5.25 0 010 7.424M6.75 8.25l4.72-4.72a.75.75 0 011.28.53v15.88a.75.75 0 01-1.28.53l-4.72-4.72H4.51c-.88 0-1.704-.507-1.938-1.354A9.01 9.01 0 012.25 12c0-.83.112-1.633.322-2.396C2.806 8.756 3.63 8.25 4.51 8.25H6.75z" />
            </svg>
            Audio learner detected! We'll generate podcast-style audio summaries.
          </div>
        )}

        {/* Kinesthetic learner hint */}
        {learningStyle === 'kinesthetic' && (
          <div className="flex items-center gap-2 text-[12px] text-violet-600 bg-violet-50/50 rounded-lg px-3 py-2 border border-violet-200/60">
            <svg className="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8">
              <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z" />
            </svg>
            Hands-on mode! Every activity will include practice exercises, coding challenges, and interactive tasks.
          </div>
        )}

        {/* Reading learner hint */}
        {learningStyle === 'reading' && (
          <div className="flex items-center gap-2 text-[12px] text-emerald-600 bg-emerald-50/50 rounded-lg px-3 py-2 border border-emerald-200/60">
            <svg className="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 016-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0018 18a8.967 8.967 0 00-6 2.292m0-14.25v14.25" />
            </svg>
            Reading mode! Each activity includes flashcards, key concept summaries, and comprehension questions.
          </div>
        )}

        {/* Validation error banner */}
        {validationError && (
          <div className="flex items-center gap-2.5 p-3 rounded-xl bg-red-50 border border-red-200/80">
            <svg className="w-4 h-4 text-red-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
            </svg>
            <p className="text-[12px] font-medium text-red-700 flex-1">{validationError}</p>
            <button
              type="button"
              onClick={() => setValidationError(null)}
              className="p-1 rounded-lg text-red-400 hover:text-red-600 hover:bg-red-100 transition-colors"
            >
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        )}

        {/* Actions */}
        <div className="flex items-center justify-end gap-2.5 pt-1">
          <button
            type="button"
            onClick={onCancel}
            className="px-4 py-2 text-[13px] font-medium text-surface-400 hover:text-navy-800 hover:bg-surface-100 rounded-xl transition-all"
            disabled={generating}
          >Cancel</button>
          <button
            type="submit"
            disabled={generating || (!topic.trim() && !uploadedFile && !selectedLibraryDoc) || (uploadedFile && !selectedCourse)}
            className="flex items-center gap-2 bg-navy-800 hover:bg-navy-900 disabled:bg-surface-200 disabled:cursor-not-allowed text-white px-5 py-2.5 rounded-xl text-[13px] font-semibold transition-all"
          >
            {generating ? (
              <>
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Generating...
              </>
            ) : (
              <>
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z" />
                </svg>
                Generate Plan
              </>
            )}
          </button>
        </div>
      </form>

      {/* Show generating overlay when plan is being created */}
      {generating && <GeneratingOverlay />}
    </div>
  )
}
