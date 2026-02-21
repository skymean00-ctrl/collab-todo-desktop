import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../utils/api'
import useAuthStore from '../store/authStore'

export default function AdminPage() {
  const { user } = useAuthStore()
  const navigate = useNavigate()
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [confirmDelete, setConfirmDelete] = useState(null) // user 객체

  useEffect(() => {
    if (!user?.is_admin) {
      navigate('/')
      return
    }
    loadUsers()
  }, [])

  async function loadUsers() {
    setLoading(true)
    try {
      const { data } = await api.get('/api/admin/users')
      setUsers(data)
    } finally {
      setLoading(false)
    }
  }

  async function handleDelete(u) {
    await api.delete(`/api/admin/users/${u.id}`)
    setConfirmDelete(null)
    loadUsers()
  }

  async function handleToggleAdmin(u) {
    await api.patch(`/api/admin/users/${u.id}/toggle-admin`)
    loadUsers()
  }

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <div className="flex items-center gap-3 mb-6">
        <button onClick={() => navigate('/')} className="text-sm text-gray-500 hover:text-gray-700">
          ← 홈
        </button>
        <h1 className="text-xl font-bold text-gray-900">사용자 관리</h1>
        <span className="bg-primary-100 text-primary-700 text-xs px-2 py-0.5 rounded-full font-medium">관리자</span>
      </div>

      <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
        {loading ? (
          <div className="py-16 text-center text-gray-400 text-sm">불러오는 중...</div>
        ) : (
          <table className="w-full">
            <thead className="bg-gray-50 text-xs text-gray-500 uppercase tracking-wide">
              <tr>
                <th className="py-3 px-4 text-left">이름</th>
                <th className="py-3 px-4 text-left">이메일</th>
                <th className="py-3 px-4 text-left">부서 · 직급</th>
                <th className="py-3 px-4 text-left">상태</th>
                <th className="py-3 px-4 text-left">가입일</th>
                <th className="py-3 px-4 text-center">관리</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id} className="border-t border-gray-100 hover:bg-gray-50">
                  <td className="py-3 px-4">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-sm text-gray-800">{u.name}</span>
                      {u.is_admin && (
                        <span className="text-xs bg-primary-100 text-primary-700 px-1.5 py-0.5 rounded">관리자</span>
                      )}
                      {u.id === user.id && (
                        <span className="text-xs bg-gray-100 text-gray-500 px-1.5 py-0.5 rounded">나</span>
                      )}
                    </div>
                  </td>
                  <td className="py-3 px-4 text-sm text-gray-600">{u.email}</td>
                  <td className="py-3 px-4 text-sm text-gray-600">
                    {u.department && <span>{u.department} · </span>}
                    {u.job_title}
                  </td>
                  <td className="py-3 px-4">
                    <div className="flex flex-col gap-1">
                      <span className={`text-xs px-2 py-0.5 rounded-full w-fit ${
                        u.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'
                      }`}>
                        {u.is_active ? '활성' : '비활성'}
                      </span>
                      <span className={`text-xs px-2 py-0.5 rounded-full w-fit ${
                        u.is_verified ? 'bg-blue-100 text-blue-700' : 'bg-amber-100 text-amber-700'
                      }`}>
                        {u.is_verified ? '이메일 인증됨' : '인증 대기'}
                      </span>
                    </div>
                  </td>
                  <td className="py-3 px-4 text-xs text-gray-400">
                    {u.created_at ? new Date(u.created_at).toLocaleDateString('ko-KR') : '-'}
                  </td>
                  <td className="py-3 px-4">
                    {u.id !== user.id && u.is_active && (
                      <div className="flex items-center justify-center gap-2">
                        <button
                          onClick={() => handleToggleAdmin(u)}
                          className="text-xs text-primary-600 hover:text-primary-800 font-medium"
                        >
                          {u.is_admin ? '관리자 해제' : '관리자 지정'}
                        </button>
                        <span className="text-gray-200">|</span>
                        <button
                          onClick={() => setConfirmDelete(u)}
                          className="text-xs text-red-500 hover:text-red-700 font-medium"
                        >
                          삭제
                        </button>
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <p className="text-xs text-gray-400 mt-3">
        * 삭제 시 계정이 비활성화됩니다. 업무 이력은 보존됩니다.
      </p>

      {/* 삭제 확인 모달 */}
      {confirmDelete && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white rounded-2xl shadow-xl p-6 w-80">
            <h3 className="font-bold text-gray-900 mb-2">계정 삭제 확인</h3>
            <p className="text-sm text-gray-600 mb-4">
              <b>{confirmDelete.name}</b> ({confirmDelete.email}) 계정을 비활성화하시겠습니까?
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => setConfirmDelete(null)}
                className="flex-1 py-2 border border-gray-300 rounded-lg text-sm hover:bg-gray-50"
              >
                취소
              </button>
              <button
                onClick={() => handleDelete(confirmDelete)}
                className="flex-1 py-2 bg-red-600 text-white rounded-lg text-sm font-medium hover:bg-red-700"
              >
                삭제
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
