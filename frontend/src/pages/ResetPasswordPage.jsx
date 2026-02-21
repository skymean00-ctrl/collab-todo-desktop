import { useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import api from '../utils/api'

export default function ResetPasswordPage() {
  const { token } = useParams()
  const navigate = useNavigate()
  const [form, setForm] = useState({ new_password: '', confirm: '' })
  const [loading, setLoading] = useState(false)
  const [success, setSuccess] = useState(false)
  const [error, setError] = useState('')

  async function handleSubmit(e) {
    e.preventDefault()
    if (form.new_password !== form.confirm) {
      setError('비밀번호가 일치하지 않습니다.')
      return
    }
    if (form.new_password.length < 6) {
      setError('비밀번호는 6자 이상이어야 합니다.')
      return
    }
    setError('')
    setLoading(true)
    try {
      await api.post('/api/auth/reset-password', { token, new_password: form.new_password })
      setSuccess(true)
    } catch (err) {
      setError(err.response?.data?.detail || '재설정에 실패했습니다. 링크가 만료되었을 수 있습니다.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-slate-900">
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-8 w-full max-w-sm">
        <h1 className="text-2xl font-bold text-center text-primary-600 mb-6">새 비밀번호 설정</h1>

        {success ? (
          <div className="text-center space-y-4">
            <div className="w-14 h-14 bg-green-100 dark:bg-green-900/30 rounded-full flex items-center justify-center mx-auto">
              <svg className="w-7 h-7 text-green-600 dark:text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <p className="text-sm text-gray-700 dark:text-gray-200 font-medium">비밀번호가 재설정되었습니다.</p>
            <button
              onClick={() => navigate('/login')}
              className="w-full bg-primary-600 text-white rounded-lg py-2 text-sm font-medium hover:bg-primary-700 transition"
            >
              로그인하기
            </button>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">새 비밀번호 (6자 이상)</label>
              <input
                type="password"
                required
                value={form.new_password}
                onChange={(e) => setForm({ ...form, new_password: e.target.value })}
                className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">새 비밀번호 확인</label>
              <input
                type="password"
                required
                value={form.confirm}
                onChange={(e) => setForm({ ...form, confirm: e.target.value })}
                className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
              />
            </div>
            {error && <p className="text-red-500 text-sm">{error}</p>}
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-primary-600 text-white rounded-lg py-2 font-medium hover:bg-primary-700 disabled:opacity-50 transition"
            >
              {loading ? '처리 중...' : '비밀번호 변경'}
            </button>
          </form>
        )}

        {!success && (
          <p className="text-center text-sm text-gray-500 dark:text-gray-400 mt-4">
            <Link to="/login" className="text-primary-600 hover:underline">← 로그인으로</Link>
          </p>
        )}
      </div>
    </div>
  )
}
