import { createSlice, PayloadAction } from '@reduxjs/toolkit'
import type { AuthState, User } from '@/types'

// Load from localStorage
const loadAuthFromStorage = (): Partial<AuthState> => {
  try {
    const accessToken = localStorage.getItem('access_token')
    const refreshToken = localStorage.getItem('refresh_token')
    const userStr = localStorage.getItem('user')
    const user = userStr ? JSON.parse(userStr) : null

    return {
      accessToken,
      refreshToken,
      user,
      isAuthenticated: !!accessToken && !!user,
    }
  } catch (error) {
    console.error('Error loading auth from storage:', error)
    return {}
  }
}

const initialState: AuthState = {
  user: null,
  accessToken: null,
  refreshToken: null,
  isAuthenticated: false,
  isLoading: false,
  error: null,
  ...loadAuthFromStorage(),
}

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    setLoading(state, action: PayloadAction<boolean>) {
      state.isLoading = action.payload
      state.error = null
    },
    setError(state, action: PayloadAction<string>) {
      state.error = action.payload
      state.isLoading = false
    },
    loginSuccess(
      state,
      action: PayloadAction<{ accessToken: string; refreshToken: string; user: User }>
    ) {
      const { accessToken, refreshToken, user } = action.payload

      state.accessToken = accessToken
      state.refreshToken = refreshToken
      state.user = user
      state.isAuthenticated = true
      state.isLoading = false
      state.error = null

      // Save to localStorage
      localStorage.setItem('access_token', accessToken)
      localStorage.setItem('refresh_token', refreshToken)
      localStorage.setItem('user', JSON.stringify(user))
    },
    logout(state) {
      state.user = null
      state.accessToken = null
      state.refreshToken = null
      state.isAuthenticated = false
      state.isLoading = false
      state.error = null

      // Clear localStorage
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('user')
    },
    updateTokens(state, action: PayloadAction<{ accessToken: string; refreshToken: string }>) {
      const { accessToken, refreshToken } = action.payload
      state.accessToken = accessToken
      state.refreshToken = refreshToken

      // Update localStorage
      localStorage.setItem('access_token', accessToken)
      localStorage.setItem('refresh_token', refreshToken)
    },
  },
})

export const { setLoading, setError, loginSuccess, logout, updateTokens } = authSlice.actions
export default authSlice.reducer
