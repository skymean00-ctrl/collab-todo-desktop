import { create } from 'zustand'
import { setAuthToken, clearAuthToken } from '../utils/api'

const useAuthStore = create((set) => ({
  user: JSON.parse(localStorage.getItem('user') || 'null'),
  token: localStorage.getItem('access_token') || null,

  login: (user, token, refreshToken) => {
    localStorage.setItem('user', JSON.stringify(user))
    setAuthToken(token)
    if (refreshToken) {
      localStorage.setItem('refresh_token', refreshToken)
    }
    set({ user, token })
  },

  logout: () => {
    clearAuthToken()
    set({ user: null, token: null })
  },

  setVerified: () => {
    set((state) => {
      const updated = { ...state.user, is_verified: true }
      localStorage.setItem('user', JSON.stringify(updated))
      return { user: updated }
    })
  },

  updateProfile: (patch) => {
    set((state) => {
      const updated = { ...state.user, ...patch }
      localStorage.setItem('user', JSON.stringify(updated))
      return { user: updated }
    })
  },
}))

// 세션 만료 이벤트 수신 (api.js에서 발생)
if (typeof window !== 'undefined') {
  window.addEventListener('auth:session-expired', () => {
    useAuthStore.setState({ user: null, token: null })
  })
}

export default useAuthStore
