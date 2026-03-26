import { lazy, Suspense } from 'react'
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom'
import ErrorBoundary from './components/ErrorBoundary'
import ProtectedRoute from './components/ProtectedRoute'
import HomePage from './pages/HomePage'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import GlobalProcessIndicator from './components/GlobalProcessIndicator'

const DashboardPage = lazy(() => import('./pages/DashboardPage'))
const CoursesPage = lazy(() => import('./pages/CoursesPage'))
const CGPAPage = lazy(() => import('./pages/CGPAPage'))
const LibraryPage = lazy(() => import('./pages/LibraryPage'))
const SmartStudyPage = lazy(() => import('./pages/SmartStudyPage'))
const ForgotPasswordPage = lazy(() => import('./pages/ForgotPasswordPage'))
const ResetPasswordPage = lazy(() => import('./pages/ResetPasswordPage'))
const EmailVerificationPage = lazy(() => import('./pages/EmailVerificationPage'))
const ProfilePage = lazy(() => import('./pages/ProfilePage'))

function LoadingSpinner() {
  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
    </div>
  )
}

function NotFoundPage() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gray-50">
      <h1 className="text-4xl font-bold text-gray-800 mb-4">404</h1>
      <p className="text-gray-600 mb-6">Page not found</p>
      <Link to="/dashboard" className="text-indigo-600 hover:text-indigo-800 font-medium">
        Go to Dashboard
      </Link>
    </div>
  )
}

function App() {
  return (
    <Router>
      <ErrorBoundary>
        <div className="min-h-screen bg-gray-50">
          <GlobalProcessIndicator />
          <Suspense fallback={<LoadingSpinner />}>
            <Routes>
              <Route path="/" element={<HomePage />} />
              <Route path="/login" element={<LoginPage />} />
              <Route path="/register" element={<RegisterPage />} />
              <Route path="/forgot-password" element={<ForgotPasswordPage />} />
              <Route path="/reset-password" element={<ResetPasswordPage />} />
              <Route path="/verify-email/:token" element={<EmailVerificationPage />} />
              <Route path="/dashboard" element={
                <ProtectedRoute><ErrorBoundary label="Dashboard" inline><DashboardPage /></ErrorBoundary></ProtectedRoute>
              } />
              <Route path="/courses" element={
                <ProtectedRoute><ErrorBoundary label="Courses" inline><CoursesPage /></ErrorBoundary></ProtectedRoute>
              } />
              <Route path="/cgpa" element={
                <ProtectedRoute><ErrorBoundary label="CGPA" inline><CGPAPage /></ErrorBoundary></ProtectedRoute>
              } />
              <Route path="/library" element={
                <ProtectedRoute><ErrorBoundary label="Library" inline><LibraryPage /></ErrorBoundary></ProtectedRoute>
              } />
              <Route path="/smartstudy" element={
                <ProtectedRoute><ErrorBoundary label="SmartStudy" inline><SmartStudyPage /></ErrorBoundary></ProtectedRoute>
              } />
              <Route path="/profile" element={
                <ProtectedRoute><ErrorBoundary label="Profile" inline><ProfilePage /></ErrorBoundary></ProtectedRoute>
              } />
              <Route path="*" element={<NotFoundPage />} />
            </Routes>
          </Suspense>
        </div>
      </ErrorBoundary>
    </Router>
  )
}

export default App
