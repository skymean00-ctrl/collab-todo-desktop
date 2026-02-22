import axios from 'axios'

export function getApiBase() {
  const isElectron = !!window.electronAPI
  if (!isElectron) {
    return window.location.origin
  }
  return localStorage.getItem('server_url') || import.meta.env.VITE_API_URL || 'http://localhost:8000'
}

const api = axios.create({
  timeout: 15000, // 15초 타임아웃
})

// 요청마다 최신 서버 URL + 인증 토큰 적용
api.interceptors.request.use((config) => {
  config.baseURL = getApiBase()
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

let _refreshing = false
let _refreshQueue = []

// 401 → Refresh Token으로 재발급 시도, 실패 시 로그인 페이지
api.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config

    if (error.response?.status === 401 && !original._retried) {
      const refreshToken = localStorage.getItem('refresh_token')
      if (!refreshToken) {
        _clearAndRedirect()
        return Promise.reject(error)
      }

      if (_refreshing) {
        // 이미 갱신 중이면 대기 후 재시도
        return new Promise((resolve, reject) => {
          _refreshQueue.push({ resolve, reject })
        }).then((token) => {
          original.headers.Authorization = `Bearer ${token}`
          return api(original)
        })
      }

      _refreshing = true
      original._retried = true

      try {
        const { data } = await axios.post(
          `${getApiBase()}/api/auth/refresh`,
          { refresh_token: refreshToken },
          { timeout: 10000 },
        )
        localStorage.setItem('access_token', data.access_token)
        localStorage.setItem('refresh_token', data.refresh_token)

        // 대기 중인 요청들 재시도
        _refreshQueue.forEach(({ resolve }) => resolve(data.access_token))
        _refreshQueue = []

        original.headers.Authorization = `Bearer ${data.access_token}`
        return api(original)
      } catch (refreshErr) {
        _refreshQueue.forEach(({ reject }) => reject(refreshErr))
        _refreshQueue = []
        _clearAndRedirect()
        return Promise.reject(refreshErr)
      } finally {
        _refreshing = false
      }
    }

    return Promise.reject(error)
  },
)

function _clearAndRedirect() {
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
  localStorage.removeItem('user')
  window.location.hash = '#/login'
}

export default api
