import { create } from 'zustand'

const useAuthStore = create((set) => ({
  user: JSON.parse(localStorage.getItem('user') || 'null'),
  token: localStorage.getItem('access_token') || null,

  login: (user, token) => {
    localStorage.setItem('user', JSON.stringify(user))
    localStorage.setItem('access_token', token)
    set({ user, token })
  },

  logout: () => {
    localStorage.removeItem('user')
    localStorage.removeItem('access_token')
    set({ user: null, token: null })
  },

  // 인증 완료 후 로컬 상태 업데이트
  setVerified: () => {
    set((state) => {
      const updated = { ...state.user, is_verified: true }
      localStorage.setItem('user', JSON.stringify(updated))
      return { user: updated }
    })
  },
}))

export default useAuthStore
