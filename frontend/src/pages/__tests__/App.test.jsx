import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, it, expect, vi } from 'vitest'

// Mock all page components to avoid complex dependency chains
vi.mock('../HomePage', () => ({ default: () => <div data-testid="home-page">Home</div> }))
vi.mock('../LoginPage', () => ({ default: () => <div data-testid="login-page">Login</div> }))
vi.mock('../RegisterPage', () => ({ default: () => <div data-testid="register-page">Register</div> }))
vi.mock('../DashboardPage', () => ({ default: () => <div data-testid="dashboard-page">Dashboard</div> }))
vi.mock('../CoursesPage', () => ({ default: () => <div data-testid="courses-page">Courses</div> }))
vi.mock('../CGPAPage', () => ({ default: () => <div data-testid="cgpa-page">CGPA</div> }))
vi.mock('../LibraryPage', () => ({ default: () => <div data-testid="library-page">Library</div> }))
vi.mock('../YouTubeTestPage', () => ({ default: () => <div data-testid="youtube-page">YouTube</div> }))

// Mock BrowserRouter so MemoryRouter works
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    BrowserRouter: ({ children }) => <>{children}</>,
  }
})

// Mock AuthContext so ProtectedRoute allows access
vi.mock('../../contexts/AuthContext', () => ({
  useAuth: () => ({
    isAuthenticated: true,
    loading: false,
    user: { full_name: 'Test' },
    token: 'test-token',
  }),
}))

import App from '../../App'

function renderApp(route = '/') {
  return render(
    <MemoryRouter initialEntries={[route]}>
      <App />
    </MemoryRouter>
  )
}

describe('App routing', () => {
  it('renders home page at /', () => {
    renderApp('/')
    expect(screen.getByTestId('home-page')).toBeInTheDocument()
  })

  it('renders login page at /login', () => {
    renderApp('/login')
    expect(screen.getByTestId('login-page')).toBeInTheDocument()
  })

  it('renders register page at /register', () => {
    renderApp('/register')
    expect(screen.getByTestId('register-page')).toBeInTheDocument()
  })

  it('renders dashboard at /dashboard (authenticated)', () => {
    renderApp('/dashboard')
    expect(screen.getByTestId('dashboard-page')).toBeInTheDocument()
  })

  it('renders courses page at /courses (authenticated)', () => {
    renderApp('/courses')
    expect(screen.getByTestId('courses-page')).toBeInTheDocument()
  })

  it('renders CGPA page at /cgpa (authenticated)', () => {
    renderApp('/cgpa')
    expect(screen.getByTestId('cgpa-page')).toBeInTheDocument()
  })

  it('renders library page at /library (authenticated)', () => {
    renderApp('/library')
    expect(screen.getByTestId('library-page')).toBeInTheDocument()
  })
})
