import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import api from '../utils/api'
import useAuthStore from '../store/authStore'

export default function RegisterPage() {
  const navigate = useNavigate()
  const login = useAuthStore((s) => s.login)
  const [form, setForm] = useState({
    email: '',
    password: '',
    passwordConfirm: '',
    name: '',
    department_name: '',
    job_title: '',
  })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')

    if (form.password !== form.passwordConfirm) {
      setError('비밀번호가 일치하지 않습니다.')
      return
    }
    if (form.password.length < 6) {
      setError('비밀번호는 6자 이상이어야 합니다.')
      return
    }

    setLoading(true)
    try {
      const { data } = await api.post('/api/auth/register', {
        email: form.email,
        password: form.password,
        name: form.name,
        department_name: form.department_name,
        job_title: form.job_title,
      })

      // 가입 즉시 자동 로그인
      login(
        {
          id: data.user_id,
          name: data.name,
          email: data.email,
          department: data.department,
          job_title: data.job_title,
          is_admin: data.is_admin,
          is_verified: data.is_verified,
        },
        data.access_token
      )
      navigate('/')
    } catch (err) {
      setError(err.response?.data?.detail || '회원가입에 실패했습니다.')
    } finally {
      setLoading(false)
    }
  }

  const field = (key, type = 'text', placeholder = '') => ({
    type,
    value: form[key],
    placeholder,
    onChange: (e) => setForm({ ...form, [key]: e.target.value }),
    className:
      'w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500',
  })

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-8">
      <div className="bg-white rounded-2xl shadow-lg p-8 w-full max-w-sm">
        <h1 className="text-2xl font-bold text-center text-primary-600 mb-2">CollabTodo</h1>
        <p className="text-center text-gray-500 text-sm mb-6">계정 만들기</p>

        <form onSubmit={handleSubmit} className="space-y-3">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">이름 *</label>
            <input required {...field('name', 'text', '홍길동')} />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">회사 이메일 *</label>
            <input required {...field('email', 'email', 'name@company.com')} />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">부서 *</label>
              <input required {...field('department_name', 'text', '개발팀')} />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">직급 *</label>
              <input required {...field('job_title', 'text', '과장')} />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">비밀번호 *</label>
            <input required {...field('password', 'password', '6자 이상')} />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">비밀번호 확인 *</label>
            <input required {...field('passwordConfirm', 'password', '비밀번호를 다시 입력')} />
          </div>

          {error && <p className="text-red-500 text-sm">{error}</p>}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-primary-600 text-white rounded-lg py-2.5 font-medium hover:bg-primary-700 disabled:opacity-50 transition mt-2"
          >
            {loading ? '처리 중...' : '가입하기'}
          </button>
        </form>

        <p className="text-center text-sm text-gray-500 mt-4">
          이미 계정이 있으신가요?{' '}
          <Link to="/login" className="text-primary-600 hover:underline">
            로그인
          </Link>
        </p>
      </div>
    </div>
  )
}
