import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import axios from 'axios'

export default function SetupPage() {
  const navigate = useNavigate()
  const [url, setUrl] = useState('http://')
  const [testing, setTesting] = useState(false)
  const [status, setStatus] = useState(null) // null | 'ok' | 'error'
  const [errorMsg, setErrorMsg] = useState('')

  async function testConnection(targetUrl) {
    setTesting(true)
    setStatus(null)
    setErrorMsg('')
    try {
      const res = await axios.get(`${targetUrl}/health`, { timeout: 5000 })
      if (res.data?.status === 'ok') {
        setStatus('ok')
        return true
      } else {
        setStatus('error')
        setErrorMsg('서버 응답이 올바르지 않습니다.')
        return false
      }
    } catch {
      setStatus('error')
      setErrorMsg('서버에 연결할 수 없습니다. 주소와 서버 상태를 확인해주세요.')
      return false
    } finally {
      setTesting(false)
    }
  }

  async function handleSave() {
    const trimmed = url.replace(/\/$/, '') // 끝 슬래시 제거
    const ok = await testConnection(trimmed)
    if (!ok) return

    // Electron 환경: config 파일에 저장
    if (window.electronAPI?.setServerUrl) {
      await window.electronAPI.setServerUrl(trimmed)
    }
    // 브라우저 환경도 대비
    localStorage.setItem('server_url', trimmed)
    navigate('/login')
  }

  async function handleTest() {
    const trimmed = url.replace(/\/$/, '')
    await testConnection(trimmed)
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="bg-white rounded-2xl shadow-lg p-8 w-full max-w-md">
        {/* 헤더 */}
        <div className="text-center mb-8">
          <div className="w-16 h-16 bg-primary-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M5 12h14M12 5l7 7-7 7" />
            </svg>
          </div>
          <h1 className="text-2xl font-bold text-gray-900">CollabTodo 설정</h1>
          <p className="text-gray-500 text-sm mt-1">처음 한 번만 설정하면 됩니다</p>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              서버 주소
            </label>
            <input
              type="text"
              value={url}
              onChange={(e) => { setUrl(e.target.value); setStatus(null) }}
              placeholder="http://192.168.0.10:8000"
              className="w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm text-gray-900 bg-white focus:outline-none focus:ring-2 focus:ring-primary-500 font-mono"
            />
            <p className="text-xs text-gray-400 mt-1">
              관리자에게 받은 서버 주소를 입력하세요.
            </p>
          </div>

          {/* 연결 상태 */}
          {status === 'ok' && (
            <div className="flex items-center gap-2 text-green-700 bg-green-50 rounded-lg px-3 py-2 text-sm">
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
              서버 연결 성공
            </div>
          )}
          {status === 'error' && (
            <div className="flex items-start gap-2 text-red-700 bg-red-50 rounded-lg px-3 py-2 text-sm">
              <svg className="w-4 h-4 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
              {errorMsg}
            </div>
          )}

          {/* 안내 */}
          <div className="bg-gray-50 rounded-lg p-3 text-xs text-gray-500 space-y-1">
            <p className="font-medium text-gray-600">주소 예시</p>
            <p>• 사내망: <span className="font-mono">http://192.168.1.100:8000</span></p>
            <p>• 외부 서버: <span className="font-mono">http://서버도메인:8000</span></p>
          </div>

          <div className="flex gap-3">
            <button
              onClick={handleTest}
              disabled={testing || !url || url === 'http://'}
              className="flex-1 py-2.5 border border-gray-300 rounded-lg text-sm font-medium hover:bg-gray-50 disabled:opacity-50 transition"
            >
              {testing ? '연결 확인 중...' : '연결 테스트'}
            </button>
            <button
              onClick={handleSave}
              disabled={testing || !url || url === 'http://'}
              className="flex-1 py-2.5 bg-primary-600 text-white rounded-lg text-sm font-medium hover:bg-primary-700 disabled:opacity-50 transition"
            >
              저장 후 시작
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
