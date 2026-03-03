/**
 * API Service for Shadow Frontend
 * Handles all HTTP requests to the backend
 */
import axios from 'axios'

// API base URL
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Request interceptor - add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor - handle errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Unauthorized - clear token and redirect to login
      localStorage.removeItem('access_token')
      localStorage.removeItem('user')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// ============================================
// Authentication API
// ============================================

/**
 * Register a new user
 * @param {Object} userData - User registration data
 * @returns {Promise} API response with token and user data
 */
export const register = async (userData) => {
  try {
    const response = await api.post('/api/v1/auth/register', userData)

    // Save token and user to localStorage
    if (response.data.access_token) {
      localStorage.setItem('access_token', response.data.access_token)
      localStorage.setItem('user', JSON.stringify(response.data.user))
    }

    return response.data
  } catch (error) {
    throw error.response?.data || error
  }
}

/**
 * Login user
 * @param {Object} credentials - Email and password
 * @returns {Promise} API response with token and user data
 */
export const login = async (credentials) => {
  try {
    const response = await api.post('/api/v1/auth/login', credentials)

    // Save token and user to localStorage
    if (response.data.access_token) {
      localStorage.setItem('access_token', response.data.access_token)
      localStorage.setItem('user', JSON.stringify(response.data.user))
    }

    return response.data
  } catch (error) {
    throw error.response?.data || error
  }
}

/**
 * Logout user
 */
export const logout = () => {
  localStorage.removeItem('access_token')
  localStorage.removeItem('user')
  window.location.href = '/login'
}

/**
 * Get current user from localStorage
 * @returns {Object|null} User object or null
 */
export const getCurrentUser = () => {
  const userStr = localStorage.getItem('user')
  return userStr ? JSON.parse(userStr) : null
}

/**
 * Check if user is authenticated
 * @returns {boolean} True if authenticated
 */
export const isAuthenticated = () => {
  return !!localStorage.getItem('access_token')
}

/**
 * Update user preferences
 * @param {Object} preferences - Preferences to update
 * @returns {Promise} Updated user data
 */
export const updateUserPreferences = async (preferences) => {
  try {
    const response = await api.patch('/api/v1/auth/me/preferences', preferences)
    // Update local storage
    if (response.data) {
      const currentUser = JSON.parse(localStorage.getItem('user') || '{}')
      const updatedUser = { ...currentUser, ...response.data }
      localStorage.setItem('user', JSON.stringify(updatedUser))
    }
    return response.data
  } catch (error) {
    throw error.response?.data || error
  }
}

/**
 * Get current user from API
 * @returns {Promise} User data
 */
export const fetchCurrentUser = async () => {
  try {
    const response = await api.get('/api/v1/auth/me')
    if (response.data) {
      localStorage.setItem('user', JSON.stringify(response.data))
    }
    return response.data
  } catch (error) {
    throw error.response?.data || error
  }
}

// ============================================
// Courses API
// ============================================

/**
 * Get all available courses with optional filters
 * @param {Object} filters - Optional filters (level, status_filter, department)
 * @returns {Promise} List of courses
 */
export const getCourses = async (filters = {}) => {
  try {
    const params = new URLSearchParams(filters).toString()
    const url = params ? `/api/v1/courses/?${params}` : '/api/v1/courses/'
    const response = await api.get(url)
    return response.data
  } catch (error) {
    throw error.response?.data || error
  }
}

/**
 * Get a specific course by ID
 * @param {string} courseId - Course UUID
 * @returns {Promise} Course details
 */
export const getCourseById = async (courseId) => {
  try {
    const response = await api.get(`/api/v1/courses/${courseId}`)
    return response.data
  } catch (error) {
    throw error.response?.data || error
  }
}

/**
 * Enroll in a course
 * @param {string} courseId - Course UUID
 * @param {Object} options - Optional enrollment options (is_carryover, is_priority, semester_id)
 * @returns {Promise} Enrollment details
 */
export const enrollInCourse = async (courseId, options = {}) => {
  try {
    const response = await api.post('/api/v1/courses/enroll', {
      course_id: courseId,
      ...options
    })
    return response.data
  } catch (error) {
    throw error.response?.data || error
  }
}

/**
 * Get user's enrolled courses
 * @param {boolean} activeOnly - Only return active semester courses
 * @returns {Promise} List of enrolled courses with details
 */
export const getEnrolledCourses = async (activeOnly = true) => {
  try {
    const url = activeOnly
      ? '/api/v1/courses/my-courses/?active_only=true'
      : '/api/v1/courses/my-courses/'
    const response = await api.get(url)
    return response.data
  } catch (error) {
    throw error.response?.data || error
  }
}

/**
 * Get specific enrollment details
 * @param {string} userCourseId - User course enrollment UUID
 * @returns {Promise} Enrollment details
 */
export const getEnrollmentDetails = async (userCourseId) => {
  try {
    const response = await api.get(`/api/v1/courses/my-courses/${userCourseId}`)
    return response.data
  } catch (error) {
    throw error.response?.data || error
  }
}

/**
 * Update enrollment details (marks, priority, etc.)
 * @param {string} userCourseId - User course enrollment UUID
 * @param {Object} updateData - Update data (ca_score, participation_score, exam_score, etc.)
 * @returns {Promise} Updated enrollment
 */
export const updateEnrollment = async (userCourseId, updateData) => {
  try {
    const response = await api.patch(`/api/v1/courses/my-courses/${userCourseId}`, updateData)
    return response.data
  } catch (error) {
    throw error.response?.data || error
  }
}

/**
 * Unenroll from a course
 * @param {string} userCourseId - User course enrollment UUID
 * @returns {Promise} Success status
 */
export const unenrollFromCourse = async (userCourseId) => {
  try {
    await api.delete(`/api/v1/courses/my-courses/${userCourseId}`)
    return { success: true }
  } catch (error) {
    throw error.response?.data || error
  }
}

// ============================================
// Tasks API
// ============================================

/**
 * Get all tasks with optional filters
 * @param {Object} filters - Optional filters (course_id, is_completed, category, is_urgent)
 * @returns {Promise} List of tasks
 */
export const getTasks = async (filters = {}) => {
  try {
    const params = new URLSearchParams(filters).toString()
    const url = params ? `/api/v1/tasks/?${params}` : '/api/v1/tasks/'
    const response = await api.get(url)
    return response.data
  } catch (error) {
    throw error.response?.data || error
  }
}

/**
 * Get task statistics
 * @returns {Promise} Task statistics
 */
export const getTaskStats = async () => {
  try {
    const response = await api.get('/api/v1/tasks/stats')
    return response.data
  } catch (error) {
    throw error.response?.data || error
  }
}

/**
 * Get tasks grouped by course
 * @returns {Promise} Course task summaries
 */
export const getTasksByCourse = async () => {
  try {
    const response = await api.get('/api/v1/tasks/by-course')
    return response.data
  } catch (error) {
    throw error.response?.data || error
  }
}

/**
 * Get a specific task by ID
 * @param {string} taskId - Task UUID
 * @returns {Promise} Task details
 */
export const getTaskById = async (taskId) => {
  try {
    const response = await api.get(`/api/v1/tasks/${taskId}`)
    return response.data
  } catch (error) {
    throw error.response?.data || error
  }
}

/**
 * Create a new task
 * @param {Object} taskData - Task creation data
 * @returns {Promise} Created task
 */
export const createTask = async (taskData) => {
  try {
    const response = await api.post('/api/v1/tasks/', taskData)
    return response.data
  } catch (error) {
    throw error.response?.data || error
  }
}

/**
 * Update a task
 * @param {string} taskId - Task UUID
 * @param {Object} updateData - Fields to update
 * @returns {Promise} Updated task
 */
export const updateTask = async (taskId, updateData) => {
  try {
    const response = await api.patch(`/api/v1/tasks/${taskId}`, updateData)
    return response.data
  } catch (error) {
    throw error.response?.data || error
  }
}

/**
 * Mark a task as complete
 * @param {string} taskId - Task UUID
 * @param {Object} completionData - Earned marks and actual effort
 * @returns {Promise} Updated task
 */
export const completeTask = async (taskId, completionData = {}) => {
  try {
    const response = await api.patch(`/api/v1/tasks/${taskId}/complete`, completionData)
    return response.data
  } catch (error) {
    throw error.response?.data || error
  }
}

/**
 * Delete a task
 * @param {string} taskId - Task UUID
 * @returns {Promise} Success status
 */
export const deleteTask = async (taskId) => {
  try {
    await api.delete(`/api/v1/tasks/${taskId}`)
    return { success: true }
  } catch (error) {
    throw error.response?.data || error
  }
}

// ============================================
// GPA API (TODO)
// ============================================

export const getCurrentCGPA = async () => {
  const response = await api.get('/api/v1/gpa/current')
  return response.data
}

// ============================================
// Semesters API
// ============================================

export const createAcademicYear = async (academicYear) => {
  const response = await api.post('/api/v1/semesters/academic-year', { academic_year: academicYear })
  return response.data
}

export const getSemesters = async () => {
  const response = await api.get('/api/v1/semesters/')
  return response.data
}

export const getActiveSemester = async () => {
  const response = await api.get('/api/v1/semesters/active')
  return response.data
}

export const activateSemester = async (semesterId) => {
  const response = await api.patch(`/api/v1/semesters/${semesterId}/activate`)
  return response.data
}

export const assignCoursesToSemester = async (semesterId, userCourseIds) => {
  const response = await api.post(`/api/v1/semesters/${semesterId}/assign-courses`, {
    user_course_ids: userCourseIds
  })
  return response.data
}

// ============================================
// SmartStudy API
// ============================================

/**
 * Send a message to SmartStudy AI
 * @param {string} content - Message content
 * @param {string|null} conversationId - Optional conversation ID to continue existing chat
 * @returns {Promise} Response with AI message
 */
export const sendSmartStudyMessage = async (content, conversationId = null) => {
  try {
    const response = await api.post('/api/v1/smartstudy/chat', {
      content,
      conversation_id: conversationId
    })
    return response.data
  } catch (error) {
    throw error.response?.data || error
  }
}

/**
 * Get all chat conversations for current user
 * @param {number} limit - Number of conversations to return
 * @returns {Promise} List of conversations
 */
export const getSmartStudyConversations = async (limit = 20) => {
  try {
    const response = await api.get('/api/v1/smartstudy/conversations', {
      params: { limit }
    })
    return response.data
  } catch (error) {
    throw error.response?.data || error
  }
}

/**
 * Get a specific conversation with all messages
 * @param {string} conversationId - Conversation UUID
 * @returns {Promise} Conversation with messages
 */
export const getSmartStudyConversation = async (conversationId) => {
  try {
    const response = await api.get(`/api/v1/smartstudy/conversations/${conversationId}`)
    return response.data
  } catch (error) {
    throw error.response?.data || error
  }
}

/**
 * Delete a conversation
 * @param {string} conversationId - Conversation UUID
 * @returns {Promise} Success response
 */
export const deleteSmartStudyConversation = async (conversationId) => {
  try {
    const response = await api.delete(`/api/v1/smartstudy/conversations/${conversationId}`)
    return response.data
  } catch (error) {
    throw error.response?.data || error
  }
}

/**
 * Get suggested chat prompts based on student's current state
 * @returns {Promise} List of suggested prompts
 */
export const getSmartStudySuggestedPrompts = async () => {
  try {
    const response = await api.get('/api/v1/smartstudy/suggested-prompts')
    return response.data
  } catch (error) {
    throw error.response?.data || error
  }
}

/**
 * Check if SmartStudy should be triggered on dashboard
 * @returns {Promise} Trigger information
 */
export const getSmartStudyDashboardTrigger = async () => {
  try {
    const response = await api.get('/api/v1/smartstudy/dashboard-trigger')
    return response.data
  } catch (error) {
    throw error.response?.data || error
  }
}

/**
 * Get student context for SmartStudy
 * @returns {Promise} Student context data
 */
export const getSmartStudyContext = async () => {
  try {
    const response = await api.get('/api/v1/smartstudy/context')
    return response.data
  } catch (error) {
    throw error.response?.data || error
  }
}

// ============================================
// SmartStudy - Study Plans API
// ============================================

/**
 * Generate a new AI-powered study plan
 * @param {object} planData - Plan creation data
 * @param {string} planData.topic - Topic to study (e.g., "Binary Search Trees")
 * @param {string} planData.courseId - Optional course UUID
 * @param {number} planData.durationDays - Optional duration (auto-calculated if not provided)
 * @param {string} planData.difficultyLevel - "beginner", "intermediate", "advanced", or "auto"
 * @param {string} planData.triggerType - "reactive", "proactive", "preventive", "exploratory"
 * @param {File} planData.uploadedFile - Optional uploaded file (PDF/PPTX)
 * @returns {Promise} Generated study plan
 */
export const generateStudyPlan = async (planData) => {
  try {
    // If file is provided, use FormData for multipart upload
    if (planData.uploadedFile) {
      const formData = new FormData()

      // Add file
      formData.append('uploaded_file', planData.uploadedFile)

      // Add other fields
      if (planData.topic) formData.append('topic', planData.topic)
      if (planData.courseId) formData.append('course_id', planData.courseId)
      if (planData.durationDays) formData.append('duration_days', planData.durationDays.toString())
      formData.append('difficulty_level', planData.difficultyLevel || 'auto')
      if (planData.learningStyle) formData.append('learning_style', planData.learningStyle)
      formData.append('trigger_type', planData.triggerType || 'student_request')
      if (planData.triggerTaskId) formData.append('trigger_task_id', planData.triggerTaskId)
      if (planData.triggerScore) formData.append('trigger_score', planData.triggerScore.toString())

      // Library contribution fields
      if (planData.isSchoolMaterial !== undefined) formData.append('is_school_material', planData.isSchoolMaterial.toString())
      if (planData.weekNumber) formData.append('week_number', planData.weekNumber.toString())
      if (planData.libraryDocumentId) formData.append('library_document_id', planData.libraryDocumentId)

      // Use the upload endpoint with multipart/form-data
      const response = await api.post('/api/v1/smartstudy/study-plans/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })
      return response.data
    } else {
      // No file - use regular JSON endpoint
      const response = await api.post('/api/v1/smartstudy/study-plans', {
        topic: planData.topic,
        course_id: planData.courseId || null,
        duration_days: planData.durationDays || null,
        difficulty_level: planData.difficultyLevel || 'auto',
        learning_style: planData.learningStyle || null,
        trigger_type: planData.triggerType || 'student_request',
        trigger_task_id: planData.triggerTaskId || null,
        trigger_score: planData.triggerScore || null
      })
      return response.data
    }
  } catch (error) {
    throw error.response?.data || error
  }
}

/**
 * Get all study plans for current user
 * @param {boolean} activeOnly - If true, only return active (incomplete) plans
 * @returns {Promise} List of study plans
 */
export const getStudyPlans = async (activeOnly = true) => {
  try {
    const response = await api.get('/api/v1/smartstudy/study-plans', {
      params: { active_only: activeOnly }
    })
    return response.data
  } catch (error) {
    throw error.response?.data || error
  }
}

/**
 * Get a specific study plan by ID
 * @param {string} planId - Study plan UUID
 * @returns {Promise} Study plan with all resources
 */
export const getStudyPlan = async (planId) => {
  try {
    const response = await api.get(`/api/v1/smartstudy/study-plans/${planId}`)
    return response.data
  } catch (error) {
    throw error.response?.data || error
  }
}

/**
 * Update study plan progress
 * @param {string} planId - Study plan UUID
 * @param {object} updateData - Update data
 * @param {number} updateData.completionPercentage - Progress (0-100)
 * @param {boolean} updateData.isActive - Mark as inactive when completed
 * @param {number} updateData.afterScore - Score after intervention
 * @returns {Promise} Update result
 */
export const updateStudyPlanProgress = async (planId, updateData) => {
  try {
    const response = await api.patch(`/api/v1/smartstudy/study-plans/${planId}`, {
      completion_percentage: updateData.completionPercentage,
      is_active: updateData.isActive,
      before_score: updateData.beforeScore,
      after_score: updateData.afterScore,
      completed_days: updateData.completedDays
    })
    return response.data
  } catch (error) {
    throw error.response?.data || error
  }
}

/**
 * Track when a student clicks on a study plan resource
 * @param {string} planId - Study plan UUID
 * @param {string} resourceId - Resource UUID
 * @returns {Promise} Success response
 */
export const trackResourceClick = async (planId, resourceId) => {
  try {
    const response = await api.post(`/api/v1/smartstudy/study-plans/${planId}/resources/${resourceId}/click`)
    return response.data
  } catch (error) {
    throw error.response?.data || error
  }
}

/**
 * Mark a study plan resource as completed
 * @param {string} planId - Study plan UUID
 * @param {string} resourceId - Resource UUID
 * @param {number} helpfulRating - Optional rating 1-5 stars
 * @returns {Promise} Success response
 */
export const markResourceComplete = async (planId, resourceId, helpfulRating = null) => {
  try {
    const response = await api.post(`/api/v1/smartstudy/study-plans/${planId}/resources/${resourceId}/complete`, {
      completed: true,
      helpful_rating: helpfulRating
    })
    return response.data
  } catch (error) {
    throw error.response?.data || error
  }
}

/**
 * Report a broken or irrelevant resource
 * @param {string} planId - Study plan UUID
 * @param {string} resourceId - Resource UUID
 * @param {string} reason - "broken_link", "irrelevant", or "outdated"
 * @returns {Promise} Success response
 */
export const reportBrokenResource = async (planId, resourceId, reason = 'broken_link') => {
  try {
    const response = await api.post(
      `/api/v1/smartstudy/study-plans/${planId}/resources/${resourceId}/report`,
      { reason }
    )
    return response.data
  } catch (error) {
    throw error.response?.data || error
  }
}

/**
 * Generate an audio summary for a resource
 * @param {string} planId - Study plan UUID
 * @param {string} resourceId - Resource UUID
 * @returns {Promise} Response with audio_url, script, duration_estimate
 */
export const generateAudioSummary = async (planId, resourceId) => {
  try {
    const response = await api.post(
      `/api/v1/smartstudy/study-plans/${planId}/resources/${resourceId}/audio`
    )
    return response.data
  } catch (error) {
    throw error.response?.data || error
  }
}

// ============================================
// Learning Library API
// ============================================

/**
 * Browse library documents with optional filters
 * @param {Object} filters - Filter parameters
 * @param {string} filters.courseId - Filter by course UUID
 * @param {number} filters.weekNumber - Filter by week (1-15)
 * @param {string} filters.search - Search in topic or filename
 * @param {number} filters.limit - Max results (default 50)
 * @param {number} filters.offset - Pagination offset
 * @returns {Promise} List of library documents
 */
export const browseLibrary = async (filters = {}) => {
  try {
    const params = new URLSearchParams()
    if (filters.courseId) params.append('course_id', filters.courseId)
    if (filters.weekNumber) params.append('week_number', filters.weekNumber)
    if (filters.search) params.append('search', filters.search)
    if (filters.limit) params.append('limit', filters.limit)
    if (filters.offset) params.append('offset', filters.offset)

    const response = await api.get(`/api/v1/library/browse?${params.toString()}`)
    return response.data
  } catch (error) {
    throw error.response?.data || error
  }
}

/**
 * Get a specific library document details
 * @param {string} documentId - Document UUID
 * @returns {Promise} Document details
 */
export const getLibraryDocument = async (documentId) => {
  try {
    const response = await api.get(`/api/v1/library/documents/${documentId}`)
    return response.data
  } catch (error) {
    throw error.response?.data || error
  }
}

/**
 * Vote on a library document
 * @param {string} documentId - Document UUID
 * @param {number} voteValue - +1 for upvote, -1 for downvote
 * @returns {Promise} Vote result
 */
export const voteOnDocument = async (documentId, voteValue) => {
  try {
    const response = await api.post(`/api/v1/library/documents/${documentId}/vote`, {
      vote_value: voteValue
    })
    return response.data
  } catch (error) {
    throw error.response?.data || error
  }
}

/**
 * Download a library document
 * @param {string} documentId - Document UUID
 * @returns {Promise} File download
 */
export const downloadLibraryDocument = async (documentId) => {
  try {
    const response = await api.get(`/api/v1/library/documents/${documentId}/download`, {
      responseType: 'blob'
    })
    return response.data
  } catch (error) {
    throw error.response?.data || error
  }
}

/**
 * Get current user's library contributions and stats
 * @returns {Promise} User's contributions data
 */
export const getMyContributions = async () => {
  try {
    const response = await api.get('/api/v1/library/my-contributions')
    return response.data
  } catch (error) {
    throw error.response?.data || error
  }
}

/**
 * Get overall library statistics
 * @returns {Promise} Library stats
 */
export const getLibraryStats = async () => {
  try {
    const response = await api.get('/api/v1/library/stats')
    return response.data
  } catch (error) {
    throw error.response?.data || error
  }
}

/**
 * Upload document to library
 * @param {Object} uploadData - Upload data
 * @param {File} uploadData.file - PDF or PPTX file
 * @param {string} uploadData.topic - Document topic
 * @param {string} uploadData.courseId - Course UUID
 * @param {number} uploadData.weekNumber - Week number (1-15)
 * @param {boolean} uploadData.isPublic - Make document public
 * @returns {Promise} Upload result with document ID
 */
export const uploadToLibrary = async (uploadData) => {
  try {
    const formData = new FormData()
    formData.append('file', uploadData.file)
    formData.append('topic', uploadData.topic)
    formData.append('course_id', uploadData.courseId)
    if (uploadData.weekNumber) {
      formData.append('week_number', uploadData.weekNumber)
    }
    formData.append('is_public', uploadData.isPublic ? 'true' : 'false')

    const response = await api.post('/api/v1/smartstudy/library/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    return response.data
  } catch (error) {
    throw error.response?.data || error
  }
}

/**
 * Get user's enrolled courses (alias for getEnrolledCourses)
 * @param {boolean} activeOnly - Only return active courses
 * @returns {Promise} List of courses
 */
export const getMyCourses = async (activeOnly = true) => {
  return getEnrolledCourses(activeOnly)
}

// ============================================
// Video Notes API
// ============================================

/**
 * Create a new video note
 * @param {Object} noteData - Note data
 * @param {string} noteData.resourceId - Resource UUID (the YouTube video resource)
 * @param {string} noteData.content - Note content
 * @param {number} noteData.timestampSeconds - Optional video timestamp in seconds
 * @param {string} noteData.noteType - Type: 'note', 'highlight', 'question', 'summary'
 * @param {string} noteData.color - Color: 'yellow', 'green', 'blue', 'pink', 'orange'
 * @returns {Promise} Created note
 */
export const createVideoNote = async (noteData) => {
  try {
    const response = await api.post('/api/v1/smartstudy/video-notes', {
      resource_id: noteData.resourceId,
      content: noteData.content,
      timestamp_seconds: noteData.timestampSeconds || null,
      note_type: noteData.noteType || 'note',
      color: noteData.color || 'yellow'
    })
    return response.data
  } catch (error) {
    throw error.response?.data || error
  }
}

/**
 * Get all notes for a specific video resource
 * @param {string} resourceId - Resource UUID
 * @returns {Promise} List of notes for the resource
 */
export const getVideoNotes = async (resourceId) => {
  try {
    const response = await api.get(`/api/v1/smartstudy/video-notes/resource/${resourceId}`)
    return response.data
  } catch (error) {
    throw error.response?.data || error
  }
}

/**
 * Update an existing video note
 * @param {string} noteId - Note UUID
 * @param {Object} updateData - Fields to update
 * @param {string} updateData.content - Note content
 * @param {number} updateData.timestampSeconds - Video timestamp in seconds
 * @param {string} updateData.noteType - Type: 'note', 'highlight', 'question', 'summary'
 * @param {string} updateData.color - Color: 'yellow', 'green', 'blue', 'pink', 'orange'
 * @returns {Promise} Updated note
 */
export const updateVideoNote = async (noteId, updateData) => {
  try {
    const response = await api.put(`/api/v1/smartstudy/video-notes/${noteId}`, {
      content: updateData.content,
      timestamp_seconds: updateData.timestampSeconds,
      note_type: updateData.noteType,
      color: updateData.color
    })
    return response.data
  } catch (error) {
    throw error.response?.data || error
  }
}

/**
 * Delete a video note
 * @param {string} noteId - Note UUID
 * @returns {Promise} Success response
 */
export const deleteVideoNote = async (noteId) => {
  try {
    const response = await api.delete(`/api/v1/smartstudy/video-notes/${noteId}`)
    return response.data
  } catch (error) {
    throw error.response?.data || error
  }
}

// ============================================
// SmartStudy - Quizzes API
// ============================================

export const generateQuiz = async (quizData) => {
  try {
    if (quizData.uploadedFile) {
      const formData = new FormData()
      formData.append('uploaded_file', quizData.uploadedFile)
      if (quizData.topic) formData.append('topic', quizData.topic)
      formData.append('quiz_type', quizData.quizType || 'quick_quiz')
      if (quizData.questionCount) formData.append('question_count', quizData.questionCount.toString())
      if (quizData.timeLimitMinutes) formData.append('time_limit_minutes', quizData.timeLimitMinutes.toString())
      formData.append('difficulty_level', quizData.difficultyLevel || 'mixed')
      if (quizData.courseId) formData.append('course_id', quizData.courseId)
      const response = await api.post('/api/v1/smartstudy/quizzes/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      return response.data
    }
    const response = await api.post('/api/v1/smartstudy/quizzes', {
      topic: quizData.topic,
      quiz_type: quizData.quizType || 'quick_quiz',
      question_count: quizData.questionCount || null,
      time_limit_minutes: quizData.timeLimitMinutes || null,
      difficulty_level: quizData.difficultyLevel || 'mixed',
      study_plan_id: quizData.studyPlanId || null,
      course_id: quizData.courseId || null,
    })
    return response.data
  } catch (error) {
    throw error.response?.data || error
  }
}

export const generateQuizFromPlan = async (planId, quizType = 'topic_review', questionCount = null) => {
  try {
    const params = new URLSearchParams()
    params.append('quiz_type', quizType)
    if (questionCount) params.append('question_count', questionCount.toString())
    const response = await api.post(`/api/v1/smartstudy/quizzes/from-plan/${planId}?${params.toString()}`)
    return response.data
  } catch (error) {
    throw error.response?.data || error
  }
}

export const getQuizzes = async (topic = null) => {
  try {
    const params = topic ? `?topic=${encodeURIComponent(topic)}` : ''
    const response = await api.get(`/api/v1/smartstudy/quizzes${params}`)
    return response.data
  } catch (error) {
    throw error.response?.data || error
  }
}

export const getQuiz = async (quizId) => {
  try {
    const response = await api.get(`/api/v1/smartstudy/quizzes/${quizId}`)
    return response.data
  } catch (error) {
    throw error.response?.data || error
  }
}

export const submitQuiz = async (quizId, answers, timeTakenSeconds = null, timedOut = false) => {
  try {
    const response = await api.post(`/api/v1/smartstudy/quizzes/${quizId}/submit`, {
      answers,
      time_taken_seconds: timeTakenSeconds,
      timed_out: timedOut,
    })
    return response.data
  } catch (error) {
    throw error.response?.data || error
  }
}

export const getQuizAttempts = async (quizId) => {
  try {
    const response = await api.get(`/api/v1/smartstudy/quizzes/${quizId}/attempts`)
    return response.data
  } catch (error) {
    throw error.response?.data || error
  }
}

export const createStudyPlanFromQuizGaps = async (quizId) => {
  try {
    const response = await api.post(`/api/v1/smartstudy/quizzes/${quizId}/study-weak-topics`)
    return response.data
  } catch (error) {
    throw error.response?.data || error
  }
}

// ============================================
// Notifications API
// ============================================

/**
 * Get user's notifications
 * @param {Object} options - Query options
 * @param {boolean} options.unreadOnly - Only return unread notifications
 * @param {number} options.limit - Max results
 * @param {number} options.offset - Pagination offset
 * @returns {Promise} Notifications list with counts
 */
export const getNotifications = async (options = {}) => {
  try {
    const params = new URLSearchParams()
    if (options.unreadOnly) params.append('unread_only', 'true')
    if (options.limit) params.append('limit', options.limit)
    if (options.offset) params.append('offset', options.offset)

    const response = await api.get(`/api/v1/notifications?${params.toString()}`)
    return response.data
  } catch (error) {
    throw error.response?.data || error
  }
}

/**
 * Get notification counts for badge display
 * @returns {Promise} Unread and total counts
 */
export const getNotificationCount = async () => {
  try {
    const response = await api.get('/api/v1/notifications/count')
    return response.data
  } catch (error) {
    throw error.response?.data || error
  }
}

/**
 * Mark a notification as read
 * @param {string} notificationId - Notification UUID
 * @returns {Promise} Action result
 */
export const markNotificationRead = async (notificationId) => {
  try {
    const response = await api.post(`/api/v1/notifications/${notificationId}/read`)
    return response.data
  } catch (error) {
    throw error.response?.data || error
  }
}

/**
 * Mark all notifications as read
 * @returns {Promise} Action result
 */
export const markAllNotificationsRead = async () => {
  try {
    const response = await api.post('/api/v1/notifications/read-all')
    return response.data
  } catch (error) {
    throw error.response?.data || error
  }
}

/**
 * Dismiss a notification
 * @param {string} notificationId - Notification UUID
 * @returns {Promise} Action result
 */
export const dismissNotification = async (notificationId) => {
  try {
    const response = await api.post(`/api/v1/notifications/${notificationId}/dismiss`)
    return response.data
  } catch (error) {
    throw error.response?.data || error
  }
}

/**
 * Get user's notification preferences
 * @returns {Promise} Notification preferences
 */
export const getNotificationPreferences = async () => {
  try {
    const response = await api.get('/api/v1/notifications/preferences/me')
    return response.data
  } catch (error) {
    throw error.response?.data || error
  }
}

/**
 * Update notification preferences
 * @param {Object} preferences - Preference updates
 * @returns {Promise} Updated preferences
 */
export const updateNotificationPreferences = async (preferences) => {
  try {
    const response = await api.put('/api/v1/notifications/preferences/me', preferences)
    return response.data
  } catch (error) {
    throw error.response?.data || error
  }
}

/**
 * Create a task reminder
 * @param {string} taskId - Task UUID
 * @param {number} hoursBefore - Hours before due date to remind
 * @returns {Promise} Created notification
 */
export const createTaskReminder = async (taskId, hoursBefore = 24) => {
  try {
    const response = await api.post(`/api/v1/notifications/task/${taskId}/remind?hours_before=${hoursBefore}`)
    return response.data
  } catch (error) {
    throw error.response?.data || error
  }
}

/**
 * Get scheduled reminders
 * @param {boolean} activeOnly - Only return active reminders
 * @returns {Promise} List of scheduled reminders
 */
export const getScheduledReminders = async (activeOnly = true) => {
  try {
    const params = new URLSearchParams()
    if (activeOnly) params.append('active_only', 'true')

    const response = await api.get(`/api/v1/notifications/reminders?${params.toString()}`)
    return response.data
  } catch (error) {
    throw error.response?.data || error
  }
}

/**
 * Create a custom scheduled reminder
 * @param {Object} reminderData - Reminder data
 * @param {string} reminderData.reminderType - Type of reminder
 * @param {string} reminderData.scheduledTime - ISO datetime string
 * @param {boolean} reminderData.isRecurring - Is recurring
 * @param {string} reminderData.recurrencePattern - 'daily', 'weekly', etc.
 * @param {string} reminderData.customTitle - Custom title
 * @param {string} reminderData.customMessage - Custom message
 * @returns {Promise} Created reminder
 */
export const createScheduledReminder = async (reminderData) => {
  try {
    const response = await api.post('/api/v1/notifications/reminders', {
      reminder_type: reminderData.reminderType,
      scheduled_time: reminderData.scheduledTime,
      is_recurring: reminderData.isRecurring || false,
      recurrence_pattern: reminderData.recurrencePattern || null,
      custom_title: reminderData.customTitle || null,
      custom_message: reminderData.customMessage || null
    })
    return response.data
  } catch (error) {
    throw error.response?.data || error
  }
}

/**
 * Delete a scheduled reminder
 * @param {string} reminderId - Reminder UUID
 * @returns {Promise} Action result
 */
export const deleteScheduledReminder = async (reminderId) => {
  try {
    const response = await api.delete(`/api/v1/notifications/reminders/${reminderId}`)
    return response.data
  } catch (error) {
    throw error.response?.data || error
  }
}

// ============================================
// Analytics API
// ============================================

/**
 * Get effectiveness summary
 * @returns {Promise} Summary of SmartStudy effectiveness
 */
export const getEffectivenessSummary = async () => {
  try {
    const response = await api.get('/api/v1/analytics/effectiveness/summary')
    return response.data
  } catch (error) {
    throw error.response?.data || error
  }
}

/**
 * Get effectiveness by learning style
 * @returns {Promise} Breakdown by learning style and resource type
 */
export const getEffectivenessByLearningStyle = async () => {
  try {
    const response = await api.get('/api/v1/analytics/effectiveness/by-learning-style')
    return response.data
  } catch (error) {
    throw error.response?.data || error
  }
}

/**
 * Get effectiveness over time
 * @param {number} days - Number of days to analyze
 * @returns {Promise} Time series data
 */
export const getEffectivenessOverTime = async (days = 30) => {
  try {
    const response = await api.get(`/api/v1/analytics/effectiveness/over-time?days=${days}`)
    return response.data
  } catch (error) {
    throw error.response?.data || error
  }
}

/**
 * Get mood-effectiveness correlation
 * @returns {Promise} Correlation data between mood and study effectiveness
 */
export const getMoodEffectivenessCorrelation = async () => {
  try {
    const response = await api.get('/api/v1/analytics/effectiveness/mood-correlation')
    return response.data
  } catch (error) {
    throw error.response?.data || error
  }
}

/**
 * Get intervention outcomes history
 * @param {number} limit - Max results
 * @returns {Promise} List of intervention outcomes
 */
export const getInterventionOutcomes = async (limit = 20) => {
  try {
    const response = await api.get(`/api/v1/analytics/effectiveness/intervention-outcomes?limit=${limit}`)
    return response.data
  } catch (error) {
    throw error.response?.data || error
  }
}

/**
 * Get topic effectiveness
 * @returns {Promise} Effectiveness metrics by topic
 */
export const getTopicEffectiveness = async () => {
  try {
    const response = await api.get('/api/v1/analytics/effectiveness/topics')
    return response.data
  } catch (error) {
    throw error.response?.data || error
  }
}

/**
 * Get research-grade statistical analysis of SmartStudy intervention effectiveness
 * Computes paired t-test, Cohen's d, 95% CI, and sample adequacy on before/after scores
 * @returns {Promise} Statistical analysis results including descriptive and inferential statistics
 */
export const getStatisticalAnalysis = async () => {
  try {
    const response = await api.get('/api/v1/analytics/effectiveness/statistical-analysis')
    return response.data
  } catch (error) {
    throw error.response?.data || error
  }
}

/**
 * Get OpenAI API cost analysis and projections
 * @returns {Promise} Cost analysis with token usage, estimated costs, and projections
 */
export const getCostAnalysis = async () => {
  const response = await api.get('/api/v1/analytics/cost-analysis')
  return response.data
}

export default api
