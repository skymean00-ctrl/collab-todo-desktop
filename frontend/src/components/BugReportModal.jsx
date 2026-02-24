import { useState } from 'react'
import api from '../utils/api'

const SEVERITY_OPTIONS = [
  { value: 'low',      label: '낮음',   color: 'text-gray-500',   bg: 'bg-gray-100 dark:bg-gray-700' },
  { value: 'normal',   label: '보통',   color: 'text-blue-600',   bg: 'bg-blue-50 dark:bg-blue-900/30' },
  { value: 'high',     label: '심각',   color: 'text-orange-600', bg: 'bg-orange-50 dark:bg-orange-900/30' },
  { value: 'critical', label: '치명적', color: 'text-red-600',    bg: 'bg-red-50 dark:bg-red-900/30' },
]

const PAGE_OPTIONS = [
  '대시보드', '업무 상세', '업무 등록', '관리자', '로그인/회원가입', '알림', '설정', '기타',
]

export default function BugReportModal({ onClose }) {
  const [form, setForm] = useState({
    title: '',
    description: '',
    page: '',
    steps: '',
    severity: 'normal',
  })
  const [loading, setLoading] = useState(false)
  const [done, setDone] = useState(false)
  const [error, setError] = useState('')

  const inputCls = 'w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100'

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await api.post('/api/bug-reports/', form)
      setDone(true)
    } catch (err) {
      setError(err.response?.data?.detail || '전송에 실패했습니다. 다시 시도해주세요.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
        {/* 헤더 */}
        <div className="p-6 border-b border-gray-100 dark:border-gray-700 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-xl">🐛</span>
            <h2 className="font-bold text-lg text-gray-900 dark:text-gray-100">오류 신고</h2>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 text-xl">✕</button>
        </div>

        {done ? (
          /* 전송 완료 */
          <div className="p-8 text-center">
            <div className="w-16 h-16 bg-green-100 dark:bg-green-900/30 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100 mb-2">접수 완료!</h3>
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-6">
              오류 신고가 접수됐습니다.<br />관리자가 확인 후 처리할 예정입니다.
            </p>
            <button
              onClick={onClose}
              className="px-6 py-2 bg-primary-600 text-white rounded-lg font-medium hover:bg-primary-700 transition"
            >
              닫기
            </button>
          </div>
        ) : (
          /* 신고 폼 */
          <form onSubmit={handleSubmit} className="p-6 space-y-4">
            {/* 제목 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                오류 제목 <span className="text-red-500">*</span>
              </label>
              <input
                required
                type="text"
                value={form.title}
                onChange={(e) => setForm({ ...form, title: e.target.value })}
                className={inputCls}
                placeholder="예: 담당자 드롭다운이 비어있음"
              />
            </div>

            {/* 발생 페이지 + 심각도 */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">발생 위치</label>
                <select
                  value={form.page}
                  onChange={(e) => setForm({ ...form, page: e.target.value })}
                  className={inputCls}
                >
                  <option value="">선택 (선택사항)</option>
                  {PAGE_OPTIONS.map((p) => (
                    <option key={p} value={p}>{p}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">심각도</label>
                <div className="flex gap-1 flex-wrap">
                  {SEVERITY_OPTIONS.map((s) => (
                    <button
                      key={s.value}
                      type="button"
                      onClick={() => setForm({ ...form, severity: s.value })}
                      className={`px-2 py-1 rounded-md text-xs font-medium border transition ${
                        form.severity === s.value
                          ? `${s.bg} ${s.color} border-current`
                          : 'bg-white dark:bg-gray-700 text-gray-500 dark:text-gray-400 border-gray-200 dark:border-gray-600'
                      }`}
                    >
                      {s.label}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* 오류 설명 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                오류 설명 <span className="text-red-500">*</span>
              </label>
              <textarea
                required
                value={form.description}
                onChange={(e) => setForm({ ...form, description: e.target.value })}
                rows={3}
                className={inputCls}
                placeholder="어떤 오류가 발생했는지 설명해주세요."
              />
            </div>

            {/* 재현 단계 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                재현 방법 <span className="text-xs text-gray-400">(선택사항)</span>
              </label>
              <textarea
                value={form.steps}
                onChange={(e) => setForm({ ...form, steps: e.target.value })}
                rows={2}
                className={inputCls}
                placeholder="예: 1. 업무 등록 클릭 2. 담당자 드롭다운 클릭 3. 목록 없음"
              />
            </div>

            {error && (
              <p className="text-sm text-red-500 dark:text-red-400">{error}</p>
            )}

            <div className="flex gap-3 pt-1">
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
                className="flex-1 py-2 bg-red-600 text-white rounded-lg text-sm font-medium hover:bg-red-700 disabled:opacity-50 transition"
              >
                {loading ? '전송 중...' : '신고하기'}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  )
}
