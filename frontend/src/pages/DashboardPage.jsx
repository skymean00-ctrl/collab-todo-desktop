import { useState, useEffect, useCallback } from 'react'
import api from '../utils/api'
import TaskRow from '../components/TaskRow'
import TaskFormModal from '../components/TaskFormModal'

const SECTIONS = [
  { key: 'assigned_to_me', label: '내가 받은 업무', showAssigner: true },
  { key: 'assigned_by_me', label: '내가 지시한 업무', showAssignee: true },
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

export default function DashboardPage() {
  const [summary, setSummary] = useState(null)
  const [tasks, setTasks] = useState({})
  const [activeSection, setActiveSection] = useState('assigned_to_me')
  const [statusFilter, setStatusFilter] = useState('')
  const [search, setSearch] = useState('')
  const [showModal, setShowModal] = useState(false)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    fetchSummary()
  }, [])

  useEffect(() => {
    fetchTasks(activeSection)
  }, [activeSection, statusFilter])

  async function fetchSummary() {
    const { data } = await api.get('/api/tasks/dashboard')
    setSummary(data)
  }

  const fetchTasks = useCallback(async (section) => {
    setLoading(true)
    try {
      const params = new URLSearchParams({ section })
      if (statusFilter) params.append('status', statusFilter)
      if (search) params.append('search', search)
      const { data } = await api.get(`/api/tasks/?${params}`)
      setTasks((prev) => ({ ...prev, [section]: data }))
    } finally {
      setLoading(false)
    }
  }, [statusFilter, search])

  function handleSearch(e) {
    e.preventDefault()
    fetchTasks(activeSection)
  }

  function onTaskCreated() {
    fetchSummary()
    fetchTasks(activeSection)
  }

  const currentTasks = tasks[activeSection] || []
  const currentSection = SECTIONS.find((s) => s.key === activeSection)

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* 요약 카드 */}
      {summary && (
        <div className="grid grid-cols-4 gap-4 mb-6">
          <SummaryCard label="내 전체 업무" value={summary.total} color="text-primary-600" bg="bg-primary-50 dark:bg-primary-900/30" />
          <SummaryCard label="긴급 업무" value={summary.urgent} color="text-red-600 dark:text-red-400" bg="bg-red-50 dark:bg-red-900/30" />
          <SummaryCard label="마감 임박 (3일)" value={summary.due_soon} color="text-orange-600 dark:text-orange-400" bg="bg-orange-50 dark:bg-orange-900/30" />
          <SummaryCard label="반려된 업무" value={summary.rejected} color="text-gray-600 dark:text-gray-300" bg="bg-gray-100 dark:bg-gray-700" />
        </div>
      )}

      {/* 섹션 탭 + 업무 등록 버튼 */}
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
                  {tasks[s.key].length}
                </span>
              )}
            </button>
          ))}
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="bg-primary-600 text-white px-4 py-2 rounded-xl text-sm font-medium hover:bg-primary-700 transition flex items-center gap-1"
        >
          + 업무 등록
        </button>
      </div>

      {/* 필터 + 검색 */}
      <div className="flex items-center gap-3 mb-4">
        <div className="flex gap-1">
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
        <form onSubmit={handleSearch} className="ml-auto flex gap-2">
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="제목 검색..."
            className="border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 w-48 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
          />
          <button type="submit" className="bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 px-3 py-1.5 rounded-lg text-sm hover:bg-gray-200 dark:hover:bg-gray-600">
            검색
          </button>
        </form>
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
                />
              ))}
            </tbody>
          </table>
        )}
      </div>

      {showModal && (
        <TaskFormModal
          onClose={() => setShowModal(false)}
          onCreated={onTaskCreated}
        />
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
