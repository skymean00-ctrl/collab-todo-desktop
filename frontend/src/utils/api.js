import axios from 'axios'

// 브라우저 접속(폰 등) 시: 현재 접속 origin이 곧 서버 URL
// Electron 앱: 저장된 server_url 사용
export function getApiBase() {
  const isElectron = !!window.electronAPI
  if (!isElectron) {
    // 브라우저 접속 → origin 자체가 서버 (nginx가 /api/ 프록시)
    return window.location.origin
  }
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
