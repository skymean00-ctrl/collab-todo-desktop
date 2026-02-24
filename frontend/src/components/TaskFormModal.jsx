import { useState, useEffect, useRef } from 'react'
import api from '../utils/api'

const PRIORITY_OPTIONS = [
  { value: 'urgent', label: '긴급', color: 'text-red-600' },
  { value: 'high', label: '높음', color: 'text-orange-500' },
  { value: 'normal', label: '보통', color: 'text-blue-500' },
  { value: 'low', label: '낮음', color: 'text-gray-400' },
]

const STOP_WORDS = new Set([
  '및','또는','그리고','하지만','때문에','위해','대한','관련','통해','따른','있는','없는',
  '하는','되는','이는','그','이','저','우리','여기','거기','이것','저것','무엇','어떤',
  '모든','각','해당','등','기타','관한','에서','으로','부터','까지','와','과','을','를',
  '이','가','은','는','도','만','도','라','이라','으로서','로서','으로써','로써','에게',
  '에서','에게서','한테','한테서','께','께서','의','과','와','이나','나','이란','란',
  '이며','며','이고','고','이라도','라도','이든지','든지','이든','든','이면','면',
  '보다','처럼','만큼','대로','마다','마저','조차','까지도','라도','이라도',
  '있습니다','합니다','입니다','됩니다','있다','없다','하다','되다','이다','아니다',
  '해야','할','하여','했','하고','하면','할때','했을','하기','하게','해서',
])

function extractKeywords(text) {
  if (!text) return []
  const words = text
    .replace(/[^\w\sㄱ-ㅎㅏ-ㅣ가-힣]/g, ' ')
    .split(/\s+/)
    .map((w) => w.trim())
    .filter((w) => w.length >= 2 && !STOP_WORDS.has(w))
  const freq = {}
  words.forEach((w) => { freq[w] = (freq[w] || 0) + 1 })
  return Object.entries(freq)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 8)
    .map(([w]) => w)
}

export default function TaskFormModal({ onClose, onCreated, parentTaskId = null }) {
  const [users, setUsers] = useState([])
  const [form, setForm] = useState({
    title: '',
    content: '',
    assignee_id: '',
    priority: 'normal',
    due_date: '',
    tag_names: '',
    is_subtask: !!parentTaskId,
    parent_task_id: parentTaskId,
  })
  const [tagSuggestions, setTagSuggestions] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [usersError, setUsersError] = useState(false)
  // 담당자 검색 콤보박스
  const [assigneeSearch, setAssigneeSearch] = useState('')
  const [showUserList, setShowUserList] = useState(false)
  const assigneeRef = useRef(null)

  useEffect(() => {
    loadUsers()
    // 외부 클릭 시 담당자 목록 닫기
    function handleClickOutside(e) {
      if (assigneeRef.current && !assigneeRef.current.contains(e.target)) {
        setShowUserList(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  function loadUsers() {
    setUsersError(false)
    api.get('/api/users/')
      .then(({ data }) => setUsers(data))
      .catch(() => setUsersError(true))
  }

  // 담당자 선택 처리
  function selectAssignee(u) {
    setForm({ ...form, assignee_id: String(u.id) })
    setAssigneeSearch(u.name + (u.department ? ` (${u.department})` : ''))
    setShowUserList(false)
  }

  // 검색어로 필터된 사용자 목록
  const filteredUsers = users.filter((u) => {
    const q = assigneeSearch.toLowerCase()
    return (
      u.name.toLowerCase().includes(q) ||
      (u.department && u.department.toLowerCase().includes(q))
    )
  })

  function autoExtractTags() {
    const keywords = extractKeywords(form.title + ' ' + form.content)
    const existing = form.tag_names.split(',').map((t) => t.trim()).filter(Boolean)
    const newSuggestions = keywords.filter((k) => !existing.includes(k))
    setTagSuggestions(newSuggestions)
  }

  function addSuggestedTag(tag) {
    const existing = form.tag_names.split(',').map((t) => t.trim()).filter(Boolean)
    if (!existing.includes(tag)) {
      const newTags = [...existing, tag].join(', ')
      setForm({ ...form, tag_names: newTags })
    }
    setTagSuggestions((s) => s.filter((t) => t !== tag))
  }

  async function handleSubmit(e) {
    e.preventDefault()
    if (!form.assignee_id) {
      setError('담당자를 선택해주세요.')
      return
    }
    setError('')
    setLoading(true)
    try {
      const payload = {
        title: form.title,
        content: form.content || null,
        assignee_id: parseInt(form.assignee_id),
        priority: form.priority,
        due_date: form.due_date || null,
        tag_names: form.tag_names ? form.tag_names.split(',').map((t) => t.trim()).filter(Boolean) : [],
        is_subtask: form.is_subtask,
        parent_task_id: form.parent_task_id || null,
        category_id: null,
        estimated_hours: null,
        material_providers: [],
      }
      await api.post('/api/tasks/', payload)
      onCreated()
      onClose()
    } catch (err) {
      setError(err.response?.data?.detail || '업무 생성에 실패했습니다.')
    } finally {
      setLoading(false)
    }
  }

  const inputCls = 'w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100'

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b border-gray-100 dark:border-gray-700 flex items-center justify-between">
          <h2 className="font-bold text-lg text-gray-900 dark:text-gray-100">
            {parentTaskId ? '자료 요청 등록' : '업무 요청 등록'}
          </h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 text-xl">✕</button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {/* 업무 제목 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">업무 제목 *</label>
            <input
              required
              type="text"
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
              className={inputCls}
              placeholder="업무 제목을 입력하세요"
            />
          </div>

          {/* 업무 내용 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">업무 내용</label>
            <textarea
              value={form.content}
              onChange={(e) => setForm({ ...form, content: e.target.value })}
              rows={3}
              className={inputCls}
              placeholder="업무 내용을 입력하세요"
            />
          </div>

          {/* 담당자 검색 + 드롭다운 */}
          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">담당자 *</label>
              {usersError && (
                <button type="button" onClick={loadUsers} className="text-xs text-primary-600 dark:text-primary-400 hover:underline">
                  다시 불러오기
                </button>
              )}
            </div>
            {usersError ? (
              <div className="text-sm text-red-500 dark:text-red-400 py-2 px-3 bg-red-50 dark:bg-red-900/20 rounded-lg">
                사용자 목록을 불러오지 못했습니다.{' '}
                <button type="button" onClick={loadUsers} className="underline font-medium">재시도</button>
              </div>
            ) : (
              <div className="relative" ref={assigneeRef}>
                {/* 숨겨진 required 체크용 input */}
                <input type="hidden" required value={form.assignee_id} />
                {/* 검색 입력 */}
                <input
                  type="text"
                  value={assigneeSearch}
                  onChange={(e) => {
                    setAssigneeSearch(e.target.value)
                    setForm({ ...form, assignee_id: '' })
                    setShowUserList(true)
                  }}
                  onFocus={() => setShowUserList(true)}
                  placeholder={users.length === 0 ? '불러오는 중...' : '이름 또는 부서로 검색...'}
                  className={inputCls}
                  autoComplete="off"
                />
                {/* 선택됨 표시 아이콘 */}
                {form.assignee_id && (
                  <span className="absolute right-3 top-1/2 -translate-y-1/2 text-green-500 text-sm">✓</span>
                )}
                {/* 드롭다운 목록 */}
                {showUserList && (
                  <div className="absolute z-10 w-full mt-1 bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg shadow-lg max-h-48 overflow-y-auto">
                    {filteredUsers.length === 0 ? (
                      <div className="px-3 py-2 text-sm text-gray-400">
                        {users.length === 0 ? '불러오는 중...' : '검색 결과 없음'}
                      </div>
                    ) : (
                      filteredUsers.map((u) => (
                        <button
                          key={u.id}
                          type="button"
                          onClick={() => selectAssignee(u)}
                          className={`w-full text-left px-3 py-2 text-sm hover:bg-primary-50 dark:hover:bg-primary-900/30 flex items-center justify-between ${
                            form.assignee_id === String(u.id)
                              ? 'bg-primary-50 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300'
                              : 'text-gray-700 dark:text-gray-200'
                          }`}
                        >
                          <span>{u.name}</span>
                          {u.department && (
                            <span className="text-xs text-gray-400 dark:text-gray-500">{u.department}</span>
                          )}
                        </button>
                      ))
                    )}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* 2열: 우선순위, 마감일 */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">우선순위</label>
              <select
                value={form.priority}
                onChange={(e) => setForm({ ...form, priority: e.target.value })}
                className={inputCls}
              >
                {PRIORITY_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">마감일</label>
              <input
                type="date"
                value={form.due_date}
                onChange={(e) => setForm({ ...form, due_date: e.target.value })}
                className={inputCls}
              />
            </div>
          </div>

          {/* 태그 */}
          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">태그</label>
              <button
                type="button"
                onClick={autoExtractTags}
                className="text-xs text-primary-600 dark:text-primary-400 hover:underline"
              >
                자동 추출
              </button>
            </div>
            <input
              type="text"
              value={form.tag_names}
              onChange={(e) => setForm({ ...form, tag_names: e.target.value })}
              className={inputCls}
              placeholder="예: 보고서, 월간, 영업 (쉼표로 구분)"
            />
            {tagSuggestions.length > 0 && (
              <div className="mt-2 flex flex-wrap gap-1.5">
                <span className="text-xs text-gray-400 self-center">추천:</span>
                {tagSuggestions.map((tag) => (
                  <button
                    key={tag}
                    type="button"
                    onClick={() => addSuggestedTag(tag)}
                    className="text-xs px-2 py-0.5 bg-primary-50 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300 border border-primary-200 dark:border-primary-700 rounded-full hover:bg-primary-100 dark:hover:bg-primary-800/50"
                  >
                    + {tag}
                  </button>
                ))}
              </div>
            )}
          </div>

          {error && <p className="text-red-500 text-sm">{error}</p>}

          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700"
            >
              취소
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex-1 py-2 bg-primary-600 text-white rounded-lg text-sm font-medium hover:bg-primary-700 disabled:opacity-50"
            >
              {loading ? '등록 중...' : '업무 등록'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
