import { useState, useEffect, useCallback, useRef } from 'react'
import api from '../utils/api'
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
  { value: 'review',      label: '검토요청으로 변경' },
  { value: 'approved',    label: '완료(승인)으로 변경' },
  { value: 'rejected',    label: '반려' },
]

const STATUS_LABELS = {
  pending: '대기', in_progress: '진행중', review: '검토', approved: '완료', rejected: '반려',
}
const STATUS_COLORS = {
  pending: 'bg-gray-400', in_progress: 'bg-blue-400', review: 'bg-yellow-400',
  approved: 'bg-green-500', rejected: 'bg-red-400',
}

const PAGE_SIZE = 20

export default function DashboardPage() {
  const [summary, setSummary] = useState(null)
  const [tasks, setTasks] = useState({})
  const [activeSection, setActiveSection] = useState('assigned_to_me')
  const [statusFilter, setStatusFilter] = useState('')
  const [priorityFilter, setPriorityFilter] = useState('')
  const [search, setSearch] = useState('')
  const [dueDateFrom, setDueDateFrom] = useState('')
  const [dueDateTo, setDueDateTo] = useState('')
  const [sortValue, setSortValue] = useState('created_at_desc')
  const [page, setPage] = useState(1)
  const [showModal, setShowModal] = useState(false)
  const [loading, setLoading] = useState(false)
  const [recentSearches, setRecentSearches] = useState(() => {
    try { return JSON.parse(localStorage.getItem('collabtodo_recent_searches') || '[]') } catch { return [] }
  })
  const [showSuggestions, setShowSuggestions] = useState(false)
  const searchRef = useRef(null)

  // 일괄처리
  const [selectedIds, setSelectedIds] = useState(new Set())
  const [showBulkPanel, setShowBulkPanel] = useState(false)
  const [bulkStatus, setBulkStatus] = useState('')
  const [bulkComment, setBulkComment] = useState('')
  const [bulkLoading, setBulkLoading] = useState(false)

  useEffect(() => { fetchSummary() }, [])

  useEffect(() => {
    setPage(1)
    setSelectedIds(new Set())
  }, [activeSection, statusFilter, priorityFilter, dueDateFrom, dueDateTo, sortValue])

  useEffect(() => {
    fetchTasks(activeSection, page)
  }, [activeSection, statusFilter, priorityFilter, dueDateFrom, dueDateTo, sortValue, page])

  async function fetchSummary() {
    const { data } = await api.get('/api/tasks/dashboard')
    setSummary(data)
  }

  const currentSort = SORT_OPTIONS.find((o) => o.value === sortValue) || SORT_OPTIONS[0]

  const fetchTasks = useCallback(async (section, p = 1) => {
    setLoading(true)
    try {
      const sort = SORT_OPTIONS.find((o) => o.value === sortValue) || SORT_OPTIONS[0]
      const params = new URLSearchParams({ section, page: p, page_size: PAGE_SIZE })
      if (statusFilter) params.append('status', statusFilter)
      if (priorityFilter) params.append('priority', priorityFilter)
      if (search) params.append('search', search)
      if (dueDateFrom) params.append('due_date_from', dueDateFrom)
      if (dueDateTo) params.append('due_date_to', dueDateTo)
      params.append('sort_by', sort.sort_by)
      params.append('sort_dir', sort.sort_dir)
      const { data } = await api.get(`/api/tasks/?${params}`)
      setTasks((prev) => ({ ...prev, [section]: data }))
    } finally {
      setLoading(false)
    }
  }, [statusFilter, priorityFilter, search, dueDateFrom, dueDateTo, sortValue])

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
    const sort = SORT_OPTIONS.find((o) => o.value === sortValue) || SORT_OPTIONS[0]
    const params = new URLSearchParams({ section: activeSection, page: 1, page_size: PAGE_SIZE })
    if (statusFilter) params.append('status', statusFilter)
    if (priorityFilter) params.append('priority', priorityFilter)
    params.append('search', term)
    if (dueDateFrom) params.append('due_date_from', dueDateFrom)
    if (dueDateTo) params.append('due_date_to', dueDateTo)
    params.append('sort_by', sort.sort_by)
    params.append('sort_dir', sort.sort_dir)
    setLoading(true)
    api.get(`/api/tasks/?${params}`).then(({ data }) => {
      setTasks((prev) => ({ ...prev, [activeSection]: data }))
    }).finally(() => setLoading(false))
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

  function exportCSV() {
    const items = tasks[activeSection]?.items || []
    if (!items.length) return
    const headers = ['ID', '제목', '지시자', '담당자', '우선순위', '상태', '진행률', '마감일', '생성일']
    const rows = items.map((t) => [
      t.id,
      `"${(t.title || '').replace(/"/g, '""')}"`,
      t.assigner?.name || '',
      t.assignee?.name || '',
      t.priority || '',
      t.status || '',
      t.progress,
      t.due_date || '',
      t.created_at ? new Date(t.created_at).toLocaleDateString('ko-KR') : '',
    ])
    const csv = [headers.join(','), ...rows.map((r) => r.join(','))].join('\n')
    const blob = new Blob(['\uFEFF' + csv], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `tasks_${activeSection}_${new Date().toISOString().slice(0, 10)}.csv`
    a.click()
    URL.revokeObjectURL(url)
  }

  // 일괄 선택
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

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* 요약 카드 */}
      {summary && (
        <div className="mb-6 space-y-3">
          <div className="grid grid-cols-4 gap-4">
            <SummaryCard label="내 전체 업무" value={summary.total} color="text-primary-600" bg="bg-primary-50 dark:bg-primary-900/30" />
            <SummaryCard label="긴급 업무" value={summary.urgent} color="text-red-600 dark:text-red-400" bg="bg-red-50 dark:bg-red-900/30" />
            <SummaryCard label="마감 임박 (3일)" value={summary.due_soon} color="text-orange-600 dark:text-orange-400" bg="bg-orange-50 dark:bg-orange-900/30" />
            <SummaryCard label="반려된 업무" value={summary.rejected} color="text-gray-600 dark:text-gray-300" bg="bg-gray-100 dark:bg-gray-700" />
          </div>

          {breakdownTotal > 0 && (
            <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700 p-4">
              <p className="text-xs text-gray-500 dark:text-gray-400 mb-2 font-medium">내 업무 상태 분포</p>
              <div className="flex rounded-full overflow-hidden h-3">
                {Object.entries(breakdown).map(([status, count]) =>
                  count > 0 ? (
                    <div
                      key={status}
                      className={`${STATUS_COLORS[status]} transition-all`}
                      style={{ width: `${(count / breakdownTotal) * 100}%` }}
                      title={`${STATUS_LABELS[status]}: ${count}`}
                    />
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

      {/* 섹션 탭 + 버튼 */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex gap-1 bg-gray-100 dark:bg-gray-700 rounded-xl p-1">
          {SECTIONS.map((s) => (
            <button
              key={s.key}
              onClick={() => setActiveSection(s.key)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
                activeSection === s.key
                  ? 'bg-white dark:bg-gray-600 text-primary-700 dark:text-primary-300 shadow-sm'
                  : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200'
              }`}
            >
              {s.label}
              {tasks[s.key] && (
                <span className="ml-1.5 text-xs bg-gray-200 dark:bg-gray-500 text-gray-600 dark:text-gray-200 rounded-full px-1.5">
                  {tasks[s.key].total ?? tasks[s.key].items?.length ?? 0}
                </span>
              )}
            </button>
          ))}
        </div>
        <div className="flex items-center gap-2">
          {/* 정렬 드롭다운 */}
          <select
            value={sortValue}
            onChange={(e) => setSortValue(e.target.value)}
            className="border border-gray-300 dark:border-gray-600 rounded-xl px-3 py-2 text-sm bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-200 focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            {SORT_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>{o.label}</option>
            ))}
          </select>

          {/* 일괄처리 버튼 */}
          {selectedIds.size > 0 && (
            <button
              onClick={() => setShowBulkPanel((v) => !v)}
              className="bg-yellow-500 text-white px-3 py-2 rounded-xl text-sm font-medium hover:bg-yellow-600 transition"
            >
              선택 {selectedIds.size}건 처리
            </button>
          )}

          <button
            onClick={exportCSV}
            title="CSV 내보내기"
            className="bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 px-3 py-2 rounded-xl text-sm hover:bg-gray-200 dark:hover:bg-gray-600 flex items-center gap-1"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
            CSV
          </button>
          <button
            onClick={() => setShowModal(true)}
            className="bg-primary-600 text-white px-4 py-2 rounded-xl text-sm font-medium hover:bg-primary-700 transition flex items-center gap-1"
          >
            + 업무 등록
          </button>
        </div>
      </div>

      {/* 일괄처리 패널 */}
      {showBulkPanel && selectedIds.size > 0 && (
        <div className="mb-4 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-700 rounded-xl p-4 flex items-center gap-3 flex-wrap">
          <span className="text-sm font-medium text-yellow-800 dark:text-yellow-200">
            {selectedIds.size}건 일괄 처리
          </span>
          <select
            value={bulkStatus}
            onChange={(e) => setBulkStatus(e.target.value)}
            className="border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-1.5 text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            <option value="">상태 선택</option>
            {BULK_STATUS_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>{o.label}</option>
            ))}
          </select>
          {bulkStatus === 'rejected' && (
            <input
              type="text"
              value={bulkComment}
              onChange={(e) => setBulkComment(e.target.value)}
              placeholder="반려 사유 (필수)"
              className="border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-1.5 text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500 w-48"
            />
          )}
          <button
            onClick={handleBulkStatus}
            disabled={bulkLoading}
            className="bg-primary-600 text-white px-4 py-1.5 rounded-lg text-sm font-medium hover:bg-primary-700 disabled:opacity-50"
          >
            {bulkLoading ? '처리 중...' : '적용'}
          </button>
          <button
            onClick={() => { setShowBulkPanel(false); setSelectedIds(new Set()) }}
            className="text-sm text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200"
          >
            취소
          </button>
        </div>
      )}

      {/* 필터 영역 */}
      <div className="space-y-2 mb-4">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-xs text-gray-400 dark:text-gray-500 w-12">상태</span>
          <div className="flex gap-1 flex-wrap">
            {STATUS_FILTERS.map((f) => (
              <button
                key={f.value}
                onClick={() => setStatusFilter(f.value)}
                className={`px-3 py-1 rounded-full text-xs font-medium transition ${
                  statusFilter === f.value
                    ? 'bg-primary-600 text-white'
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
              <button
                key={f.value}
                onClick={() => setPriorityFilter(f.value)}
                className={`px-3 py-1 rounded-full text-xs font-medium transition ${
                  priorityFilter === f.value
                    ? 'bg-primary-600 text-white'
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
          <input
            type="date" value={dueDateFrom}
            onChange={(e) => setDueDateFrom(e.target.value)}
            className="border border-gray-300 dark:border-gray-600 rounded-lg px-2 py-1 text-xs bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-1 focus:ring-primary-500"
          />
          <span className="text-gray-400 text-xs">~</span>
          <input
            type="date" value={dueDateTo}
            onChange={(e) => setDueDateTo(e.target.value)}
            className="border border-gray-300 dark:border-gray-600 rounded-lg px-2 py-1 text-xs bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-1 focus:ring-primary-500"
          />
          {(dueDateFrom || dueDateTo) && (
            <button onClick={() => { setDueDateFrom(''); setDueDateTo('') }} className="text-xs text-gray-400 hover:text-gray-600 dark:hover:text-gray-200">초기화</button>
          )}
          <form onSubmit={handleSearch} className="ml-auto flex gap-2 relative" ref={searchRef}>
            <div className="relative">
              <input
                type="text" value={search}
                onChange={(e) => setSearch(e.target.value)}
                onFocus={() => setShowSuggestions(true)}
                onBlur={() => setTimeout(() => setShowSuggestions(false), 150)}
                placeholder="담당자·태그·키워드 검색"
                className="border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 w-64 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
              />
              {search && (
                <button type="button" onClick={() => { setSearch(''); setPage(1); fetchTasks(activeSection, 1) }}
                  className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 text-xs">✕</button>
              )}
              {showSuggestions && recentSearches.length > 0 && (
                <div className="absolute top-full left-0 mt-1 w-full bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-lg shadow-lg z-30 overflow-hidden">
                  <p className="text-xs text-gray-400 dark:text-gray-500 px-3 pt-2 pb-1">최근 검색어</p>
                  {recentSearches.map((s) => (
                    <div key={s} onClick={() => applyRecentSearch(s)}
                      className="flex items-center justify-between px-3 py-2 text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer">
                      <span className="flex items-center gap-2">
                        <svg className="w-3 h-3 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        {s}
                      </span>
                      <button type="button" onClick={(e) => clearRecentSearch(s, e)}
                        className="text-gray-300 hover:text-gray-500 dark:hover:text-gray-200 text-xs ml-2">✕</button>
                    </div>
                  ))}
                </div>
              )}
            </div>
            <button type="submit" className="bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 px-3 py-1.5 rounded-lg text-sm hover:bg-gray-200 dark:hover:bg-gray-600 flex-shrink-0">검색</button>
          </form>
        </div>
      </div>

      {/* 업무 테이블 */}
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
        {loading ? (
          <div className="py-16 text-center text-gray-400 text-sm">불러오는 중...</div>
        ) : currentTasks.length === 0 ? (
          <div className="py-16 text-center text-gray-400 text-sm">업무가 없습니다.</div>
        ) : (
          <table className="w-full">
            <thead className="bg-gray-50 dark:bg-gray-700 text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wide">
              <tr>
                <th className="py-3 px-4 text-left w-10">
                  <input
                    type="checkbox"
                    checked={currentTasks.length > 0 && selectedIds.size === currentTasks.length}
                    onChange={toggleSelectAll}
                    className="rounded border-gray-300 dark:border-gray-600 text-primary-600 focus:ring-primary-500"
                  />
                </th>
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
                <TaskRow
                  key={task.id}
                  task={task}
                  showAssigner={currentSection?.showAssigner}
                  showAssignee={currentSection?.showAssignee}
                  selected={selectedIds.has(task.id)}
                  onSelect={toggleSelect}
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
            className="px-3 py-1.5 rounded-lg text-sm border border-gray-300 dark:border-gray-600 text-gray-600 dark:text-gray-300 disabled:opacity-40 hover:bg-gray-50 dark:hover:bg-gray-700">이전</button>
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
                  }`}>{p}</button>
              )
            )}
          <button onClick={() => setPage((p) => Math.min(totalPages, p + 1))} disabled={page >= totalPages}
            className="px-3 py-1.5 rounded-lg text-sm border border-gray-300 dark:border-gray-600 text-gray-600 dark:text-gray-300 disabled:opacity-40 hover:bg-gray-50 dark:hover:bg-gray-700">다음</button>
          <span className="text-xs text-gray-400 dark:text-gray-500 ml-2">
            {page} / {totalPages} 페이지 (총 {currentData.total}건)
          </span>
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
