import { useState, useEffect, useCallback, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import api, { getApiBase } from '../utils/api'
import useAuthStore from '../store/authStore'
import TaskRow from '../components/TaskRow'
import TaskFormModal from '../components/TaskFormModal'

const SECTIONS = [
  { key: 'assigned_to_me', label: '내가 받은 업무', showAssigner: true },
  { key: 'assigned_by_me', label: '내가 요청한 업무', showAssignee: true },
  { key: 'subtasks_to_me', label: '내가 받은 자료요청', showAssigner: true },
]

const STATUS_FILTERS = [
  { value: '', label: '전체' },
  { value: 'pending', label: '대기' },
  { value: 'in_progress', label: '진행중' },
  { value: 'review', label: '검토요청' },
  { value: 'approved', label: '완료' },
  { value: 'rejected', label: '반려' },
]

const PRIORITY_FILTERS = [
  { value: '', label: '전체' },
  { value: 'urgent', label: '긴급' },
  { value: 'high', label: '높음' },
  { value: 'normal', label: '보통' },
  { value: 'low', label: '낮음' },
]

const SORT_OPTIONS = [
  { value: 'created_at_desc', label: '최신순', sort_by: 'created_at', sort_dir: 'desc' },
  { value: 'created_at_asc',  label: '오래된순', sort_by: 'created_at', sort_dir: 'asc' },
  { value: 'due_date_asc',    label: '마감 임박순', sort_by: 'due_date', sort_dir: 'asc' },
  { value: 'priority_asc',    label: '우선순위 높은순', sort_by: 'priority', sort_dir: 'asc' },
  { value: 'status_asc',      label: '상태순', sort_by: 'status', sort_dir: 'asc' },
  { value: 'title_asc',       label: '제목 오름차순', sort_by: 'title', sort_dir: 'asc' },
]

const BULK_STATUS_OPTIONS = [
  { value: 'in_progress', label: '진행중으로 변경' },
  { value: 'review', label: '검토요청으로 변경' },
  { value: 'approved', label: '완료(승인)으로 변경' },
  { value: 'rejected', label: '반려' },
]

const STATUS_LABELS = {
  pending: '대기', in_progress: '진행중', review: '검토', approved: '완료', rejected: '반려',
}
const STATUS_COLORS = {
  pending: 'bg-gray-400', in_progress: 'bg-blue-400', review: 'bg-yellow-400',
  approved: 'bg-green-500', rejected: 'bg-red-400',
}

const PAGE_SIZE = 20

// D-Day 배지 계산
function getDayBadge(dueDate, status) {
  if (!dueDate || status === 'approved') return null
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const due = new Date(dueDate)
  due.setHours(0, 0, 0, 0)
  const diff = Math.round((due - today) / (1000 * 60 * 60 * 24))
  if (diff < 0) return { label: `D+${Math.abs(diff)}`, cls: 'bg-red-500 text-white', title: '마감 초과' }
  if (diff === 0) return { label: 'D-Day', cls: 'bg-red-500 text-white animate-pulse', title: '오늘 마감' }
  if (diff <= 1) return { label: `D-${diff}`, cls: 'bg-red-400 text-white', title: `${diff}일 후 마감` }
  if (diff <= 3) return { label: `D-${diff}`, cls: 'bg-orange-400 text-white', title: `${diff}일 후 마감` }
  if (diff <= 7) return { label: `D-${diff}`, cls: 'bg-yellow-400 text-gray-800', title: `${diff}일 후 마감` }
  return null
}

// 캘린더 뷰
function CalendarView({ tasks }) {
  const today = new Date()
  const [year, setYear] = useState(today.getFullYear())
  const [month, setMonth] = useState(today.getMonth())
  const navigate = useNavigate()

  const firstDay = new Date(year, month, 1).getDay()
  const daysInMonth = new Date(year, month + 1, 0).getDate()

  const tasksByDate = {}
  tasks.forEach((t) => {
    if (!t.due_date) return
    const key = t.due_date.slice(0, 10)
    if (!tasksByDate[key]) tasksByDate[key] = []
    tasksByDate[key].push(t)
  })

  const cells = []
  for (let i = 0; i < firstDay; i++) cells.push(null)
  for (let d = 1; d <= daysInMonth; d++) cells.push(d)

  const monthNames = ['1월', '2월', '3월', '4월', '5월', '6월', '7월', '8월', '9월', '10월', '11월', '12월']

  return (
    <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700 p-4">
      <div className="flex items-center justify-between mb-4">
        <button onClick={() => { if (month === 0) { setMonth(11); setYear(y => y - 1) } else setMonth(m => m - 1) }}
          className="p-1.5 rounded hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-600 dark:text-gray-300">‹</button>
        <span className="font-semibold text-gray-800 dark:text-white">{year}년 {monthNames[month]}</span>
        <button onClick={() => { if (month === 11) { setMonth(0); setYear(y => y + 1) } else setMonth(m => m + 1) }}
          className="p-1.5 rounded hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-600 dark:text-gray-300">›</button>
      </div>
      <div className="grid grid-cols-7 gap-px text-xs">
        {['일', '월', '화', '수', '목', '금', '토'].map((d, i) => (
          <div key={d} className={`text-center py-1 font-medium ${i === 0 ? 'text-red-500' : i === 6 ? 'text-blue-500' : 'text-gray-500 dark:text-gray-400'}`}>{d}</div>
        ))}
        {cells.map((day, i) => {
          if (!day) return <div key={`e-${i}`} />
          const dateKey = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`
          const dayTasks = tasksByDate[dateKey] || []
          const isToday = today.getFullYear() === year && today.getMonth() === month && today.getDate() === day
          const dayOfWeek = (firstDay + day - 1) % 7
          return (
            <div key={day} className={`min-h-[60px] rounded-lg p-1 border ${isToday ? 'border-primary-400 bg-primary-50 dark:bg-primary-900/30' : 'border-gray-100 dark:border-gray-700'}`}>
              <p className={`text-center text-xs font-medium mb-0.5 ${dayOfWeek === 0 ? 'text-red-500' : dayOfWeek === 6 ? 'text-blue-500' : 'text-gray-700 dark:text-gray-300'}`}>{day}</p>
              {dayTasks.slice(0, 3).map((t) => (
                <div key={t.id} onClick={() => navigate(`/tasks/${t.id}`)}
                  className={`text-xs truncate rounded px-1 py-0.5 cursor-pointer mb-0.5 ${
                    t.status === 'approved' ? 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300' :
                    t.priority === 'urgent' ? 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300' :
                    'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300'
                  }`}
                  title={t.title}
                >
                  {t.title}
                </div>
              ))}
              {dayTasks.length > 3 && (
                <p className="text-xs text-gray-400 text-center">+{dayTasks.length - 3}</p>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default function DashboardPage() {
  const token = useAuthStore((s) => s.token)
  const [summary, setSummary] = useState(null)
  const [tasks, setTasks] = useState({})
  const [activeSection, setActiveSection] = useState('assigned_to_me')
  const [viewMode, setViewMode] = useState('list') // 'list' | 'calendar'
  const [statusFilter, setStatusFilter] = useState('')
  const [priorityFilter, setPriorityFilter] = useState('')
  const [search, setSearch] = useState('')
  const [dueDateFrom, setDueDateFrom] = useState('')
  const [dueDateTo, setDueDateTo] = useState('')
  const [sortValue, setSortValue] = useState('created_at_desc')
  const [favoritesOnly, setFavoritesOnly] = useState(false)
  const [page, setPage] = useState(1)
  const [showModal, setShowModal] = useState(false)
  const [loading, setLoading] = useState(false)
  const [recentSearches, setRecentSearches] = useState(() => {
    try { return JSON.parse(localStorage.getItem('collabtodo_recent_searches') || '[]') } catch { return [] }
  })
  const [showSuggestions, setShowSuggestions] = useState(false)
  const searchRef = useRef(null)

  // 필터 프리셋
  const [presets, setPresets] = useState([])
  const [showPresetModal, setShowPresetModal] = useState(false)
  const [presetName, setPresetName] = useState('')

  // 일괄처리
  const [selectedIds, setSelectedIds] = useState(new Set())
  const [showBulkPanel, setShowBulkPanel] = useState(false)
  const [bulkStatus, setBulkStatus] = useState('')
  const [bulkComment, setBulkComment] = useState('')
  const [bulkLoading, setBulkLoading] = useState(false)

  useEffect(() => {
    fetchSummary()
    // 모든 섹션 초기 로드 (탭 카운트 표시용)
    SECTIONS.forEach((s) => {
      api.get(`/api/tasks/?section=${s.key}&page=1&page_size=20`)
        .then(({ data }) => setTasks((prev) => ({ ...prev, [s.key]: data })))
        .catch(() => {})
    })
  }, [])

  useEffect(() => {
    api.get('/api/users/me/filter-presets').then(({ data }) => setPresets(data)).catch(() => {})
  }, [])

  useEffect(() => {
    setPage(1)
    setSelectedIds(new Set())
  }, [activeSection, statusFilter, priorityFilter, dueDateFrom, dueDateTo, sortValue, favoritesOnly])

  useEffect(() => {
    fetchTasks(activeSection, page)
  }, [activeSection, statusFilter, priorityFilter, dueDateFrom, dueDateTo, sortValue, page, favoritesOnly])

  async function fetchSummary() {
    try {
      const { data } = await api.get('/api/tasks/dashboard')
      setSummary(data)
    } catch (e) { console.error(e) }
  }

  const currentSort = SORT_OPTIONS.find((o) => o.value === sortValue) || SORT_OPTIONS[0]

  const fetchTasks = useCallback(async (section, p = 1) => {
    setLoading(true)
    try {
      const params = new URLSearchParams({ section, page: p, page_size: PAGE_SIZE })
      if (statusFilter) params.append('status', statusFilter)
      if (priorityFilter) params.append('priority', priorityFilter)
      if (search) params.append('search', search)
      if (dueDateFrom) params.append('due_date_from', dueDateFrom)
      if (dueDateTo) params.append('due_date_to', dueDateTo)
      if (favoritesOnly) params.append('favorites_only', 'true')
      params.append('sort_by', currentSort.sort_by)
      params.append('sort_dir', currentSort.sort_dir)
      const { data } = await api.get(`/api/tasks/?${params}`)
      setTasks((prev) => ({ ...prev, [section]: data }))
    } catch (e) {
      console.error('fetchTasks error:', e)
    } finally {
      setLoading(false)
    }
  }, [statusFilter, priorityFilter, search, dueDateFrom, dueDateTo, sortValue, favoritesOnly])

  // 필터 프리셋 저장
  async function savePreset() {
    if (!presetName.trim()) return
    try {
      await api.post('/api/users/me/filter-presets', {
        name: presetName.trim(),
        section: activeSection,
        status: statusFilter || null,
        priority: priorityFilter || null,
        sort_by: currentSort.sort_by,
        sort_dir: currentSort.sort_dir,
        due_date_from: dueDateFrom || null,
        due_date_to: dueDateTo || null,
      })
      const { data } = await api.get('/api/users/me/filter-presets')
      setPresets(data)
      setShowPresetModal(false)
      setPresetName('')
    } catch (e) {
      alert(e.response?.data?.detail || '저장에 실패했습니다.')
    }
  }

  async function deletePreset(id) {
    await api.delete(`/api/users/me/filter-presets/${id}`)
    setPresets((p) => p.filter((x) => x.id !== id))
  }

  function applyPreset(preset) {
    if (preset.section) setActiveSection(preset.section)
    setStatusFilter(preset.status || '')
    setPriorityFilter(preset.priority || '')
    if (preset.sort_by) {
      const match = SORT_OPTIONS.find((o) => o.sort_by === preset.sort_by && o.sort_dir === preset.sort_dir)
      if (match) setSortValue(match.value)
    }
    setDueDateFrom(preset.due_date_from || '')
    setDueDateTo(preset.due_date_to || '')
    setPage(1)
  }

  // 서버에서 Excel 다운로드
  async function exportExcel() {
    try {
      const params = new URLSearchParams({ section: activeSection, fmt: 'xlsx' })
      if (statusFilter) params.append('status', statusFilter)
      if (priorityFilter) params.append('priority', priorityFilter)
      if (search) params.append('search', search)
      if (dueDateFrom) params.append('due_date_from', dueDateFrom)
      if (dueDateTo) params.append('due_date_to', dueDateTo)
      const token = localStorage.getItem('access_token')
      const base = getApiBase()
      const response = await fetch(`${base}/api/tasks/export?${params}`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!response.ok) throw new Error('export failed')
      const blob = await response.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `tasks_${new Date().toISOString().slice(0, 10)}.csv`
      a.click()
      URL.revokeObjectURL(url)
    } catch (e) {
      alert('내보내기에 실패했습니다.')
    }
  }

  function saveRecentSearch(term) {
    if (!term.trim()) return
    const next = [term, ...recentSearches.filter((s) => s !== term)].slice(0, 6)
    setRecentSearches(next)
    localStorage.setItem('collabtodo_recent_searches', JSON.stringify(next))
  }

  function handleSearch(e) {
    e.preventDefault()
    setShowSuggestions(false)
    if (search.trim()) saveRecentSearch(search.trim())
    setPage(1)
    fetchTasks(activeSection, 1)
  }

  function applyRecentSearch(term) {
    setSearch(term)
    setShowSuggestions(false)
    setPage(1)
  }

  function clearRecentSearch(term, e) {
    e.stopPropagation()
    const next = recentSearches.filter((s) => s !== term)
    setRecentSearches(next)
    localStorage.setItem('collabtodo_recent_searches', JSON.stringify(next))
  }

  function onTaskCreated() {
    fetchSummary()
    fetchTasks(activeSection, page)
  }

  async function toggleFavorite(taskId, e) {
    e.stopPropagation()
    e.preventDefault()
    try {
      const { data } = await api.post(`/api/tasks/${taskId}/favorite`)
      setTasks((prev) => {
        const updated = { ...prev }
        Object.keys(updated).forEach((sec) => {
          if (updated[sec]?.items) {
            updated[sec] = {
              ...updated[sec],
              items: updated[sec].items.map((t) =>
                t.id === taskId ? { ...t, is_favorite: data.is_favorite } : t
              ),
            }
          }
        })
        return updated
      })
    } catch (e) { console.error(e) }
  }

  const currentItems = tasks[activeSection]?.items || []

  function toggleSelectAll() {
    if (selectedIds.size === currentItems.length) {
      setSelectedIds(new Set())
    } else {
      setSelectedIds(new Set(currentItems.map((t) => t.id)))
    }
  }

  function toggleSelect(id) {
    setSelectedIds((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  async function handleBulkStatus() {
    if (!bulkStatus) { alert('변경할 상태를 선택해주세요.'); return }
    if (bulkStatus === 'rejected' && !bulkComment.trim()) { alert('반려 시 코멘트는 필수입니다.'); return }
    if (selectedIds.size === 0) { alert('업무를 선택해주세요.'); return }
    setBulkLoading(true)
    try {
      const { data } = await api.post('/api/tasks/bulk-status', {
        task_ids: Array.from(selectedIds),
        status: bulkStatus,
        comment: bulkComment || null,
      })
      alert(data.message)
      setSelectedIds(new Set())
      setShowBulkPanel(false)
      setBulkStatus('')
      setBulkComment('')
      fetchSummary()
      fetchTasks(activeSection, page)
    } catch (err) {
      alert(err.response?.data?.detail || '일괄 처리에 실패했습니다.')
    } finally {
      setBulkLoading(false)
    }
  }

  const currentData = tasks[activeSection] || { items: [], total: 0, page: 1, page_size: PAGE_SIZE }
  const currentTasks = currentData.items || []
  const totalPages = Math.ceil((currentData.total || 0) / PAGE_SIZE)
  const currentSection = SECTIONS.find((s) => s.key === activeSection)

  const breakdown = summary?.status_breakdown || {}
  const breakdownTotal = Object.values(breakdown).reduce((a, b) => a + b, 0) || 1

  // 캘린더용: 현재 섹션의 모든 업무 (최대 200개)
  const calendarTasks = viewMode === 'calendar' ? (currentData.items || []) : []

  return (
    <div className="p-4 md:p-6 max-w-7xl mx-auto">
      {/* 요약 카드 */}
      {summary && (
        <div className="mb-6 space-y-3">
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
            <SummaryCard label="내 전체 업무" value={summary.total} color="text-primary-600" bg="bg-primary-50 dark:bg-primary-900/30" />
            <SummaryCard label="긴급" value={summary.urgent} color="text-red-600 dark:text-red-400" bg="bg-red-50 dark:bg-red-900/30" />
            <SummaryCard label="마감 3일 이내" value={summary.due_soon} color="text-orange-600 dark:text-orange-400" bg="bg-orange-50 dark:bg-orange-900/30" />
            <SummaryCard label="마감 초과" value={summary.overdue || 0} color="text-red-700 dark:text-red-300" bg="bg-red-100 dark:bg-red-900/40" />
            <SummaryCard label="반려된 업무" value={summary.rejected} color="text-gray-600 dark:text-gray-300" bg="bg-gray-100 dark:bg-gray-700" />
          </div>

          {breakdownTotal > 0 && (
            <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700 p-4">
              <p className="text-xs text-gray-500 dark:text-gray-400 mb-2 font-medium">내 업무 상태 분포</p>
              <div className="flex rounded-full overflow-hidden h-3">
                {Object.entries(breakdown).map(([status, count]) =>
                  count > 0 ? (
                    <div key={status} className={`${STATUS_COLORS[status]} transition-all`}
                      style={{ width: `${(count / breakdownTotal) * 100}%` }}
                      title={`${STATUS_LABELS[status]}: ${count}`} />
                  ) : null
                )}
              </div>
              <div className="flex gap-4 mt-2 flex-wrap">
                {Object.entries(breakdown).map(([status, count]) => (
                  <span key={status} className="flex items-center gap-1 text-xs text-gray-500 dark:text-gray-400">
                    <span className={`w-2 h-2 rounded-full ${STATUS_COLORS[status]}`} />
                    {STATUS_LABELS[status]} {count}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* 섹션 탭 + 뷰 전환 + 액션 버튼 */}
      <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
        <div className="flex gap-1 bg-gray-100 dark:bg-gray-700 rounded-xl p-1">
          {SECTIONS.map((s) => (
            <button key={s.key} onClick={() => setActiveSection(s.key)}
              className={`px-3 md:px-4 py-2 rounded-lg text-sm font-medium transition ${
                activeSection === s.key
                  ? 'bg-white dark:bg-gray-600 text-primary-700 dark:text-white shadow-sm'
                  : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200'
              }`}
            >
              {s.label}
              {tasks[s.key] && (
                <span className={`ml-1 text-xs rounded-full px-1.5 ${
                  activeSection === s.key
                    ? 'bg-primary-100 dark:bg-primary-800 text-primary-700 dark:text-primary-200'
                    : 'bg-gray-200 dark:bg-gray-600 text-gray-600 dark:text-gray-300'
                }`}>
                  {tasks[s.key].total ?? tasks[s.key].items?.length ?? 0}
                </span>
              )}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          {/* 뷰 전환 */}
          <div className="flex bg-gray-100 dark:bg-gray-700 rounded-lg p-0.5">
            <button onClick={() => setViewMode('list')}
              className={`px-3 py-1.5 rounded text-sm ${viewMode === 'list' ? 'bg-white dark:bg-gray-600 shadow-sm' : 'text-gray-500 dark:text-gray-400'}`}
              title="목록 뷰">☰</button>
            <button onClick={() => setViewMode('calendar')}
              className={`px-3 py-1.5 rounded text-sm ${viewMode === 'calendar' ? 'bg-white dark:bg-gray-600 shadow-sm' : 'text-gray-500 dark:text-gray-400'}`}
              title="캘린더 뷰">📅</button>
          </div>

          {/* 즐겨찾기 토글 */}
          <button onClick={() => setFavoritesOnly((v) => !v)}
            className={`px-3 py-2 rounded-xl text-sm transition ${favoritesOnly ? 'bg-yellow-400 text-white' : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'}`}
            title="즐겨찾기만 보기"
          >
            ★ 즐겨찾기
          </button>

          {/* 정렬 */}
          <select value={sortValue} onChange={(e) => setSortValue(e.target.value)}
            className="border border-gray-300 dark:border-gray-600 rounded-xl px-3 py-2 text-sm bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-200 focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            {SORT_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
          </select>

          {selectedIds.size > 0 && (
            <button onClick={() => setShowBulkPanel((v) => !v)}
              className="bg-yellow-500 text-white px-3 py-2 rounded-xl text-sm font-medium hover:bg-yellow-600 transition"
            >
              선택 {selectedIds.size}건 처리
            </button>
          )}

          {/* Excel 내보내기 */}
          <button onClick={exportExcel} title="CSV 내보내기 (Excel에서 열기 가능)"
            className="bg-green-600 text-white px-3 py-2 rounded-xl text-sm hover:bg-green-700 flex items-center gap-1"
          >
            ↓ CSV
          </button>

          {/* 프리셋 */}
          <div className="relative group">
            <button className="bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 px-3 py-2 rounded-xl text-sm hover:bg-gray-200 dark:hover:bg-gray-600">
              🔖 프리셋
            </button>
            <div className="absolute right-0 top-full mt-1 w-52 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-xl shadow-xl z-30 hidden group-hover:block">
              <div className="p-2 border-b border-gray-100 dark:border-gray-700">
                <button onClick={() => setShowPresetModal(true)}
                  className="w-full text-left text-sm text-primary-600 hover:text-primary-700 px-2 py-1 rounded hover:bg-gray-50 dark:hover:bg-gray-700"
                >
                  + 현재 필터 저장
                </button>
              </div>
              {presets.length === 0 ? (
                <p className="text-xs text-gray-400 text-center py-3">저장된 프리셋 없음</p>
              ) : (
                presets.map((p) => (
                  <div key={p.id} className="flex items-center justify-between px-2 py-1.5 hover:bg-gray-50 dark:hover:bg-gray-700">
                    <button onClick={() => applyPreset(p)}
                      className="text-sm text-gray-700 dark:text-gray-200 text-left flex-1 truncate"
                    >
                      {p.name}
                    </button>
                    <button onClick={() => deletePreset(p.id)}
                      className="text-gray-300 hover:text-red-400 text-sm ml-2"
                    >×</button>
                  </div>
                ))
              )}
            </div>
          </div>

          <button onClick={() => setShowModal(true)}
            className="bg-primary-600 text-white px-4 py-2 rounded-xl text-sm font-medium hover:bg-primary-700 transition"
          >
            + 업무 등록
          </button>
        </div>
      </div>

      {/* 일괄처리 패널 */}
      {showBulkPanel && selectedIds.size > 0 && (
        <div className="mb-4 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-700 rounded-xl p-4 flex items-center gap-3 flex-wrap">
          <span className="text-sm font-medium text-yellow-800 dark:text-yellow-200">{selectedIds.size}건 일괄 처리</span>
          <select value={bulkStatus} onChange={(e) => setBulkStatus(e.target.value)}
            className="border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-1.5 text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
          >
            <option value="">상태 선택</option>
            {BULK_STATUS_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
          </select>
          {bulkStatus === 'rejected' && (
            <input type="text" value={bulkComment} onChange={(e) => setBulkComment(e.target.value)}
              placeholder="반려 사유 (필수)"
              className="border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-1.5 text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 w-48"
            />
          )}
          <button onClick={handleBulkStatus} disabled={bulkLoading}
            className="bg-primary-600 text-white px-4 py-1.5 rounded-lg text-sm font-medium hover:bg-primary-700 disabled:opacity-50"
          >
            {bulkLoading ? '처리 중...' : '적용'}
          </button>
          <button onClick={() => { setShowBulkPanel(false); setSelectedIds(new Set()) }}
            className="text-sm text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200"
          >취소</button>
        </div>
      )}

      {/* 필터 영역 */}
      <div className="space-y-2 mb-4">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-xs text-gray-400 dark:text-gray-500 w-12">상태</span>
          <div className="flex gap-1 flex-wrap">
            {STATUS_FILTERS.map((f) => (
              <button key={f.value} onClick={() => setStatusFilter(f.value)}
                className={`px-3 py-1 rounded-full text-xs font-semibold transition ${
                  statusFilter === f.value
                    ? 'bg-primary-600 text-white ring-2 ring-primary-400 ring-offset-1 dark:ring-offset-gray-800'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                }`}
              >
                {f.label}
              </button>
            ))}
          </div>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-xs text-gray-400 dark:text-gray-500 w-12">우선순위</span>
          <div className="flex gap-1 flex-wrap">
            {PRIORITY_FILTERS.map((f) => (
              <button key={f.value} onClick={() => setPriorityFilter(f.value)}
                className={`px-3 py-1 rounded-full text-xs font-semibold transition ${
                  priorityFilter === f.value
                    ? 'bg-primary-600 text-white ring-2 ring-primary-400 ring-offset-1 dark:ring-offset-gray-800'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                }`}
              >
                {f.label}
              </button>
            ))}
          </div>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-xs text-gray-400 dark:text-gray-500 w-12">마감일</span>
          <input type="date" value={dueDateFrom} onChange={(e) => setDueDateFrom(e.target.value)}
            className="border border-gray-300 dark:border-gray-600 rounded-lg px-2 py-1 text-xs bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
          />
          <span className="text-gray-400 text-xs">~</span>
          <input type="date" value={dueDateTo} onChange={(e) => setDueDateTo(e.target.value)}
            className="border border-gray-300 dark:border-gray-600 rounded-lg px-2 py-1 text-xs bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
          />
          {(dueDateFrom || dueDateTo) && (
            <button onClick={() => { setDueDateFrom(''); setDueDateTo('') }} className="text-xs text-gray-400 hover:text-gray-600 dark:hover:text-gray-200">초기화</button>
          )}

          <form onSubmit={handleSearch} className="ml-auto flex gap-2 relative" ref={searchRef}>
            <div className="relative">
              <input type="text" value={search} onChange={(e) => setSearch(e.target.value)}
                onFocus={() => setShowSuggestions(true)}
                onBlur={() => setTimeout(() => setShowSuggestions(false), 150)}
                placeholder="담당자·태그·키워드 검색"
                className="border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 w-64 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
              />
              {search && (
                <button type="button" onClick={() => { setSearch(''); setPage(1); fetchTasks(activeSection, 1) }}
                  className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 text-xs"
                >✕</button>
              )}
              {showSuggestions && recentSearches.length > 0 && (
                <div className="absolute top-full left-0 mt-1 w-full bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-lg shadow-lg z-30">
                  <p className="text-xs text-gray-400 dark:text-gray-500 px-3 pt-2 pb-1">최근 검색어</p>
                  {recentSearches.map((s) => (
                    <div key={s} onClick={() => applyRecentSearch(s)}
                      className="flex items-center justify-between px-3 py-2 text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer"
                    >
                      <span>{s}</span>
                      <button type="button" onClick={(e) => clearRecentSearch(s, e)} className="text-gray-300 hover:text-gray-500 dark:hover:text-gray-200 text-xs ml-2">✕</button>
                    </div>
                  ))}
                </div>
              )}
            </div>
            <button type="submit" className="bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 px-3 py-1.5 rounded-lg text-sm hover:bg-gray-200 dark:hover:bg-gray-600 flex-shrink-0">검색</button>
          </form>
        </div>
      </div>

      {/* 캘린더 뷰 or 목록 뷰 */}
      {viewMode === 'calendar' ? (
        <CalendarView tasks={currentTasks} />
      ) : (
        <>
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
            {loading ? (
              <div className="py-16 text-center text-gray-400 text-sm">불러오는 중...</div>
            ) : currentTasks.length === 0 ? (
              <div className="py-16 text-center text-gray-400 text-sm">
                {favoritesOnly ? '즐겨찾기한 업무가 없습니다.' : '업무가 없습니다.'}
              </div>
            ) : (
              <table className="w-full">
                <thead className="bg-gray-50 dark:bg-gray-700 text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wide">
                  <tr>
                    <th className="py-3 px-4 text-left w-10">
                      <input type="checkbox"
                        checked={currentTasks.length > 0 && selectedIds.size === currentTasks.length}
                        onChange={toggleSelectAll}
                        className="rounded border-gray-300 dark:border-gray-600 text-primary-600"
                      />
                    </th>
                    <th className="py-3 px-4 text-left w-8">★</th>
                    <th className="py-3 px-4 text-left">업무명</th>
                    {currentSection?.showAssigner && <th className="py-3 px-4 text-left">지시자</th>}
                    {currentSection?.showAssignee && <th className="py-3 px-4 text-left">담당자</th>}
                    <th className="py-3 px-4 text-left">우선순위</th>
                    <th className="py-3 px-4 text-left">상태</th>
                    <th className="py-3 px-4 text-left">진행률</th>
                    <th className="py-3 px-4 text-left">마감일</th>
                  </tr>
                </thead>
                <tbody>
                  {currentTasks.map((task) => (
                    <TaskRowWithFavorite
                      key={task.id}
                      task={task}
                      showAssigner={currentSection?.showAssigner}
                      showAssignee={currentSection?.showAssignee}
                      selected={selectedIds.has(task.id)}
                      onSelect={toggleSelect}
                      onToggleFavorite={toggleFavorite}
                    />
                  ))}
                </tbody>
              </table>
            )}
          </div>

          {/* 페이지네이션 */}
          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-2 mt-4">
              <button onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page <= 1}
                className="px-3 py-1.5 rounded-lg text-sm border border-gray-300 dark:border-gray-600 text-gray-600 dark:text-gray-300 disabled:opacity-40"
              >이전</button>
              {Array.from({ length: totalPages }, (_, i) => i + 1)
                .filter((p) => p === 1 || p === totalPages || Math.abs(p - page) <= 2)
                .reduce((acc, p, idx, arr) => {
                  if (idx > 0 && p - arr[idx - 1] > 1) acc.push('...')
                  acc.push(p)
                  return acc
                }, [])
                .map((p, i) =>
                  p === '...' ? (
                    <span key={`e-${i}`} className="px-2 text-gray-400">...</span>
                  ) : (
                    <button key={p} onClick={() => setPage(p)}
                      className={`px-3 py-1.5 rounded-lg text-sm border transition ${
                        page === p ? 'bg-primary-600 text-white border-primary-600' : 'border-gray-300 dark:border-gray-600 text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'
                      }`}
                    >{p}</button>
                  )
                )}
              <button onClick={() => setPage((p) => Math.min(totalPages, p + 1))} disabled={page >= totalPages}
                className="px-3 py-1.5 rounded-lg text-sm border border-gray-300 dark:border-gray-600 text-gray-600 dark:text-gray-300 disabled:opacity-40"
              >다음</button>
              <span className="text-xs text-gray-400 dark:text-gray-500 ml-2">
                {page} / {totalPages} (총 {currentData.total}건)
              </span>
            </div>
          )}
        </>
      )}

      {/* 프리셋 저장 모달 */}
      {showPresetModal && (
        <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center">
          <div className="bg-white dark:bg-gray-800 rounded-2xl p-6 w-80 shadow-2xl">
            <h3 className="font-semibold text-gray-900 dark:text-white mb-3">필터 프리셋 저장</h3>
            <input type="text" value={presetName} onChange={(e) => setPresetName(e.target.value)}
              placeholder="프리셋 이름"
              className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 mb-4"
              autoFocus
              onKeyDown={(e) => { if (e.key === 'Enter') savePreset() }}
            />
            <div className="flex gap-2 justify-end">
              <button onClick={() => { setShowPresetModal(false); setPresetName('') }}
                className="px-4 py-2 text-sm text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
              >취소</button>
              <button onClick={savePreset}
                className="px-4 py-2 text-sm bg-primary-600 text-white rounded-lg hover:bg-primary-700"
              >저장</button>
            </div>
          </div>
        </div>
      )}

      {showModal && (
        <TaskFormModal onClose={() => setShowModal(false)} onCreated={onTaskCreated} />
      )}
    </div>
  )
}

function SummaryCard({ label, value, color, bg }) {
  return (
    <div className={`${bg} rounded-2xl p-4`}>
      <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">{label}</p>
      <p className={`text-3xl font-bold ${color}`}>{value}</p>
    </div>
  )
}

// 즐겨찾기 버튼 포함 TaskRow 래퍼
function TaskRowWithFavorite({ task, showAssigner, showAssignee, selected, onSelect, onToggleFavorite }) {
  const badge = getDayBadge(task.due_date, task.status)
  const navigate = useNavigate()

  const PRIORITY_LABELS = { urgent: '긴급', high: '높음', normal: '보통', low: '낮음' }
  const PRIORITY_COLORS = {
    urgent: 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300',
    high: 'bg-orange-100 text-orange-700 dark:bg-orange-900 dark:text-orange-300',
    normal: 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300',
    low: 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400',
  }
  const STATUS_LABEL = { pending: '대기', in_progress: '진행중', review: '검토', approved: '완료', rejected: '반려' }
  const STATUS_CLS = {
    pending: 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400',
    in_progress: 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300',
    review: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300',
    approved: 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300',
    rejected: 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300',
  }

  return (
    <tr
      className="border-t border-gray-100 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-750 cursor-pointer transition-colors"
      onClick={() => navigate(`/tasks/${task.id}`)}
    >
      <td className="py-3 px-4" onClick={(e) => e.stopPropagation()}>
        <input type="checkbox" checked={selected} onChange={() => onSelect(task.id)}
          className="rounded border-gray-300 dark:border-gray-600 text-primary-600"
        />
      </td>
      <td className="py-3 px-2" onClick={(e) => e.stopPropagation()}>
        <button onClick={(e) => onToggleFavorite(task.id, e)}
          className={`text-lg leading-none ${task.is_favorite ? 'text-yellow-400' : 'text-gray-200 dark:text-gray-600 hover:text-yellow-300'}`}
          title={task.is_favorite ? '즐겨찾기 해제' : '즐겨찾기 추가'}
        >
          ★
        </button>
      </td>
      <td className="py-3 px-4">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-gray-900 dark:text-white truncate max-w-xs">{task.title}</span>
          {task.attachment_count > 0 && (
            <span className="text-xs text-gray-400 flex-shrink-0">📎{task.attachment_count}</span>
          )}
          {task.subtask_count > 0 && (
            <span className="text-xs text-gray-400 flex-shrink-0">
              [{task.subtasks_done}/{task.subtask_count}]
            </span>
          )}
        </div>
        {task.tags?.length > 0 && (
          <div className="flex gap-1 mt-0.5 flex-wrap">
            {task.tags.slice(0, 3).map((tag) => (
              <span key={tag.id} className="text-xs bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400 px-1.5 py-0.5 rounded">
                {tag.name}
              </span>
            ))}
          </div>
        )}
      </td>
      {showAssigner && (
        <td className="py-3 px-4 text-sm text-gray-500 dark:text-gray-400">{task.assigner?.name || '-'}</td>
      )}
      {showAssignee && (
        <td className="py-3 px-4 text-sm text-gray-500 dark:text-gray-400">{task.assignee?.name || '-'}</td>
      )}
      <td className="py-3 px-4">
        <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${PRIORITY_COLORS[task.priority] || ''}`}>
          {PRIORITY_LABELS[task.priority] || task.priority}
        </span>
      </td>
      <td className="py-3 px-4">
        <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_CLS[task.status] || ''}`}>
          {STATUS_LABEL[task.status] || task.status}
        </span>
      </td>
      <td className="py-3 px-4">
        <div className="flex items-center gap-2">
          <div className="w-16 bg-gray-200 dark:bg-gray-600 rounded-full h-1.5">
            <div className="bg-primary-500 h-1.5 rounded-full" style={{ width: `${task.progress || 0}%` }} />
          </div>
          <span className="text-xs text-gray-500 dark:text-gray-400">{task.progress || 0}%</span>
        </div>
      </td>
      <td className="py-3 px-4">
        <div className="flex items-center gap-1.5">
          {task.due_date && (
            <span className="text-xs text-gray-500 dark:text-gray-400">{task.due_date}</span>
          )}
          {badge && (
            <span className={`text-xs px-1.5 py-0.5 rounded-full font-medium flex-shrink-0 ${badge.cls}`} title={badge.title}>
              {badge.label}
            </span>
          )}
        </div>
      </td>
    </tr>
  )
}
