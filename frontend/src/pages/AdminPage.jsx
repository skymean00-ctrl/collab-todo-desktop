import { useState, useEffect } from 'react'
import api from '../utils/api'
import useAuthStore from '../store/authStore'

const TABS = [
  { key: 'users', label: '사용자 관리' },
  { key: 'departments', label: '부서 관리' },
  { key: 'stats', label: '전체 통계' },
  { key: 'announcement', label: '공지 발송' },
  { key: 'bug_reports', label: '🐛 오류 접수' },
]

export default function AdminPage() {
  const user = useAuthStore((s) => s.user)
  const [tab, setTab] = useState('users')

  if (!user?.is_admin) {
    return (
      <div className="p-8 text-center text-gray-400">
        관리자만 접근할 수 있습니다.
      </div>
    )
  }

  return (
    <div className="max-w-5xl mx-auto px-4 py-6">
      <h1 className="text-xl font-bold text-gray-900 dark:text-white mb-6">관리자</h1>

      <div className="flex gap-1 bg-gray-100 dark:bg-gray-700 rounded-xl p-1 mb-6 flex-wrap">
        {TABS.map((t) => (
          <button key={t.key} onClick={() => setTab(t.key)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
              tab === t.key
                ? 'bg-white dark:bg-gray-600 text-primary-700 dark:text-primary-300 shadow-sm'
                : 'text-gray-500 dark:text-gray-400 hover:text-gray-700'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === 'users' && <UsersTab />}
      {tab === 'departments' && <DepartmentsTab />}
      {tab === 'stats' && <StatsTab />}
      {tab === 'announcement' && <AnnouncementTab />}
      {tab === 'bug_reports' && <BugReportsTab />}
    </div>
  )
}

// ── 사용자 관리 ────────────────────────────────────────────
function UsersTab() {
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [showCreate, setShowCreate] = useState(false)
  const [editUser, setEditUser] = useState(null)
  const [resetTarget, setResetTarget] = useState(null)
  const [newPw, setNewPw] = useState('')
  const [departments, setDepartments] = useState([])
  const [selectedIds, setSelectedIds] = useState(new Set())
  const [bulkDeleting, setBulkDeleting] = useState(false)

  useEffect(() => { load(); loadDepts() }, [])

  async function load() {
    setLoading(true)
    setSelectedIds(new Set())
    try {
      const { data } = await api.get('/api/users/admin/all')
      setUsers(data)
    } finally { setLoading(false) }
  }

  async function loadDepts() {
    const { data } = await api.get('/api/users/departments/list')
    setDepartments(data)
  }

  async function toggleActive(u) {
    const action = u.is_active ? '비활성화' : '활성화'
    if (!confirm(`${u.name}을 ${action}하시겠습니까?`)) return
    await api.patch(`/api/users/admin/${u.id}`, { is_active: !u.is_active })
    load()
  }

  async function deleteUser(u) {
    if (!confirm(`${u.name} 계정을 완전히 삭제하시겠습니까?\n삭제 후 복구할 수 없습니다.`)) return
    try {
      await api.delete(`/api/users/admin/${u.id}`)
      load()
    } catch (e) { alert(e.response?.data?.detail || '삭제 실패') }
  }

  function toggleSelect(id) {
    setSelectedIds((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  function toggleSelectAll() {
    if (selectedIds.size === users.length) {
      setSelectedIds(new Set())
    } else {
      setSelectedIds(new Set(users.map((u) => u.id)))
    }
  }

  async function bulkDelete() {
    if (selectedIds.size === 0) return
    if (!confirm(`선택한 ${selectedIds.size}명의 계정을 삭제하시겠습니까?\n삭제 후 복구할 수 없습니다.`)) return
    setBulkDeleting(true)
    let failCount = 0
    for (const id of selectedIds) {
      try {
        await api.delete(`/api/users/admin/${id}`)
      } catch {
        failCount++
      }
    }
    setBulkDeleting(false)
    if (failCount > 0) alert(`${failCount}명 삭제 실패 (자신의 계정 포함 여부 확인)`)
    load()
  }

  async function doResetPw() {
    if (!newPw || newPw.length < 6) { alert('비밀번호는 6자 이상이어야 합니다.'); return }
    try {
      await api.post(`/api/users/admin/${resetTarget.id}/reset-password`, { new_password: newPw })
      alert(`${resetTarget.name}의 비밀번호가 변경되었습니다.`)
      setResetTarget(null)
      setNewPw('')
    } catch (e) { alert(e.response?.data?.detail || '초기화 실패') }
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-4 gap-2">
        {selectedIds.size > 0 ? (
          <button
            onClick={bulkDelete}
            disabled={bulkDeleting}
            className="bg-red-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-red-700 disabled:opacity-50 flex items-center gap-2"
          >
            {bulkDeleting ? '삭제 중...' : `선택 ${selectedIds.size}명 삭제`}
          </button>
        ) : (
          <div />
        )}
        <button
          onClick={() => setShowCreate(true)}
          className="bg-primary-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-primary-700 flex items-center gap-2"
        >
          <span>＋</span> 사용자 추가
        </button>
      </div>

      {loading ? (
        <div className="text-center py-8 text-gray-400">불러오는 중...</div>
      ) : (
        <div className="overflow-auto rounded-xl border border-gray-100 dark:border-gray-700">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 dark:bg-gray-700 text-xs text-gray-500 dark:text-gray-400 uppercase">
              <tr>
                <th className="px-3 py-3 text-left">
                  <input
                    type="checkbox"
                    checked={users.length > 0 && selectedIds.size === users.length}
                    onChange={toggleSelectAll}
                    className="rounded"
                  />
                </th>
                <th className="px-4 py-3 text-left">이름</th>
                <th className="px-4 py-3 text-left">아이디</th>
                <th className="px-4 py-3 text-left">이메일</th>
                <th className="px-4 py-3 text-left">부서</th>
                <th className="px-4 py-3 text-left">상태</th>
                <th className="px-4 py-3 text-left">권한</th>
                <th className="px-4 py-3 text-left">작업</th>
              </tr>
            </thead>
            <tbody className="bg-white dark:bg-gray-800">
              {users.map((u) => (
                <tr key={u.id} className={`border-t border-gray-100 dark:border-gray-700 ${selectedIds.has(u.id) ? 'bg-blue-50 dark:bg-blue-900/10' : ''}`}>
                  <td className="px-3 py-3">
                    <input
                      type="checkbox"
                      checked={selectedIds.has(u.id)}
                      onChange={() => toggleSelect(u.id)}
                      className="rounded"
                    />
                  </td>
                  <td className="px-4 py-3 font-medium text-gray-900 dark:text-white whitespace-nowrap">{u.name}</td>
                  <td className="px-4 py-3 text-gray-500 dark:text-gray-400 text-xs font-mono">{u.username}</td>
                  <td className="px-4 py-3 text-gray-500 dark:text-gray-400">{u.email || '-'}</td>
                  <td className="px-4 py-3 text-gray-500 dark:text-gray-400">{u.department || '-'}</td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium whitespace-nowrap ${
                      u.is_active
                        ? 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300'
                        : 'bg-gray-100 text-gray-500 dark:bg-gray-700'
                    }`}>
                      {u.is_active ? '활성' : '비활성'}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium whitespace-nowrap ${
                      u.is_admin
                        ? 'bg-purple-100 text-purple-700 dark:bg-purple-900 dark:text-purple-300'
                        : 'bg-gray-100 text-gray-500 dark:bg-gray-600'
                    }`}>
                      {u.is_admin ? '관리자' : '일반'}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex gap-1 flex-nowrap">
                      <button
                        onClick={() => setEditUser(u)}
                        className="px-2 py-1 text-xs bg-blue-100 text-blue-600 rounded hover:bg-blue-200 dark:bg-blue-900/30 dark:text-blue-400 whitespace-nowrap"
                      >
                        수정
                      </button>
                      <button
                        onClick={() => toggleActive(u)}
                        className={`px-2 py-1 text-xs rounded whitespace-nowrap ${
                          u.is_active
                            ? 'bg-yellow-100 text-yellow-700 hover:bg-yellow-200 dark:bg-yellow-900/30 dark:text-yellow-400'
                            : 'bg-green-100 text-green-600 hover:bg-green-200 dark:bg-green-900/30 dark:text-green-400'
                        }`}
                      >
                        {u.is_active ? '비활성화' : '활성화'}
                      </button>
                      <button
                        onClick={() => { setResetTarget(u); setNewPw('') }}
                        className="px-2 py-1 text-xs bg-gray-100 text-gray-600 rounded hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300 whitespace-nowrap"
                      >
                        PW변경
                      </button>
                      <button
                        onClick={() => deleteUser(u)}
                        className="px-2 py-1 text-xs bg-red-100 text-red-600 rounded hover:bg-red-200 dark:bg-red-900/30 dark:text-red-400 whitespace-nowrap"
                      >
                        삭제
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
              {users.length === 0 && (
                <tr>
                  <td colSpan={8} className="text-center py-8 text-gray-400">사용자가 없습니다.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* 사용자 추가 모달 */}
      {showCreate && (
        <CreateUserModal
          departments={departments}
          onClose={() => setShowCreate(false)}
          onCreated={() => { setShowCreate(false); load() }}
        />
      )}

      {/* 사용자 수정 모달 */}
      {editUser && (
        <EditUserModal
          user={editUser}
          departments={departments}
          onClose={() => setEditUser(null)}
          onSaved={() => { setEditUser(null); load() }}
        />
      )}

      {/* 비밀번호 변경 모달 */}
      {resetTarget && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-sm p-6">
            <h3 className="font-bold text-gray-900 dark:text-white mb-4">
              {resetTarget.name} 비밀번호 변경
            </h3>
            <input
              type="text"
              value={newPw}
              onChange={(e) => setNewPw(e.target.value)}
              placeholder="새 비밀번호 (6자 이상)"
              className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm mb-4 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
            />
            <div className="flex gap-3">
              <button onClick={() => setResetTarget(null)}
                className="flex-1 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm text-gray-600 dark:text-gray-300">
                취소
              </button>
              <button onClick={doResetPw}
                className="flex-1 py-2 bg-primary-600 text-white rounded-lg text-sm font-medium hover:bg-primary-700">
                변경
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

// 사용자 추가 모달
function CreateUserModal({ departments, onClose, onCreated }) {
  const [form, setForm] = useState({
    username: '', name: '', email: '', password: '', department_name: '', role: 'user',
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await api.post('/api/users/admin/create', form)
      onCreated()
    } catch (err) {
      setError(err.response?.data?.detail || '생성 실패')
    } finally { setLoading(false) }
  }

  const inputCls = 'w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500'

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-md">
        <div className="p-6 border-b border-gray-100 dark:border-gray-700 flex items-center justify-between">
          <h3 className="font-bold text-gray-900 dark:text-white">사용자 추가</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl">✕</button>
        </div>
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">아이디 *</label>
              <input required value={form.username} onChange={(e) => setForm({ ...form, username: e.target.value })}
                placeholder="영문/숫자" className={inputCls} />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">이름 *</label>
              <input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })}
                placeholder="홍길동" className={inputCls} />
            </div>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">이메일</label>
            <input type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })}
              placeholder="example@company.com" className={inputCls} />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">비밀번호 * (6자 이상)</label>
            <input required type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })}
              placeholder="비밀번호" className={inputCls} />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">부서</label>
              <select value={form.department_name} onChange={(e) => setForm({ ...form, department_name: e.target.value })}
                className={inputCls}>
                <option value="">부서 없음</option>
                {departments.map((d) => <option key={d} value={d}>{d}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">권한</label>
              <select value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })}
                className={inputCls}>
                <option value="user">일반</option>
                <option value="admin">관리자</option>
              </select>
            </div>
          </div>
          {error && <p className="text-red-500 text-sm">{error}</p>}
          <div className="flex gap-3 pt-2">
            <button type="button" onClick={onClose}
              className="flex-1 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm text-gray-600 dark:text-gray-300">
              취소
            </button>
            <button type="submit" disabled={loading}
              className="flex-1 py-2 bg-primary-600 text-white rounded-lg text-sm font-medium hover:bg-primary-700 disabled:opacity-50">
              {loading ? '생성 중...' : '사용자 추가'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

// 사용자 수정 모달
function EditUserModal({ user, departments, onClose, onSaved }) {
  const [form, setForm] = useState({
    name: user.name || '',
    email: user.email || '',
    department_name: user.department || '',
    role: user.role || 'user',
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await api.patch(`/api/users/admin/${user.id}`, form)
      onSaved()
    } catch (err) {
      setError(err.response?.data?.detail || '수정 실패')
    } finally { setLoading(false) }
  }

  const inputCls = 'w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500'

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-md">
        <div className="p-6 border-b border-gray-100 dark:border-gray-700 flex items-center justify-between">
          <h3 className="font-bold text-gray-900 dark:text-white">{user.name} 정보 수정</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl">✕</button>
        </div>
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">이름 *</label>
            <input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })}
              className={inputCls} />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">이메일</label>
            <input type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })}
              className={inputCls} />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">부서</label>
              <select value={form.department_name} onChange={(e) => setForm({ ...form, department_name: e.target.value })}
                className={inputCls}>
                <option value="">부서 없음</option>
                {departments.map((d) => <option key={d} value={d}>{d}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">권한</label>
              <select value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })}
                className={inputCls}>
                <option value="user">일반</option>
                <option value="admin">관리자</option>
              </select>
            </div>
          </div>
          {error && <p className="text-red-500 text-sm">{error}</p>}
          <div className="flex gap-3 pt-2">
            <button type="button" onClick={onClose}
              className="flex-1 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm text-gray-600 dark:text-gray-300">
              취소
            </button>
            <button type="submit" disabled={loading}
              className="flex-1 py-2 bg-primary-600 text-white rounded-lg text-sm font-medium hover:bg-primary-700 disabled:opacity-50">
              {loading ? '저장 중...' : '저장'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

// ── 부서 관리 ──────────────────────────────────────────────
function DepartmentsTab() {
  const [depts, setDepts] = useState([])
  const [newName, setNewName] = useState('')
  const [editId, setEditId] = useState(null)
  const [editName, setEditName] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => { load() }, [])

  async function load() {
    setLoading(true)
    try {
      const { data } = await api.get('/api/users/admin/departments')
      setDepts(data)
    } finally { setLoading(false) }
  }

  async function create() {
    if (!newName.trim()) return
    try {
      await api.post('/api/users/admin/departments', { name: newName.trim() })
      setNewName('')
      load()
    } catch (e) { alert(e.response?.data?.detail || '생성 실패') }
  }

  async function update(id) {
    if (!editName.trim()) return
    try {
      await api.patch(`/api/users/admin/departments/${id}`, { name: editName.trim() })
      setEditId(null)
      load()
    } catch (e) { alert(e.response?.data?.detail || '수정 실패') }
  }

  async function remove(dept) {
    if (!confirm(`"${dept.name}" 부서를 삭제하시겠습니까?`)) return
    try {
      await api.delete(`/api/users/admin/departments/${dept.id}`)
      load()
    } catch (e) { alert(e.response?.data?.detail || '삭제 실패') }
  }

  return (
    <div>
      <div className="flex gap-2 mb-6">
        <input type="text" value={newName} onChange={(e) => setNewName(e.target.value)}
          placeholder="새 부서명"
          className="border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 flex-1"
          onKeyDown={(e) => { if (e.key === 'Enter') create() }}
        />
        <button onClick={create} className="bg-primary-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-primary-700">추가</button>
      </div>

      {loading ? <div className="text-center py-8 text-gray-400">불러오는 중...</div> : (
        <div className="space-y-2">
          {depts.map((d) => (
            <div key={d.id} className="flex items-center gap-3 p-3 bg-white dark:bg-gray-800 rounded-xl border border-gray-100 dark:border-gray-700">
              {editId === d.id ? (
                <>
                  <input type="text" value={editName} onChange={(e) => setEditName(e.target.value)}
                    className="border border-gray-300 dark:border-gray-600 rounded px-2 py-1 text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 flex-1"
                    autoFocus onKeyDown={(e) => { if (e.key === 'Enter') update(d.id) }}
                  />
                  <button onClick={() => update(d.id)} className="text-xs bg-primary-600 text-white px-3 py-1 rounded hover:bg-primary-700">저장</button>
                  <button onClick={() => setEditId(null)} className="text-xs text-gray-500 hover:text-gray-700 dark:hover:text-gray-200">취소</button>
                </>
              ) : (
                <>
                  <span className="font-medium text-gray-800 dark:text-white flex-1">{d.name}</span>
                  <span className="text-xs text-gray-400">사용자 {d.user_count}명</span>
                  <button onClick={() => { setEditId(d.id); setEditName(d.name) }}
                    className="text-xs text-gray-500 hover:text-primary-600 dark:hover:text-primary-400">수정</button>
                  <button onClick={() => remove(d)} className="text-xs text-red-400 hover:text-red-600">삭제</button>
                </>
              )}
            </div>
          ))}
          {depts.length === 0 && <p className="text-center text-gray-400 py-8">등록된 부서가 없습니다.</p>}
        </div>
      )}
    </div>
  )
}

// ── 전체 통계 ──────────────────────────────────────────────
function StatsTab() {
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get('/api/users/admin/stats').then(({ data }) => setStats(data)).finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="text-center py-8 text-gray-400">불러오는 중...</div>
  if (!stats) return null

  const STATUS_LABELS = { pending: '대기', in_progress: '진행중', review: '검토', approved: '완료', rejected: '반려' }
  const STATUS_COLORS_CARD = {
    pending: 'bg-gray-100 text-gray-700', in_progress: 'bg-blue-100 text-blue-700',
    review: 'bg-yellow-100 text-yellow-700', approved: 'bg-green-100 text-green-700',
    rejected: 'bg-red-100 text-red-700',
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-primary-50 dark:bg-primary-900/30 rounded-xl p-4">
          <p className="text-xs text-gray-500 mb-1">전체 사용자</p>
          <p className="text-2xl font-bold text-primary-600">{stats.total_users}</p>
        </div>
        <div className="bg-blue-50 dark:bg-blue-900/30 rounded-xl p-4">
          <p className="text-xs text-gray-500 mb-1">전체 업무</p>
          <p className="text-2xl font-bold text-blue-600">{stats.total_tasks}</p>
        </div>
        <div className="bg-red-50 dark:bg-red-900/30 rounded-xl p-4">
          <p className="text-xs text-gray-500 mb-1">마감 초과</p>
          <p className="text-2xl font-bold text-red-600">{stats.overdue}</p>
        </div>
        <div className="bg-gray-50 dark:bg-gray-700 rounded-xl p-4">
          <p className="text-xs text-gray-500 mb-1">완료율</p>
          <p className="text-2xl font-bold text-gray-600">
            {stats.total_tasks ? Math.round(((stats.status_breakdown?.approved || 0) / stats.total_tasks) * 100) : 0}%
          </p>
        </div>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-100 dark:border-gray-700 p-4">
        <h3 className="font-semibold text-gray-800 dark:text-white mb-3">상태별 분포</h3>
        <div className="grid grid-cols-5 gap-2">
          {Object.entries(stats.status_breakdown || {}).map(([s, cnt]) => (
            <div key={s} className={`rounded-lg p-3 text-center ${STATUS_COLORS_CARD[s] || 'bg-gray-100 text-gray-700'}`}>
              <p className="text-xl font-bold">{cnt}</p>
              <p className="text-xs mt-0.5">{STATUS_LABELS[s] || s}</p>
            </div>
          ))}
        </div>
      </div>

      {stats.dept_stats?.length > 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-100 dark:border-gray-700 p-4">
          <h3 className="font-semibold text-gray-800 dark:text-white mb-3">부서별 업무 수</h3>
          <div className="space-y-2">
            {stats.dept_stats.sort((a, b) => b.task_count - a.task_count).map((d) => {
              const maxCount = Math.max(...stats.dept_stats.map((x) => x.task_count), 1)
              return (
                <div key={d.department} className="flex items-center gap-3">
                  <span className="text-sm text-gray-600 dark:text-gray-300 w-24 truncate">{d.department}</span>
                  <div className="flex-1 bg-gray-100 dark:bg-gray-700 rounded-full h-2">
                    <div className="bg-primary-500 h-2 rounded-full" style={{ width: `${(d.task_count / maxCount) * 100}%` }} />
                  </div>
                  <span className="text-sm font-medium text-gray-700 dark:text-gray-300 w-8 text-right">{d.task_count}</span>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {stats.top_assignees?.length > 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-100 dark:border-gray-700 p-4">
          <h3 className="font-semibold text-gray-800 dark:text-white mb-3">미완료 업무 많은 담당자 TOP 10</h3>
          <table className="w-full text-sm">
            <thead>
              <tr className="text-xs text-gray-400 uppercase">
                <th className="text-left py-1">이름</th>
                <th className="text-right py-1">미완료 업무</th>
              </tr>
            </thead>
            <tbody>
              {stats.top_assignees.map((a, i) => (
                <tr key={a.user_id} className="border-t border-gray-50 dark:border-gray-700">
                  <td className="py-2 text-gray-700 dark:text-gray-300">
                    <span className="mr-2 text-xs text-gray-400">{i + 1}</span>{a.name}
                  </td>
                  <td className="py-2 text-right font-medium text-gray-800 dark:text-white">{a.pending_tasks}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

// ── 공지 발송 ──────────────────────────────────────────────
function AnnouncementTab() {
  const [message, setMessage] = useState('')
  const [sending, setSending] = useState(false)

  async function send() {
    if (!message.trim()) { alert('공지 내용을 입력해주세요.'); return }
    if (!confirm('전체 사용자에게 공지를 발송하시겠습니까?')) return
    setSending(true)
    try {
      const { data } = await api.post('/api/users/admin/announcement', { message: message.trim() })
      alert(data.message)
      setMessage('')
    } catch (e) {
      alert(e.response?.data?.detail || '발송 실패')
    } finally { setSending(false) }
  }

  return (
    <div className="max-w-lg">
      <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
        전체 활성 사용자에게 앱 내 알림을 발송합니다.
      </p>
      <textarea
        value={message} onChange={(e) => setMessage(e.target.value)}
        placeholder="공지 내용을 입력하세요"
        rows={5}
        className="w-full border border-gray-300 dark:border-gray-600 rounded-xl px-4 py-3 text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500 mb-4"
      />
      <button onClick={send} disabled={sending}
        className="bg-primary-600 text-white px-6 py-2.5 rounded-xl text-sm font-medium hover:bg-primary-700 disabled:opacity-50"
      >
        {sending ? '발송 중...' : '전체 발송'}
      </button>
    </div>
  )
}

// ── 오류 접수 탭 ────────────────────────────────────────────
const SEVERITY_LABEL = { low: '낮음', normal: '보통', high: '심각', critical: '치명적' }
const SEVERITY_COLOR = {
  low: 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-300',
  normal: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300',
  high: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-300',
  critical: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300',
}
const STATUS_LABEL = { open: '접수', in_review: '검토중', resolved: '해결됨', closed: '종료' }
const STATUS_COLOR = {
  open: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-300',
  in_review: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300',
  resolved: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300',
  closed: 'bg-gray-100 text-gray-500 dark:bg-gray-700 dark:text-gray-400',
}

function BugReportsTab() {
  const [reports, setReports] = useState([])
  const [loading, setLoading] = useState(true)
  const [filterStatus, setFilterStatus] = useState('')
  const [filterSeverity, setFilterSeverity] = useState('')
  const [selected, setSelected] = useState(null)  // 상세 보기
  const [adminNote, setAdminNote] = useState('')
  const [saving, setSaving] = useState(false)
  const [unreadCount, setUnreadCount] = useState(0)

  useEffect(() => { load() }, [filterStatus, filterSeverity])

  async function load() {
    setLoading(true)
    try {
      const params = {}
      if (filterStatus) params.status = filterStatus
      if (filterSeverity) params.severity = filterSeverity
      const { data } = await api.get('/api/bug-reports/', { params })
      setReports(data.items || [])
      setUnreadCount((data.items || []).filter(r => r.status === 'open').length)
    } catch {
      setReports([])
    } finally { setLoading(false) }
  }

  function openDetail(report) {
    setSelected(report)
    setAdminNote(report.admin_note || '')
  }

  async function saveNote(newStatus) {
    if (!selected) return
    setSaving(true)
    try {
      await api.patch(`/api/bug-reports/${selected.id}`, {
        status: newStatus || selected.status,
        admin_note: adminNote,
      })
      setSelected(null)
      load()
    } catch {
      alert('저장에 실패했습니다.')
    } finally { setSaving(false) }
  }

  const inputCls = 'border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-1.5 text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500'

  return (
    <div>
      {/* 헤더 + 필터 */}
      <div className="flex items-center justify-between mb-4 gap-3 flex-wrap">
        <div className="flex items-center gap-2">
          <h2 className="text-base font-semibold text-gray-900 dark:text-white">오류 접수 목록</h2>
          {unreadCount > 0 && (
            <span className="bg-red-500 text-white text-xs rounded-full px-2 py-0.5 font-medium">
              신규 {unreadCount}
            </span>
          )}
        </div>
        <div className="flex gap-2">
          <select value={filterSeverity} onChange={e => setFilterSeverity(e.target.value)} className={inputCls}>
            <option value="">전체 심각도</option>
            <option value="critical">치명적</option>
            <option value="high">심각</option>
            <option value="normal">보통</option>
            <option value="low">낮음</option>
          </select>
          <select value={filterStatus} onChange={e => setFilterStatus(e.target.value)} className={inputCls}>
            <option value="">전체 상태</option>
            <option value="open">접수</option>
            <option value="in_review">검토중</option>
            <option value="resolved">해결됨</option>
            <option value="closed">종료</option>
          </select>
          <button onClick={load} className="px-3 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300">
            새로고침
          </button>
        </div>
      </div>

      {/* 테이블 */}
      {loading ? (
        <div className="text-center py-12 text-gray-400">불러오는 중...</div>
      ) : reports.length === 0 ? (
        <div className="text-center py-12 text-gray-400">접수된 오류가 없습니다.</div>
      ) : (
        <div className="border border-gray-200 dark:border-gray-700 rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 dark:bg-gray-700/50">
              <tr>
                <th className="text-left py-3 px-4 text-gray-500 dark:text-gray-400 font-medium">제목</th>
                <th className="text-left py-3 px-4 text-gray-500 dark:text-gray-400 font-medium">신고자</th>
                <th className="text-left py-3 px-4 text-gray-500 dark:text-gray-400 font-medium">위치</th>
                <th className="text-center py-3 px-4 text-gray-500 dark:text-gray-400 font-medium">심각도</th>
                <th className="text-center py-3 px-4 text-gray-500 dark:text-gray-400 font-medium">상태</th>
                <th className="text-left py-3 px-4 text-gray-500 dark:text-gray-400 font-medium">접수일</th>
                <th className="py-3 px-4"></th>
              </tr>
            </thead>
            <tbody>
              {reports.map((r) => (
                <tr key={r.id} className="border-t border-gray-100 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700/30">
                  <td className="py-3 px-4 font-medium text-gray-900 dark:text-gray-100 max-w-[200px] truncate">
                    {r.title}
                  </td>
                  <td className="py-3 px-4 text-gray-600 dark:text-gray-300">
                    {r.reporter_name}
                    {r.reporter_dept && <span className="text-xs text-gray-400 ml-1">({r.reporter_dept})</span>}
                  </td>
                  <td className="py-3 px-4 text-gray-500 dark:text-gray-400">{r.page || '-'}</td>
                  <td className="py-3 px-4 text-center">
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${SEVERITY_COLOR[r.severity] || ''}`}>
                      {SEVERITY_LABEL[r.severity] || r.severity}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-center">
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_COLOR[r.status] || ''}`}>
                      {STATUS_LABEL[r.status] || r.status}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-gray-400 text-xs">
                    {r.created_at ? new Date(r.created_at).toLocaleDateString('ko-KR') : '-'}
                  </td>
                  <td className="py-3 px-4">
                    <button
                      onClick={() => openDetail(r)}
                      className="text-xs px-3 py-1 bg-primary-50 dark:bg-primary-900/20 text-primary-700 dark:text-primary-300 rounded-lg hover:bg-primary-100"
                    >
                      상세
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* 상세 모달 */}
      {selected && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-lg max-h-[85vh] overflow-y-auto">
            <div className="p-6 border-b border-gray-100 dark:border-gray-700 flex items-center justify-between">
              <h3 className="font-bold text-gray-900 dark:text-white">오류 상세</h3>
              <button onClick={() => setSelected(null)} className="text-gray-400 hover:text-gray-600 text-xl">✕</button>
            </div>
            <div className="p-6 space-y-4">
              {/* 기본 정보 */}
              <div>
                <p className="text-xs text-gray-400 mb-1">제목</p>
                <p className="font-medium text-gray-900 dark:text-gray-100">{selected.title}</p>
              </div>
              <div className="grid grid-cols-3 gap-3 text-sm">
                <div>
                  <p className="text-xs text-gray-400 mb-1">신고자</p>
                  <p className="text-gray-700 dark:text-gray-300">{selected.reporter_name}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-400 mb-1">발생 위치</p>
                  <p className="text-gray-700 dark:text-gray-300">{selected.page || '-'}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-400 mb-1">심각도</p>
                  <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${SEVERITY_COLOR[selected.severity] || ''}`}>
                    {SEVERITY_LABEL[selected.severity]}
                  </span>
                </div>
              </div>
              <div>
                <p className="text-xs text-gray-400 mb-1">오류 설명</p>
                <p className="text-sm text-gray-700 dark:text-gray-300 bg-gray-50 dark:bg-gray-700 rounded-lg p-3 whitespace-pre-wrap">
                  {selected.description}
                </p>
              </div>
              {selected.steps && (
                <div>
                  <p className="text-xs text-gray-400 mb-1">재현 방법</p>
                  <p className="text-sm text-gray-700 dark:text-gray-300 bg-gray-50 dark:bg-gray-700 rounded-lg p-3 whitespace-pre-wrap">
                    {selected.steps}
                  </p>
                </div>
              )}
              {/* 관리자 처리 */}
              <div className="pt-2 border-t border-gray-100 dark:border-gray-700">
                <p className="text-xs text-gray-400 mb-2">관리자 메모</p>
                <textarea
                  value={adminNote}
                  onChange={e => setAdminNote(e.target.value)}
                  rows={2}
                  placeholder="처리 내용, 원인, 해결 방법 등을 기록하세요"
                  className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
              </div>
              {/* 상태 변경 버튼 */}
              <div className="flex gap-2 flex-wrap">
                {['open','in_review','resolved','closed'].map(s => (
                  <button
                    key={s}
                    onClick={() => saveNote(s)}
                    disabled={saving || selected.status === s}
                    className={`px-3 py-1.5 text-xs rounded-lg font-medium transition disabled:opacity-40 ${
                      selected.status === s
                        ? `${STATUS_COLOR[s]} cursor-default`
                        : 'border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300'
                    }`}
                  >
                    {saving ? '저장 중...' : `→ ${STATUS_LABEL[s]}`}
                  </button>
                ))}
              </div>
              <button
                onClick={() => saveNote(selected.status)}
                disabled={saving}
                className="w-full py-2 bg-primary-600 text-white rounded-lg text-sm font-medium hover:bg-primary-700 disabled:opacity-50"
              >
                {saving ? '저장 중...' : '메모 저장'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
