/**
 * Centralized API mock for frontend tests.
 * Import and use vi.mock('../../services/api', ...) in test files.
 */
export const login = vi.fn()
export const register = vi.fn()
export const logout = vi.fn()
export const getCurrentUser = vi.fn()
export const isAuthenticated = vi.fn()
export const fetchCurrentUser = vi.fn()
export const updateUserPreferences = vi.fn()

export const getCourses = vi.fn()
export const getCourseById = vi.fn()
export const enrollInCourse = vi.fn()
export const getEnrolledCourses = vi.fn()
export const getEnrollmentDetails = vi.fn()
export const updateEnrollment = vi.fn()
export const unenrollFromCourse = vi.fn()
export const getMyCourses = vi.fn()

export const getTasks = vi.fn()
export const getTaskStats = vi.fn()
export const getTasksByCourse = vi.fn()
export const getTaskById = vi.fn()
export const createTask = vi.fn()
export const updateTask = vi.fn()
export const completeTask = vi.fn()
export const deleteTask = vi.fn()

export const getCurrentCGPA = vi.fn()

export const sendSmartStudyMessage = vi.fn()
export const getSmartStudyConversations = vi.fn()
export const getSmartStudyConversation = vi.fn()
export const deleteSmartStudyConversation = vi.fn()
export const getSmartStudySuggestedPrompts = vi.fn()
export const getSmartStudyDashboardTrigger = vi.fn()
export const getSmartStudyContext = vi.fn()

export const generateStudyPlan = vi.fn()
export const getStudyPlans = vi.fn()
export const getStudyPlan = vi.fn()
export const updateStudyPlanProgress = vi.fn()
export const trackResourceClick = vi.fn()
export const markResourceComplete = vi.fn()

export const browseLibrary = vi.fn()
export const getLibraryDocument = vi.fn()
export const voteOnDocument = vi.fn()
export const downloadLibraryDocument = vi.fn()
export const getMyContributions = vi.fn()
export const getLibraryStats = vi.fn()
export const uploadToLibrary = vi.fn()

export const getNotifications = vi.fn()
export const getNotificationCount = vi.fn()
export const markNotificationRead = vi.fn()
export const markAllNotificationsRead = vi.fn()
export const dismissNotification = vi.fn()
export const getNotificationPreferences = vi.fn()
export const updateNotificationPreferences = vi.fn()
export const createTaskReminder = vi.fn()
export const getScheduledReminders = vi.fn()
export const createScheduledReminder = vi.fn()
export const deleteScheduledReminder = vi.fn()

export const getEffectivenessSummary = vi.fn()
export const getEffectivenessByLearningStyle = vi.fn()
export const getEffectivenessOverTime = vi.fn()
export const getMoodEffectivenessCorrelation = vi.fn()
export const getInterventionOutcomes = vi.fn()
export const getTopicEffectiveness = vi.fn()

export const createVideoNote = vi.fn()
export const getVideoNotes = vi.fn()
export const updateVideoNote = vi.fn()
export const deleteVideoNote = vi.fn()

const api = {
  get: vi.fn(),
  post: vi.fn(),
  patch: vi.fn(),
  put: vi.fn(),
  delete: vi.fn(),
}
export default api
