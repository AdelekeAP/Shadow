/**
 * API Service for Shadow Frontend
 * Handles all HTTP requests to the backend
 */
import axios from 'axios'

// API base URL
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001'

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

export default api
