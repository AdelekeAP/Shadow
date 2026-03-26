import { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react'
import { getStudyPlans, getStudyPlan, generateStudyPlan } from '../services/api'
import { useAuth } from './AuthContext'

const SmartStudyContext = createContext(null)

export function SmartStudyProvider({ children }) {
  const { isAuthenticated } = useAuth()

  /* ─── Core state ─── */
  const [plans, setPlans] = useState([])
  const [currentPlan, setCurrentPlan] = useState(null)
  const [loading, setLoading] = useState(false)
  const [loadError, setLoadError] = useState(null)
  const [plansLoaded, setPlansLoaded] = useState(false)

  /* ─── Generation state (survives route changes) ─── */
  const [generating, setGenerating] = useState(false)
  const [generationResult, setGenerationResult] = useState(null) // { success: true, plan } or { success: false, error }
  const generationAbortRef = useRef(false)

  /* ─── Load plans on auth ─── */
  const loadStudyPlans = useCallback(async () => {
    if (!isAuthenticated) return
    try {
      setLoading(true)
      setLoadError(null)
      const data = await getStudyPlans(false)
      setPlans(data)
      // Auto-select active plan if none selected (fetch full data for slide content)
      if (!currentPlan) {
        const active = data.find(p => p.is_active)
        const toSelect = active || data[0]
        if (toSelect) {
          setCurrentPlan(toSelect)
          getStudyPlan(toSelect.id).then(full => setCurrentPlan(full)).catch(() => {})
        }
      }
      setPlansLoaded(true)
    } catch (err) {
      console.error('Error loading study plans:', err)
      setLoadError('Failed to load study plans. Check your connection and try again.')
    } finally {
      setLoading(false)
    }
  }, [isAuthenticated]) // eslint-disable-line react-hooks/exhaustive-deps

  /* ─── Load plans when authenticated (once) ─── */
  useEffect(() => {
    if (isAuthenticated && !plansLoaded && !loading) {
      loadStudyPlans()
    }
  }, [isAuthenticated, plansLoaded, loading, loadStudyPlans])

  /* ─── Reset on logout ─── */
  useEffect(() => {
    if (!isAuthenticated) {
      setPlans([])
      setCurrentPlan(null)
      setPlansLoaded(false)
      setGenerating(false)
      setGenerationResult(null)
    }
  }, [isAuthenticated])

  /* ─── Start plan generation (lives in context so it survives navigation) ─── */
  const startGeneration = useCallback(async (params) => {
    if (generating) return
    generationAbortRef.current = false
    setGenerating(true)
    setGenerationResult(null)

    try {
      const result = await generateStudyPlan(params)

      if (generationAbortRef.current) return

      // Refresh plans list
      const freshPlans = await getStudyPlans(false)
      setPlans(freshPlans)

      // Auto-select the newly generated plan (fetch full data for slide content)
      const newPlan = freshPlans.find(p =>
        p.id === (result.study_plan_id || result.id)
      ) || freshPlans[0]

      if (newPlan) {
        setCurrentPlan(newPlan)
        getStudyPlan(newPlan.id).then(full => setCurrentPlan(full)).catch(() => {})
      }

      setGenerationResult({ success: true, plan: result })
    } catch (err) {
      console.error('Error generating study plan:', err)
      if (!generationAbortRef.current) {
        setGenerationResult({ success: false, error: err?.message || 'Failed to generate study plan. Please try again.' })
      }
    } finally {
      if (!generationAbortRef.current) {
        setGenerating(false)
      }
    }
  }, [generating])

  /* ─── Select a plan and fetch full data (includes _slide_content) ─── */
  const selectPlan = useCallback(async (plan) => {
    if (!plan) { setCurrentPlan(null); return }
    // Set summary immediately for responsiveness
    setCurrentPlan(plan)
    // Fetch full plan data (list endpoint strips _slide_content for performance)
    try {
      const fullPlan = await getStudyPlan(plan.id)
      setCurrentPlan(fullPlan)
    } catch {
      // Keep summary data if full fetch fails
    }
  }, [])

  /* ─── Clear generation result (consumed by SmartStudyPage) ─── */
  const clearGenerationResult = useCallback(() => {
    setGenerationResult(null)
  }, [])

  const value = {
    // Plans state
    plans,
    setPlans,
    currentPlan,
    setCurrentPlan,
    selectPlan,
    loading,
    loadError,
    plansLoaded,
    loadStudyPlans,

    // Generation state
    generating,
    generationResult,
    startGeneration,
    clearGenerationResult,
  }

  return <SmartStudyContext.Provider value={value}>{children}</SmartStudyContext.Provider>
}

export function useSmartStudy() {
  const context = useContext(SmartStudyContext)
  if (!context) {
    throw new Error('useSmartStudy must be used within a SmartStudyProvider')
  }
  return context
}

export default SmartStudyContext
