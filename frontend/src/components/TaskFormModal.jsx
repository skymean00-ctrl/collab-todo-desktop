import { useState, useEffect } from 'react'
import api from '../utils/api'

const PRIORITY_OPTIONS = [
  { value: 'urgent', label: '긴급', color: 'text-red-600' },
  { value: 'high', label: '높음', color: 'text-orange-500' },
  { value: 'normal', label: '보통', color: 'text-blue-500' },
  { value: 'low', label: '낮음', color: 'text-gray-400' },
]

export default function TaskFormModal({ onClose, onCreated, parentTaskId = null }) {
  const [users, setUsers] = useState([])
  const [categories, setCategories] = useState([])
  const [form, setForm] = useState({
    title: '',
    content: '',
    assignee_id: '',
    category_id: '',
    priority: 'normal',
    estimated_hours: '',
    due_date: '',
    tag_names: '',
    is_subtask: !!parentTaskId,
    parent_task_id: parentTaskId,
    // 흐름2: 자료제공자 직접 지정
    material_providers: [],
  })
  const [assignmentMode, setAssignmentMode] = useState('single') // 'single' | 'multi'
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    api.get('/api/users/').then(({ data }) => setUsers(data))
    api.get('/api/categories/').then(({ data }) => setCategories(data))
  }, [])

  function addMaterialProvider() {
    setForm((f) => ({
      ...f,
      material_providers: [...f.material_providers, { assignee_id: '', title: '', due_date: '' }],
    }))
  }

  function updateProvider(idx, field, value) {
    setForm((f) => {
      const providers = [...f.material_providers]
      providers[idx] = { ...providers[idx], [field]: value }
      return { ...f, material_providers: providers }
    })
  }

  function removeProvider(idx) {
    setForm((f) => ({
      ...f,
      material_providers: f.material_providers.filter((_, i) => i !== idx),
    }))
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const payload = {
        title: form.title,
        content: form.content || null,
        assignee_id: parseInt(form.assignee_id),
        category_id: form.category_id ? parseInt(form.category_id) : null,
        priority: form.priority,
        estimated_hours: form.estimated_hours ? parseFloat(form.estimated_hours) : null,
        due_date: form.due_date || null,
        tag_names: form.tag_names ? form.tag_names.split(',').map((t) => t.trim()).filter(Boolean) : [],
        is_subtask: form.is_subtask,
        parent_task_id: form.parent_task_id || null,
        material_providers: assignmentMode === 'multi'
          ? form.material_providers
              .filter((p) => p.assignee_id && p.title)
              .map((p) => ({
                assignee_id: parseInt(p.assignee_id),
                title: p.title,
                due_date: p.due_date || null,
              }))
          : [],
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

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b flex items-center justify-between">
          <h2 className="font-bold text-lg">{parentTaskId ? '자료 요청 등록' : '업무 지시 등록'}</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl">✕</button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {/* 업무 제목 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">업무 제목 *</label>
            <input
              required
              type="text"
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
              placeholder="업무 제목을 입력하세요"
            />
          </div>

          {/* 업무 내용 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">업무 내용</label>
            <textarea
              value={form.content}
              onChange={(e) => setForm({ ...form, content: e.target.value })}
              rows={3}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
              placeholder="업무 내용을 입력하세요"
            />
          </div>

          {/* 배정 방식 (최상위 업무에서만) */}
          {!parentTaskId && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">배정 방식</label>
              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={() => setAssignmentMode('single')}
                  className={`flex-1 py-2 rounded-lg text-sm border transition ${
                    assignmentMode === 'single'
                      ? 'bg-primary-600 text-white border-primary-600'
                      : 'bg-white text-gray-600 border-gray-300 hover:border-primary-400'
                  }`}
                >
                  단일 담당자
                  <span className="block text-xs opacity-70">담당자가 직접 자료 요청</span>
                </button>
                <button
                  type="button"
                  onClick={() => setAssignmentMode('multi')}
                  className={`flex-1 py-2 rounded-lg text-sm border transition ${
                    assignmentMode === 'multi'
                      ? 'bg-primary-600 text-white border-primary-600'
                      : 'bg-white text-gray-600 border-gray-300 hover:border-primary-400'
                  }`}
                >
                  주담당 + 자료제공자
                  <span className="block text-xs opacity-70">지시자가 직접 자료제공자 지정</span>
                </button>
              </div>
            </div>
          )}

          {/* 주 담당자 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {assignmentMode === 'multi' ? '주 담당자 *' : '담당자 *'}
            </label>
            <select
              required
              value={form.assignee_id}
              onChange={(e) => setForm({ ...form, assignee_id: e.target.value })}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="">담당자 선택</option>
              {users.map((u) => (
                <option key={u.id} value={u.id}>
                  {u.name} ({u.department} · {u.job_title})
                </option>
              ))}
            </select>
          </div>

          {/* 자료제공자 (흐름2) */}
          {assignmentMode === 'multi' && (
            <div className="border border-dashed border-primary-300 rounded-xl p-4 bg-primary-50 space-y-3">
              <div className="flex items-center justify-between">
                <label className="text-sm font-medium text-primary-700">자료제공자</label>
                <button
                  type="button"
                  onClick={addMaterialProvider}
                  className="text-sm text-primary-600 hover:text-primary-800 font-medium"
                >
                  + 추가
                </button>
              </div>
              {form.material_providers.map((mp, idx) => (
                <div key={idx} className="flex gap-2 items-start">
                  <select
                    value={mp.assignee_id}
                    onChange={(e) => updateProvider(idx, 'assignee_id', e.target.value)}
                    className="border border-gray-300 rounded-lg px-2 py-1.5 text-sm flex-1 focus:outline-none focus:ring-2 focus:ring-primary-500"
                  >
                    <option value="">담당자</option>
                    {users.map((u) => (
                      <option key={u.id} value={u.id}>
                        {u.name} ({u.job_title})
                      </option>
                    ))}
                  </select>
                  <input
                    type="text"
                    placeholder="요청 자료명"
                    value={mp.title}
                    onChange={(e) => updateProvider(idx, 'title', e.target.value)}
                    className="border border-gray-300 rounded-lg px-2 py-1.5 text-sm flex-1 focus:outline-none focus:ring-2 focus:ring-primary-500"
                  />
                  <input
                    type="date"
                    value={mp.due_date}
                    onChange={(e) => updateProvider(idx, 'due_date', e.target.value)}
                    className="border border-gray-300 rounded-lg px-2 py-1.5 text-sm w-36 focus:outline-none focus:ring-2 focus:ring-primary-500"
                  />
                  <button type="button" onClick={() => removeProvider(idx)} className="text-red-400 hover:text-red-600">✕</button>
                </div>
              ))}
              {form.material_providers.length === 0 && (
                <p className="text-xs text-primary-500">+ 추가 버튼으로 자료제공자를 지정하세요</p>
              )}
            </div>
          )}

          {/* 2열 그리드: 우선순위, 카테고리 */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">우선순위</label>
              <select
                value={form.priority}
                onChange={(e) => setForm({ ...form, priority: e.target.value })}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                {PRIORITY_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">카테고리</label>
              <select
                value={form.category_id}
                onChange={(e) => setForm({ ...form, category_id: e.target.value })}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                <option value="">선택 안함</option>
                {categories.map((c) => (
                  <option key={c.id} value={c.id}>{c.name}</option>
                ))}
              </select>
            </div>
          </div>

          {/* 2열 그리드: 마감일, 예상시간 */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">마감일</label>
              <input
                type="date"
                value={form.due_date}
                onChange={(e) => setForm({ ...form, due_date: e.target.value })}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">예상 소요시간 (h)</label>
              <input
                type="number"
                min="0"
                step="0.5"
                value={form.estimated_hours}
                onChange={(e) => setForm({ ...form, estimated_hours: e.target.value })}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
                placeholder="예: 4.5"
              />
            </div>
          </div>

          {/* 태그 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">태그 (쉼표로 구분)</label>
            <input
              type="text"
              value={form.tag_names}
              onChange={(e) => setForm({ ...form, tag_names: e.target.value })}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
              placeholder="예: 보고서, 월간, 영업"
            />
          </div>

          {error && <p className="text-red-500 text-sm">{error}</p>}

          <div className="flex gap-3 pt-2">
            <button type="button" onClick={onClose} className="flex-1 py-2 border border-gray-300 rounded-lg text-sm hover:bg-gray-50">
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
