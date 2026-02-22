import { useState } from 'react'
import api from '../utils/api'
import useAuthStore from '../store/authStore'

export default function VerificationBanner() {
  const user = useAuthStore((s) => s.user)
  const [sent, setSent] = useState(false)
  const [loading, setLoading] = useState(false)

  if (!user || user.is_verified) return null

  async function resend() {
    setLoading(true)
    try {
      await api.post('/api/auth/resend-verification')
      setSent(true)
    } catch {}
    setLoading(false)
  }

  return (
    <div className="bg-amber-50 dark:bg-amber-900/20 border-b border-amber-200 dark:border-amber-800 px-4 py-2.5 flex items-center justify-between text-sm flex-shrink-0">
      <div className="flex items-center gap-2">
        <svg className="w-4 h-4 text-amber-500 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
        </svg>
        <span className="text-amber-800 dark:text-amber-300">
          이메일 인증이 완료되지 않았습니다. <b>{user.email}</b>으로 발송된 인증 메일을 확인해주세요.
        </span>
      </div>
      {sent ? (
        <span className="text-green-700 dark:text-green-400 font-medium ml-4 flex-shrink-0">재발송 완료</span>
      ) : (
        <button
          onClick={resend}
          disabled={loading}
          className="ml-4 flex-shrink-0 text-amber-700 dark:text-amber-400 underline hover:text-amber-900 dark:hover:text-amber-200 font-medium disabled:opacity-50"
        >
          {loading ? '발송 중...' : '인증 메일 재발송'}
        </button>
      )}
    </div>
  )
}
