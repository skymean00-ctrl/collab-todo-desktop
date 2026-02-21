import axios from 'axios'

// Electron 저장값 → localStorage → 환경변수 순서로 서버 URL 결정
export function getApiBase() {
  return localStorage.getItem('server_url') || import.meta.env.VITE_API_URL || 'http://localhost:8000'
}

const api = axios.create()

// 요청마다 최신 서버 URL + 인증 토큰 적용
api.interceptors.request.use((config) => {
  config.baseURL = getApiBase()
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 401 → 로그인 페이지로
api.interceptors.response.use(
  (res) => res,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token')
      localStorage.removeItem('user')
      window.location.hash = '#/login'
    }
    return Promise.reject(error)
  }
)

export default api
