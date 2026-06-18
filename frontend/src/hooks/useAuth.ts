import { create } from 'zustand'
import type { AuthState } from '../types'

interface AuthStore extends AuthState {
  setAuth: (tokens: { accessToken: string; refreshToken: string; userId: string; role: string }) => void
  clearAuth: () => void
  isAuthenticated: () => boolean
}

export const useAuthStore = create<AuthStore>((set, get) => ({
  accessToken: localStorage.getItem('access_token'),
  refreshToken: localStorage.getItem('refresh_token'),
  userId: localStorage.getItem('user_id'),
  role: localStorage.getItem('role') as AuthState['role'],

  setAuth: ({ accessToken, refreshToken, userId, role }) => {
    localStorage.setItem('access_token', accessToken)
    localStorage.setItem('refresh_token', refreshToken)
    localStorage.setItem('user_id', userId)
    localStorage.setItem('role', role)
    set({ accessToken, refreshToken, userId, role: role as AuthState['role'] })
  },

  clearAuth: () => {
    localStorage.clear()
    set({ accessToken: null, refreshToken: null, userId: null, role: null })
  },

  isAuthenticated: () => !!get().accessToken,
}))
