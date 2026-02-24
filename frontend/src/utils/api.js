import axios from 'axios'

export function getApiBase() {
  const isElectron = !!window.electronAPI
  if (!isElectron) {
    return window.location.origin
  }
  return localStorage.getItem('server_url') || import.meta.env.VITE_API_URL || 'http://localhost:8000'
}

const api = axios.create({
  timeout: 15000,
})

// ── 토큰 관리 ───────────────────────────────────────────
// Axios defaults.headers에 직접 설정 (인터셉터 의존 제거)
function _applyToken(token) {
  if (token) {
    api.defaults.headers.common['Authorization'] = `Bearer ${token}`
  } else {
    delete api.defaults.headers.common['Authorization']
  }
}

// 앱 시작 시 저장된 토큰 적용
_applyToken(localStorage.getItem('access_token'))

// 로그인 시 호출
export function setAuthToken(token) {
  localStorage.setItem('access_token', token)
  _applyToken(token)
}

// 로그아웃 시 호출
export function clearAuthToken() {
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
  localStorage.removeItem('user')
  _applyToken(null)
}

// ── 요청: baseURL 설정 ──────────────────────────────────
api.interceptors.request.use((config) => {
  config.baseURL = getApiBase()
  return config
})

// ── 응답: 401이면 로그인 페이지로 (한번만) ──────────────
let _redirecting = false

api.interceptors.response.use(
  (res) => res,
  (error) => {
    if (error.response?.status === 401 && !_redirecting) {
      const url = error.config?.url || ''
      if (!url.includes('/api/auth/login') && !url.includes('/api/auth/register')) {
        _redirecting = true
        clearAuthToken()
        window.dispatchEvent(new Event('auth:session-expired'))
        window.location.hash = '#/login'
        setTimeout(() => { _redirecting = false }, 2000)
      }
    }
    return Promise.reject(error)
  },
)

export default api
