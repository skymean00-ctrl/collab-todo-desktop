import { useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../utils/api'

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('')
  const [loading, setLoading] = useState(false)
  const [sent, setSent] = useState(false)
  const [error, setError] = useState('')

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await api.post('/api/auth/forgot-password', { email })
      setSent(true)
    } catch (err) {
      setError(err.response?.data?.detail || '요청에 실패했습니다.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-slate-900">
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-8 w-full max-w-sm">
        <h1 className="text-2xl font-bold text-center text-primary-600 mb-2">비밀번호 찾기</h1>
        <p className="text-center text-sm text-gray-500 dark:text-gray-400 mb-6">
          가입한 이메일 주소를 입력하면 재설정 링크를 보내드립니다.
        </p>

        {sent ? (
          <div className="text-center space-y-4">
            <div className="w-14 h-14 bg-green-100 dark:bg-green-900/30 rounded-full flex items-center justify-center mx-auto">
              <svg className="w-7 h-7 text-green-600 dark:text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <p className="text-sm text-gray-700 dark:text-gray-200">
              입력하신 이메일로 재설정 링크를 발송했습니다.<br />
              메일함을 확인해주세요.
            </p>
            <p className="text-xs text-gray-400 dark:text-gray-500">
              메일이 오지 않으면 스팸함을 확인하거나<br />다시 시도해주세요.
            </p>
            <Link to="/login" className="block w-full text-center bg-primary-600 text-white rounded-lg py-2 text-sm font-medium hover:bg-primary-700 transition mt-2">
              로그인으로 돌아가기
            </Link>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">이메일</label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="가입한 이메일 주소"
                className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
              />
            </div>
            {error && <p className="text-red-500 text-sm">{error}</p>}
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-primary-600 text-white rounded-lg py-2 font-medium hover:bg-primary-700 disabled:opacity-50 transition"
            >
              {loading ? '발송 중...' : '재설정 링크 받기'}
            </button>
          </form>
        )}

        {!sent && (
          <p className="text-center text-sm text-gray-500 dark:text-gray-400 mt-4">
            <Link to="/login" className="text-primary-600 hover:underline">← 로그인으로</Link>
          </p>
        )}
      </div>
    </div>
  )
}
