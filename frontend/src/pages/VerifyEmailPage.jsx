import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import api from '../utils/api'
import useAuthStore from '../store/authStore'

export default function VerifyEmailPage() {
  const { token } = useParams()
  const navigate = useNavigate()
  const { setVerified, user } = useAuthStore()
  const [status, setStatus] = useState('loading') // loading | success | error
  const [message, setMessage] = useState('')

  useEffect(() => {
    async function verify() {
      try {
        await api.post(`/api/auth/verify-email/${token}`)
        setVerified()
        setStatus('success')
      } catch (err) {
        setStatus('error')
        setMessage(err.response?.data?.detail || '인증에 실패했습니다.')
      }
    }
    verify()
  }, [token])

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="bg-white rounded-2xl shadow-lg p-10 w-full max-w-md text-center">
        {status === 'loading' && (
          <>
            <div className="w-12 h-12 border-4 border-primary-200 border-t-primary-600 rounded-full animate-spin mx-auto mb-4" />
            <p className="text-gray-600">이메일 인증 중...</p>
          </>
        )}

        {status === 'success' && (
          <>
            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h2 className="text-xl font-bold text-gray-900 mb-2">인증 완료!</h2>
            <p className="text-gray-500 mb-6">이메일 인증이 성공적으로 완료되었습니다.</p>
            <button
              onClick={() => navigate('/')}
              className="bg-primary-600 text-white px-6 py-2.5 rounded-xl font-medium hover:bg-primary-700 transition"
            >
              홈으로 이동
            </button>
          </>
        )}

        {status === 'error' && (
          <>
            <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </div>
            <h2 className="text-xl font-bold text-gray-900 mb-2">인증 실패</h2>
            <p className="text-gray-500 mb-6">{message}</p>
            {user && (
              <ResendButton />
            )}
            <button
              onClick={() => navigate('/')}
              className="mt-3 text-sm text-gray-500 hover:text-gray-700 underline block mx-auto"
            >
              홈으로 이동
            </button>
          </>
        )}
      </div>
    </div>
  )
}

function ResendButton() {
  const [sent, setSent] = useState(false)
  const [loading, setLoading] = useState(false)

  async function resend() {
    setLoading(true)
    try {
      await api.post('/api/auth/resend-verification')
      setSent(true)
    } catch {}
    setLoading(false)
  }

  if (sent) return <p className="text-green-600 text-sm">인증 메일을 재발송했습니다. 메일함을 확인해주세요.</p>

  return (
    <button
      onClick={resend}
      disabled={loading}
      className="bg-primary-600 text-white px-6 py-2.5 rounded-xl font-medium hover:bg-primary-700 disabled:opacity-50 transition"
    >
      {loading ? '발송 중...' : '인증 메일 재발송'}
    </button>
  )
}
