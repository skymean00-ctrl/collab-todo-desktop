import { create } from 'zustand'

const useAuthStore = create((set) => ({
  user: JSON.parse(localStorage.getItem('user') || 'null'),
  token: localStorage.getItem('access_token') || null,

  login: (user, token, refreshToken) => {
    localStorage.setItem('user', JSON.stringify(user))
    localStorage.setItem('access_token', token)
    if (refreshToken) {
      localStorage.setItem('refresh_token', refreshToken)
    }
    set({ user, token })
  },

  logout: () => {
    // 서버에 refresh token 폐기 요청 (best-effort)
    const refreshToken = localStorage.getItem('refresh_token')
    if (refreshToken) {
      import('../utils/api').then(({ default: api }) => {
        api.post('/api/auth/logout', { refresh_token: refreshToken }).catch(() => {})
      })
    }
    localStorage.removeItem('user')
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
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

export default useAuthStore
