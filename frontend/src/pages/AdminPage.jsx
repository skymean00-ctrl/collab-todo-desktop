import { useState, useEffect } from 'react'
import api from '../utils/api'
import useAuthStore from '../store/authStore'
import { useNavigate } from 'react-router-dom'

const TABS = [
  { key: 'users', label: '사용자 관리' },
  { key: 'departments', label: '부서 관리' },
  { key: 'categories', label: '카테고리 관리' },
  { key: 'stats', label: '전체 통계' },
  { key: 'announcement', label: '공지 발송' },
]

export default function AdminPage() {
  const user = useAuthStore((s) => s.user)
  const navigate = useNavigate()
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

      {/* 탭 */}
      <div className="flex gap-1 bg-gray-100 dark:bg-gray-700 rounded-xl p-1 mb-6 flex-wrap">
        {TABS.map((t) => (
          <button key={t.key} onClick={() => setTab(t.key)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
              tab === t.key ? 'bg-white dark:bg-gray-600 text-primary-700 dark:text-primary-300 shadow-sm' : 'text-gray-500 dark:text-gray-400 hover:text-gray-700'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === 'users' && <UsersTab />}
      {tab === 'departments' && <DepartmentsTab />}
      {tab === 'categories' && <CategoriesTab />}
      {tab === 'stats' && <StatsTab />}
      {tab === 'announcement' && <AnnouncementTab />}
    </div>
  )
}

// ── 사용자 관리 ────────────────────────────────────────────
function UsersTab() {
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [resetResult, setResetResult] = useState(null)

  useEffect(() => { load() }, [])

  async function load() {
    setLoading(true)
    try {
      const { data } = await api.get('/api/admin/users')
      setUsers(data)
    } finally { setLoading(false) }
  }

  async function deactivate(u) {
    if (!confirm(`${u.name}을 비활성화하시겠습니까?`)) return
    await api.delete(`/api/admin/users/${u.id}`)
    load()
  }

  async function activate(u) {
    await api.patch(`/api/admin/users/${u.id}/activate`)
    load()
  }

  async function toggleAdmin(u) {
    await api.patch(`/api/admin/users/${u.id}/toggle-admin`)
    load()
  }

  async function forceReset(u) {
    if (!confirm(`${u.name}의 비밀번호를 임시값으로 초기화하시겠습니까?`)) return
    const { data } = await api.post(`/api/admin/users/${u.id}/reset-password`)
    setResetResult(data)
  }

  return (
    <div>
      {resetResult && (
        <div className="mb-4 p-4 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-700 rounded-xl">
          <p className="font-medium text-yellow-800 dark:text-yellow-200">{resetResult.message}</p>
          <p className="text-sm text-yellow-700 dark:text-yellow-300 mt-1">
            임시 비밀번호: <code className="bg-yellow-100 dark:bg-yellow-800 px-2 py-0.5 rounded font-mono">{resetResult.temp_password}</code>
          </p>
          <p className="text-xs text-yellow-600 dark:text-yellow-400 mt-1">이 정보를 사용자에게 안전하게 전달하세요.</p>
          <button onClick={() => setResetResult(null)} className="mt-2 text-xs text-yellow-600 hover:underline">닫기</button>
        </div>
      )}

      {loading ? (
        <div className="text-center py-8 text-gray-400">불러오는 중...</div>
      ) : (
        <div className="overflow-auto rounded-xl border border-gray-100 dark:border-gray-700">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 dark:bg-gray-700 text-xs text-gray-500 dark:text-gray-400 uppercase">
              <tr>
                <th className="px-4 py-3 text-left">이름</th>
                <th className="px-4 py-3 text-left">이메일</th>
                <th className="px-4 py-3 text-left">부서</th>
                <th className="px-4 py-3 text-left">직함</th>
                <th className="px-4 py-3 text-left">상태</th>
                <th className="px-4 py-3 text-left">관리자</th>
                <th className="px-4 py-3 text-left">가입일</th>
                <th className="px-4 py-3 text-left">작업</th>
              </tr>
            </thead>
            <tbody className="bg-white dark:bg-gray-800">
              {users.map((u) => (
                <tr key={u.id} className="border-t border-gray-100 dark:border-gray-700">
                  <td className="px-4 py-3 font-medium text-gray-900 dark:text-white">{u.name}</td>
                  <td className="px-4 py-3 text-gray-500 dark:text-gray-400">{u.email}</td>
                  <td className="px-4 py-3 text-gray-500 dark:text-gray-400">{u.department || '-'}</td>
                  <td className="px-4 py-3 text-gray-500 dark:text-gray-400">{u.job_title || '-'}</td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${u.is_active ? 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300' : 'bg-gray-100 text-gray-500 dark:bg-gray-700'}`}>
                      {u.is_active ? '활성' : '비활성'}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    {u.is_admin && <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-700 dark:bg-purple-900 dark:text-purple-300">관리자</span>}
                  </td>
                  <td className="px-4 py-3 text-xs text-gray-400">{u.created_at?.slice(0, 10) || '-'}</td>
                  <td className="px-4 py-3">
                    <div className="flex gap-1 flex-wrap">
                      {u.is_active ? (
                        <button onClick={() => deactivate(u)} className="px-2 py-1 text-xs bg-red-100 text-red-600 rounded hover:bg-red-200 dark:bg-red-900/30 dark:text-red-400">비활성화</button>
                      ) : (
                        <button onClick={() => activate(u)} className="px-2 py-1 text-xs bg-green-100 text-green-600 rounded hover:bg-green-200 dark:bg-green-900/30 dark:text-green-400">활성화</button>
                      )}
                      <button onClick={() => toggleAdmin(u)} className="px-2 py-1 text-xs bg-purple-100 text-purple-600 rounded hover:bg-purple-200 dark:bg-purple-900/30 dark:text-purple-400">
                        {u.is_admin ? '관리자 해제' : '관리자 지정'}
                      </button>
                      <button onClick={() => forceReset(u)} className="px-2 py-1 text-xs bg-yellow-100 text-yellow-700 rounded hover:bg-yellow-200 dark:bg-yellow-900/30 dark:text-yellow-400">PW 초기화</button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
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
      const { data } = await api.get('/api/admin/departments')
      setDepts(data)
    } finally { setLoading(false) }
  }

  async function create() {
    if (!newName.trim()) return
    try {
      await api.post('/api/admin/departments', { name: newName.trim() })
      setNewName('')
      load()
    } catch (e) { alert(e.response?.data?.detail || '생성 실패') }
  }

  async function update(id) {
    if (!editName.trim()) return
    try {
      await api.patch(`/api/admin/departments/${id}`, { name: editName.trim() })
      setEditId(null)
      load()
    } catch (e) { alert(e.response?.data?.detail || '수정 실패') }
  }

  async function remove(dept) {
    if (!confirm(`"${dept.name}" 부서를 삭제하시겠습니까?`)) return
    try {
      await api.delete(`/api/admin/departments/${dept.id}`)
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
                  <button onClick={() => { setEditId(d.id); setEditName(d.name) }} className="text-xs text-gray-500 hover:text-primary-600 dark:hover:text-primary-400">수정</button>
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

// ── 카테고리 관리 ──────────────────────────────────────────
function CategoriesTab() {
  const [cats, setCats] = useState([])
  const [newName, setNewName] = useState('')
  const [newColor, setNewColor] = useState('#6366f1')
  const [editId, setEditId] = useState(null)
  const [editName, setEditName] = useState('')
  const [editColor, setEditColor] = useState('')

  useEffect(() => { load() }, [])

  async function load() {
    const { data } = await api.get('/api/categories/')
    setCats(data)
  }

  async function create() {
    if (!newName.trim()) return
    try {
      await api.post('/api/categories/', { name: newName.trim(), color: newColor })
      setNewName('')
      load()
    } catch (e) { alert(e.response?.data?.detail || '생성 실패') }
  }

  async function update(id) {
    try {
      await api.patch(`/api/categories/${id}`, { name: editName.trim(), color: editColor })
      setEditId(null)
      load()
    } catch (e) { alert(e.response?.data?.detail || '수정 실패') }
  }

  async function remove(cat) {
    if (!confirm(`"${cat.name}" 카테고리를 삭제하시겠습니까? 해당 업무들의 카테고리가 해제됩니다.`)) return
    try {
      await api.delete(`/api/categories/${cat.id}`)
      load()
    } catch (e) { alert(e.response?.data?.detail || '삭제 실패') }
  }

  return (
    <div>
      <div className="flex gap-2 mb-6">
        <input type="color" value={newColor} onChange={(e) => setNewColor(e.target.value)}
          className="w-10 h-10 rounded border border-gray-300 dark:border-gray-600 cursor-pointer p-0.5"
        />
        <input type="text" value={newName} onChange={(e) => setNewName(e.target.value)}
          placeholder="새 카테고리명"
          className="border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 flex-1"
          onKeyDown={(e) => { if (e.key === 'Enter') create() }}
        />
        <button onClick={create} className="bg-primary-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-primary-700">추가</button>
      </div>

      <div className="space-y-2">
        {cats.map((c) => (
          <div key={c.id} className="flex items-center gap-3 p-3 bg-white dark:bg-gray-800 rounded-xl border border-gray-100 dark:border-gray-700">
            {editId === c.id ? (
              <>
                <input type="color" value={editColor} onChange={(e) => setEditColor(e.target.value)}
                  className="w-8 h-8 rounded border cursor-pointer p-0.5"
                />
                <input type="text" value={editName} onChange={(e) => setEditName(e.target.value)}
                  className="border border-gray-300 dark:border-gray-600 rounded px-2 py-1 text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 flex-1"
                  autoFocus
                />
                <button onClick={() => update(c.id)} className="text-xs bg-primary-600 text-white px-3 py-1 rounded hover:bg-primary-700">저장</button>
                <button onClick={() => setEditId(null)} className="text-xs text-gray-500 hover:text-gray-700">취소</button>
              </>
            ) : (
              <>
                <span className="w-5 h-5 rounded-full flex-shrink-0" style={{ backgroundColor: c.color }} />
                <span className="font-medium text-gray-800 dark:text-white flex-1">{c.name}</span>
                <button onClick={() => { setEditId(c.id); setEditName(c.name); setEditColor(c.color) }}
                  className="text-xs text-gray-500 hover:text-primary-600">수정</button>
                <button onClick={() => remove(c)} className="text-xs text-red-400 hover:text-red-600">삭제</button>
              </>
            )}
          </div>
        ))}
        {cats.length === 0 && <p className="text-center text-gray-400 py-8">등록된 카테고리가 없습니다.</p>}
      </div>
    </div>
  )
}

// ── 전체 통계 ──────────────────────────────────────────────
function StatsTab() {
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get('/api/admin/stats').then(({ data }) => setStats(data)).finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="text-center py-8 text-gray-400">불러오는 중...</div>
  if (!stats) return null

  const STATUS_LABELS = { pending: '대기', in_progress: '진행중', review: '검토', approved: '완료', rejected: '반려' }
  const PRIORITY_LABELS = { urgent: '긴급', high: '높음', normal: '보통', low: '낮음' }
  const STATUS_COLORS_CARD = {
    pending: 'bg-gray-100 text-gray-700', in_progress: 'bg-blue-100 text-blue-700',
    review: 'bg-yellow-100 text-yellow-700', approved: 'bg-green-100 text-green-700',
    rejected: 'bg-red-100 text-red-700',
  }

  return (
    <div className="space-y-6">
      {/* 요약 */}
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

      {/* 상태별 분포 */}
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

      {/* 부서별 업무 */}
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

      {/* 담당자별 미완료 업무 TOP 10 */}
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
      const { data } = await api.post('/api/admin/announcements', { message: message.trim() })
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
