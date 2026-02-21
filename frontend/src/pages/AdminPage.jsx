import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../utils/api'
import useAuthStore from '../store/authStore'

export default function AdminPage() {
  const { user } = useAuthStore()
  const navigate = useNavigate()
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [confirmDelete, setConfirmDelete] = useState(null)

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

  async function handleActivate(u) {
    await api.patch(`/api/admin/users/${u.id}/activate`)
    loadUsers()
  }

  async function handleToggleAdmin(u) {
    await api.patch(`/api/admin/users/${u.id}/toggle-admin`)
    loadUsers()
  }

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <div className="flex items-center gap-3 mb-6">
        <button onClick={() => navigate('/')} className="text-sm text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200">
          ← 홈
        </button>
        <h1 className="text-xl font-bold text-gray-900 dark:text-gray-100">사용자 관리</h1>
        <span className="bg-primary-100 dark:bg-primary-900/40 text-primary-700 dark:text-primary-300 text-xs px-2 py-0.5 rounded-full font-medium">관리자</span>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
        {loading ? (
          <div className="py-16 text-center text-gray-400 text-sm">불러오는 중...</div>
        ) : (
          <table className="w-full">
            <thead className="bg-gray-50 dark:bg-gray-700 text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wide">
              <tr>
                <th className="py-3 px-4 text-left">이름</th>
                <th className="py-3 px-4 text-left">이메일</th>
                <th className="py-3 px-4 text-left">부서</th>
                <th className="py-3 px-4 text-left">상태</th>
                <th className="py-3 px-4 text-left">가입일</th>
                <th className="py-3 px-4 text-center">관리</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id} className="border-t border-gray-100 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700">
                  <td className="py-3 px-4">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-sm text-gray-800 dark:text-gray-100">{u.name}</span>
                      {u.is_admin && (
                        <span className="text-xs bg-primary-100 dark:bg-primary-900/40 text-primary-700 dark:text-primary-300 px-1.5 py-0.5 rounded">관리자</span>
                      )}
                      {u.id === user.id && (
                        <span className="text-xs bg-gray-100 dark:bg-gray-600 text-gray-500 dark:text-gray-300 px-1.5 py-0.5 rounded">나</span>
                      )}
                    </div>
                  </td>
                  <td className="py-3 px-4 text-sm text-gray-600 dark:text-gray-300">{u.email}</td>
                  <td className="py-3 px-4 text-sm text-gray-600 dark:text-gray-300">
                    {u.department || '-'}
                  </td>
                  <td className="py-3 px-4">
                    <div className="flex flex-col gap-1">
                      <span className={`text-xs px-2 py-0.5 rounded-full w-fit ${
                        u.is_active ? 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-400' : 'bg-gray-100 text-gray-500 dark:bg-gray-700 dark:text-gray-400'
                      }`}>
                        {u.is_active ? '활성' : '비활성'}
                      </span>
                      <span className={`text-xs px-2 py-0.5 rounded-full w-fit ${
                        u.is_verified ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-400' : 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-400'
                      }`}>
                        {u.is_verified ? '이메일 인증됨' : '인증 대기'}
                      </span>
                    </div>
                  </td>
                  <td className="py-3 px-4 text-xs text-gray-400 dark:text-gray-500">
                    {u.created_at ? new Date(u.created_at).toLocaleDateString('ko-KR') : '-'}
                  </td>
                  <td className="py-3 px-4">
                    {u.id !== user.id && (
                      <div className="flex items-center justify-center gap-2">
                        {u.is_active ? (
                          <>
                            <button
                              onClick={() => handleToggleAdmin(u)}
                              className="text-xs text-primary-600 dark:text-primary-400 hover:text-primary-800 dark:hover:text-primary-200 font-medium"
                            >
                              {u.is_admin ? '관리자 해제' : '관리자 지정'}
                            </button>
                            <span className="text-gray-200 dark:text-gray-600">|</span>
                            <button
                              onClick={() => setConfirmDelete(u)}
                              className="text-xs text-red-500 hover:text-red-700 font-medium"
                            >
                              비활성화
                            </button>
                          </>
                        ) : (
                          <button
                            onClick={() => handleActivate(u)}
                            className="text-xs text-green-600 dark:text-green-400 hover:text-green-800 dark:hover:text-green-200 font-medium"
                          >
                            재활성화
                          </button>
                        )}
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <p className="text-xs text-gray-400 dark:text-gray-500 mt-3">
        * 비활성화 시 계정이 잠기며 업무 이력은 보존됩니다. 언제든 재활성화할 수 있습니다.
      </p>

      {/* 비활성화 확인 모달 */}
      {confirmDelete && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl p-6 w-80">
            <h3 className="font-bold text-gray-900 dark:text-gray-100 mb-2">계정 비활성화 확인</h3>
            <p className="text-sm text-gray-600 dark:text-gray-300 mb-4">
              <b>{confirmDelete.name}</b> ({confirmDelete.email}) 계정을 비활성화하시겠습니까?
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => setConfirmDelete(null)}
                className="flex-1 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700"
              >
                취소
              </button>
              <button
                onClick={() => handleDelete(confirmDelete)}
                className="flex-1 py-2 bg-red-600 text-white rounded-lg text-sm font-medium hover:bg-red-700"
              >
                비활성화
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
