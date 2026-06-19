import { create } from 'zustand'
import type { AuthState } from '../types'

interface AuthStore extends AuthState {
  churchId: string | null
  setAuth: (tokens: { accessToken: string; refreshToken: string; userId: string; role: string }) => void
  setChurchId: (churchId: string) => void
  clearAuth: () => void
  isAuthenticated: () => boolean
}

export const useAuthStore = create<AuthStore>((set, get) => ({
  accessToken: localStorage.getItem('access_token'),
  refreshToken: localStorage.getItem('refresh_token'),
  userId: localStorage.getItem('user_id'),
  role: localStorage.getItem('role') as AuthState['role'],
  churchId: localStorage.getItem('church_id'),

  setAuth: ({ accessToken, refreshToken, userId, role }) => {
    localStorage.setItem('access_token', accessToken)
    localStorage.setItem('refresh_token', refreshToken)
    localStorage.setItem('user_id', userId)
    localStorage.setItem('role', role)
    set({ accessToken, refreshToken, userId, role: role as AuthState['role'] })
  },

  setChurchId: (churchId) => {
    localStorage.setItem('church_id', churchId)
    set({ churchId })
  },

  clearAuth: () => {
    localStorage.clear()
    set({ accessToken: null, refreshToken: null, userId: null, role: null, churchId: null })
  },

  isAuthenticated: () => !!get().accessToken,
}))
