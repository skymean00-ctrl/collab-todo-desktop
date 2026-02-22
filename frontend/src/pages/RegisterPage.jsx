import { useState, useEffect } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import api, { getApiBase } from '../utils/api'
import useAuthStore from '../store/authStore'

const PASSWORD_HINT = '8자 이상, 대문자·소문자·숫자·특수문자(!@#$%^&* 등) 포함'

export default function RegisterPage() {
  const navigate = useNavigate()
  const login = useAuthStore((s) => s.login)
  const [form, setForm] = useState({
    email: '',
    password: '',
    passwordConfirm: '',
    name: '',
    department_name: '',
  })
  const [departments, setDepartments] = useState([])
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    // 인증 없이 부서 목록 로드 (DB 기반)
    fetch(`${getApiBase()}/api/users/departments/list`)
      .then((r) => r.json())
      .then((data) => setDepartments(Array.isArray(data) ? data : []))
      .catch(() => setDepartments([]))
  }, [])

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')

    if (!form.department_name) {
      setError('부서를 선택해주세요.')
      return
    }
    if (form.password !== form.passwordConfirm) {
      setError('비밀번호가 일치하지 않습니다.')
      return
    }

    setLoading(true)
    try {
      const { data } = await api.post('/api/auth/register', {
        email: form.email,
        password: form.password,
        name: form.name,
        department_name: form.department_name,
      })

      login(
        {
          id: data.user_id, name: data.name, email: data.email,
          department: data.department, job_title: data.job_title,
          is_admin: data.is_admin, is_verified: data.is_verified,
        },
        data.access_token,
        data.refresh_token,
      )
      navigate('/')
    } catch (err) {
      setError(err.response?.data?.detail || '회원가입에 실패했습니다.')
    } finally {
      setLoading(false)
    }
  }

  const inputCls = 'w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100'

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-slate-900 py-8">
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-8 w-full max-w-sm">
        <h1 className="text-2xl font-bold text-center text-primary-600 mb-2">CollabTodo</h1>
        <p className="text-center text-gray-500 dark:text-gray-400 text-sm mb-6">계정 만들기</p>

        <form onSubmit={handleSubmit} className="space-y-3">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">이름 *</label>
            <input
              required type="text" placeholder="홍길동"
              value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })}
              className={inputCls}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">회사 이메일 *</label>
            <input
              required type="email" placeholder="name@company.com"
              value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })}
              className={inputCls}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">부서 *</label>
            {departments.length > 0 ? (
              <select
                required value={form.department_name}
                onChange={(e) => setForm({ ...form, department_name: e.target.value })}
                className={inputCls}
              >
                <option value="">부서를 선택하세요</option>
                {departments.map((d) => (
                  <option key={d} value={d}>{d}</option>
                ))}
              </select>
            ) : (
              <input
                type="text" placeholder="소속 부서명 입력"
                value={form.department_name}
                onChange={(e) => setForm({ ...form, department_name: e.target.value })}
                className={inputCls}
              />
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">비밀번호 *</label>
            <input
              required type="password" placeholder={PASSWORD_HINT}
              value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })}
              className={inputCls}
            />
            <p className="text-xs text-gray-400 mt-1">{PASSWORD_HINT}</p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">비밀번호 확인 *</label>
            <input
              required type="password" placeholder="비밀번호를 다시 입력"
              value={form.passwordConfirm}
              onChange={(e) => setForm({ ...form, passwordConfirm: e.target.value })}
              className={inputCls}
            />
          </div>

          {error && <p className="text-red-500 text-sm">{error}</p>}

          <button
            type="submit" disabled={loading}
            className="w-full bg-primary-600 text-white rounded-lg py-2.5 font-medium hover:bg-primary-700 disabled:opacity-50 transition mt-2"
          >
            {loading ? '처리 중...' : '가입하기'}
          </button>
        </form>

        <p className="text-center text-sm text-gray-500 dark:text-gray-400 mt-4">
          이미 계정이 있으신가요?{' '}
          <Link to="/login" className="text-primary-600 hover:underline">로그인</Link>
        </p>
      </div>
    </div>
  )
}
