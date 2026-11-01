import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'

import { ApiError, TOKEN_KEY, api } from '../services/api.js'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [booting, setBooting] = useState(Boolean(localStorage.getItem(TOKEN_KEY)))

  useEffect(() => {
    if (!localStorage.getItem(TOKEN_KEY)) return
    let active = true
    api
      .me()
      .then((profile) => {
        if (active) setUser(profile)
      })
      .catch((error) => {
        if (error instanceof ApiError && error.status === 401) {
          localStorage.removeItem(TOKEN_KEY)
        }
      })
      .finally(() => {
        if (active) setBooting(false)
      })
    return () => {
      active = false
    }
  }, [])

  const login = useCallback(async (email, password) => {
    const data = await api.login({ email, password })
    localStorage.setItem(TOKEN_KEY, data.access_token)
    setUser(data.user)
    return data.user
  }, [])

  const register = useCallback(
    async (name, email, password) => {
      await api.register({ name, email, password })
      return login(email, password)
    },
    [login],
  )

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY)
    setUser(null)
  }, [])

  const value = useMemo(
    () => ({ user, booting, login, register, logout }),
    [user, booting, login, register, logout],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth must be used inside AuthProvider')
  return context
}
