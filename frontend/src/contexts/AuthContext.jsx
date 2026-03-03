import { createContext, useContext, useState, useEffect } from 'react'
import {
  login as apiLogin,
  register as apiRegister,
  logout as apiLogout,
  getCurrentUser,
  isAuthenticated as checkAuth,
} from '../services/api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [token, setToken] = useState(localStorage.getItem('access_token'))
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Restore user from localStorage on mount
    const savedUser = getCurrentUser()
    if (savedUser && token) {
      setUser(savedUser)
    }
    setLoading(false)
  }, [])

  const login = async (credentials) => {
    const data = await apiLogin(credentials)
    setToken(data.access_token)
    setUser(data.user)
    return data
  }

  const register = async (userData) => {
    const data = await apiRegister(userData)
    setToken(data.access_token)
    setUser(data.user)
    return data
  }

  const logout = () => {
    setUser(null)
    setToken(null)
    apiLogout()
  }

  const isAuthenticated = !!token && !!user

  const value = {
    user,
    token,
    loading,
    login,
    register,
    logout,
    isAuthenticated,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

export default AuthContext
