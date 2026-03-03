import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import ErrorBoundary from './components/ErrorBoundary'
import ProtectedRoute from './components/ProtectedRoute'
import HomePage from './pages/HomePage'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import DashboardPage from './pages/DashboardPage'
import CoursesPage from './pages/CoursesPage'
import CGPAPage from './pages/CGPAPage'
import LibraryPage from './pages/LibraryPage'
import SmartStudyPage from './pages/SmartStudyPage'
import YouTubeTestPage from './pages/YouTubeTestPage'

function App() {
  return (
    <Router>
      <ErrorBoundary>
        <div className="min-h-screen bg-gray-50">
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route path="/dashboard" element={
              <ProtectedRoute><DashboardPage /></ProtectedRoute>
            } />
            <Route path="/courses" element={
              <ProtectedRoute><CoursesPage /></ProtectedRoute>
            } />
            <Route path="/cgpa" element={
              <ProtectedRoute><CGPAPage /></ProtectedRoute>
            } />
            <Route path="/library" element={
              <ProtectedRoute><LibraryPage /></ProtectedRoute>
            } />
            <Route path="/smartstudy" element={
              <ProtectedRoute><ErrorBoundary label="SmartStudy" inline><SmartStudyPage /></ErrorBoundary></ProtectedRoute>
            } />
            <Route path="/youtube-test" element={<YouTubeTestPage />} />
          </Routes>
        </div>
      </ErrorBoundary>
    </Router>
  )
}

export default App
