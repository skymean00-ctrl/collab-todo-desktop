import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import api, { getApiBase } from '../utils/api'
import useAuthStore from '../store/authStore'
import TaskFormModal from '../components/TaskFormModal'

const STATUS_FLOW = {
  pending:     { label: '대기',     next: [{ value: 'in_progress', label: '진행 시작' }] },
  in_progress: { label: '진행중',   next: [{ value: 'review', label: '검토 요청' }] },
  review:      { label: '검토요청', next: [{ value: 'approved', label: '승인(완료)' }, { value: 'rejected', label: '반려' }] },
  approved:    { label: '완료',     next: [] },
  rejected:    { label: '반려',     next: [{ value: 'in_progress', label: '재진행' }] },
}

const STATUS_CLS = {
  pending:     'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-300',
  in_progress: 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-400',
  review:      'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/40 dark:text-yellow-400',
  approved:    'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-400',
  rejected:    'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-400',
}

export default function TaskDetailPage() {
  const { taskId } = useParams()
  const navigate = useNavigate()
  const { user } = useAuthStore()
  const [task, setTask] = useState(null)
  const [logs, setLogs] = useState([])
  const [comment, setComment] = useState('')
  const [progress, setProgress] = useState(0)
  const [showSubtaskModal, setShowSubtaskModal] = useState(false)
  const [uploading, setUploading] = useState(false)

  useEffect(() => {
    loadTask()
    loadLogs()
  }, [taskId])

  async function loadTask() {
    const { data } = await api.get(`/api/tasks/${taskId}`)
    setTask(data)
    setProgress(data.progress)
  }

  async function loadLogs() {
    const { data } = await api.get(`/api/tasks/${taskId}/logs`)
    setLogs(data)
  }

  async function changeStatus(newStatus) {
    await api.post(`/api/tasks/${taskId}/status`, { status: newStatus, comment: comment || null })
    setComment('')
    loadTask()
    loadLogs()
  }

  async function updateProgress() {
    await api.patch(`/api/tasks/${taskId}`, { progress })
    loadTask()
  }

  async function handleFileUpload(e) {
    const file = e.target.files[0]
    if (!file) return
    setUploading(true)
    const formData = new FormData()
    formData.append('file', file)
    await api.post(`/api/attachments/${taskId}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    setUploading(false)
    loadTask()
  }

  async function downloadFile(attachment) {
    const url = `${getApiBase()}/api/attachments/${attachment.id}/download`
    const token = localStorage.getItem('access_token')
    if (window.electronAPI) {
      const result = await window.electronAPI.downloadFile({ url, filename: attachment.filename, token })
      if (result?.success) {
        alert(`저장 완료: ${result.filePath}`)
      }
    } else {
      // 브라우저: Authorization 헤더와 함께 fetch → Blob URL로 다운로드
      const res = await fetch(url, { headers: { Authorization: `Bearer ${token}` } })
      if (!res.ok) { alert('다운로드에 실패했습니다.'); return }
      const blob = await res.blob()
      const blobUrl = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = blobUrl
      a.download = attachment.filename
      a.click()
      URL.revokeObjectURL(blobUrl)
    }
  }

  if (!task) return <div className="p-8 text-center text-gray-400">불러오는 중...</div>

  const flow = STATUS_FLOW[task.status] || { label: task.status, next: [] }
  const isAssigner = user?.id === task.assigner?.id
  const isAssignee = user?.id === task.assignee?.id
  const canChangeStatus =
    (isAssignee && ['pending', 'in_progress', 'rejected'].includes(task.status)) ||
    (isAssigner && task.status === 'review')

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <button onClick={() => navigate(-1)} className="text-sm text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 mb-4 flex items-center gap-1">
        ← 목록으로
      </button>

      <div className="grid grid-cols-3 gap-6">
        {/* 왼쪽: 업무 상세 */}
        <div className="col-span-2 space-y-4">
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700 p-6">
            <div className="flex items-start justify-between mb-4">
              <h1 className="text-xl font-bold text-gray-900 dark:text-gray-100">{task.title}</h1>
              <span className={`text-sm px-3 py-1 rounded-full font-medium ${STATUS_CLS[task.status]}`}>
                {flow.label}
              </span>
            </div>

            {task.content && (
              <p className="text-sm text-gray-600 dark:text-gray-300 mb-4 whitespace-pre-wrap">{task.content}</p>
            )}

            <div className="grid grid-cols-2 gap-3 text-sm">
              <MetaItem label="지시자" value={task.assigner?.name} />
              <MetaItem label="담당자" value={task.assignee?.name} />
              <MetaItem label="마감일" value={task.due_date || '-'} />
              <MetaItem label="예상시간" value={task.estimated_hours ? `${task.estimated_hours}h` : '-'} />
              <MetaItem label="카테고리" value={task.category?.name || '-'} />
              <MetaItem label="우선순위" value={task.priority} />
            </div>

            {task.tags?.length > 0 && (
              <div className="mt-3 flex flex-wrap gap-1">
                {task.tags.map((t) => (
                  <span key={t.id} className="text-xs bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 px-2 py-0.5 rounded-full">#{t.name}</span>
                ))}
              </div>
            )}
          </div>

          {/* 진행률 */}
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700 p-4">
            <label className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block">진행률: {progress}%</label>
            <div className="flex items-center gap-3">
              <input
                type="range"
                min="0"
                max="100"
                step="5"
                value={progress}
                onChange={(e) => setProgress(parseInt(e.target.value))}
                className="flex-1"
              />
              {isAssignee && progress !== task.progress && (
                <button onClick={updateProgress} className="text-sm bg-primary-600 text-white px-3 py-1 rounded-lg hover:bg-primary-700">
                  저장
                </button>
              )}
            </div>
            <div className="mt-1.5 bg-gray-200 dark:bg-gray-600 rounded-full h-2">
              <div className="bg-primary-500 h-2 rounded-full transition-all" style={{ width: `${progress}%` }} />
            </div>
          </div>

          {/* 자료요청 서브태스크 */}
          {(task.subtasks?.length > 0 || isAssignee) && (
            <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700 p-4">
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-semibold text-gray-700 dark:text-gray-300 text-sm">자료요청</h3>
                {isAssignee && (
                  <button
                    onClick={() => setShowSubtaskModal(true)}
                    className="text-xs text-primary-600 dark:text-primary-400 hover:text-primary-800 dark:hover:text-primary-200 font-medium"
                  >
                    + 자료 요청 추가
                  </button>
                )}
              </div>
              {task.subtasks?.length === 0 ? (
                <p className="text-xs text-gray-400">아직 자료요청이 없습니다.</p>
              ) : (
                <div className="space-y-2">
                  {task.subtasks.map((s) => (
                    <div
                      key={s.id}
                      className="flex items-center justify-between py-2 px-3 bg-gray-50 dark:bg-gray-700 rounded-lg cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-600"
                      onClick={() => navigate(`/tasks/${s.id}`)}
                    >
                      <span className="text-sm text-gray-700 dark:text-gray-200">{s.title}</span>
                      <span className={`text-xs px-2 py-0.5 rounded-full ${STATUS_CLS[s.status]}`}>
                        {STATUS_FLOW[s.status]?.label || s.status}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* 첨부파일 */}
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700 p-4">
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-semibold text-gray-700 dark:text-gray-300 text-sm">첨부파일</h3>
              <label className="text-xs text-primary-600 dark:text-primary-400 hover:text-primary-800 dark:hover:text-primary-200 font-medium cursor-pointer">
                {uploading ? '업로드 중...' : '+ 파일 첨부'}
                <input type="file" className="hidden" onChange={handleFileUpload} disabled={uploading} />
              </label>
            </div>
            {task.attachments?.length === 0 ? (
              <p className="text-xs text-gray-400">첨부된 파일이 없습니다.</p>
            ) : (
              <div className="space-y-1">
                {task.attachments.map((a) => (
                  <div key={a.id} className="flex items-center justify-between py-1.5 px-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                    <div>
                      <span className="text-sm text-gray-700 dark:text-gray-200">{a.filename}</span>
                      <span className="text-xs text-gray-400 ml-2">{formatSize(a.file_size)}</span>
                    </div>
                    <button
                      onClick={() => downloadFile(a)}
                      className="text-xs text-primary-600 dark:text-primary-400 hover:text-primary-800 dark:hover:text-primary-200 font-medium"
                    >
                      다운로드
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* 오른쪽: 상태 변경 + 이력 */}
        <div className="space-y-4">
          {canChangeStatus && flow.next.length > 0 && (
            <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700 p-4">
              <h3 className="font-semibold text-gray-700 dark:text-gray-300 text-sm mb-3">상태 변경</h3>
              <textarea
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                placeholder="코멘트 (선택사항)"
                rows={2}
                className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm mb-3 focus:outline-none focus:ring-2 focus:ring-primary-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
              />
              <div className="space-y-2">
                {flow.next.map((n) => (
                  <button
                    key={n.value}
                    onClick={() => changeStatus(n.value)}
                    className={`w-full py-2 rounded-lg text-sm font-medium transition ${
                      n.value === 'rejected'
                        ? 'bg-red-50 dark:bg-red-900/30 text-red-700 dark:text-red-400 hover:bg-red-100 dark:hover:bg-red-900/50 border border-red-200 dark:border-red-800'
                        : n.value === 'approved'
                        ? 'bg-green-50 dark:bg-green-900/30 text-green-700 dark:text-green-400 hover:bg-green-100 dark:hover:bg-green-900/50 border border-green-200 dark:border-green-800'
                        : 'bg-primary-50 dark:bg-primary-900/30 text-primary-700 dark:text-primary-400 hover:bg-primary-100 dark:hover:bg-primary-900/50 border border-primary-200 dark:border-primary-800'
                    }`}
                  >
                    {n.label}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* 이력 로그 */}
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700 p-4">
            <h3 className="font-semibold text-gray-700 dark:text-gray-300 text-sm mb-3">이력</h3>
            {logs.length === 0 ? (
              <p className="text-xs text-gray-400">이력이 없습니다.</p>
            ) : (
              <div className="space-y-2">
                {logs.map((log) => (
                  <div key={log.id} className="text-xs border-l-2 border-gray-200 dark:border-gray-600 pl-3 py-1">
                    <p className="text-gray-700 dark:text-gray-200 font-medium">{log.user?.name}</p>
                    <p className="text-gray-500 dark:text-gray-400">{formatAction(log)}</p>
                    {log.comment && <p className="text-gray-600 dark:text-gray-300 mt-0.5 italic">"{log.comment}"</p>}
                    <p className="text-gray-400 dark:text-gray-500 mt-0.5">{new Date(log.created_at).toLocaleString('ko-KR')}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {showSubtaskModal && (
        <TaskFormModal
          parentTaskId={parseInt(taskId)}
          onClose={() => setShowSubtaskModal(false)}
          onCreated={() => { loadTask(); loadLogs() }}
        />
      )}
    </div>
  )
}

function MetaItem({ label, value }) {
  return (
    <div>
      <span className="text-gray-400 dark:text-gray-500 text-xs">{label}</span>
      <p className="text-gray-700 dark:text-gray-200 font-medium">{value}</p>
    </div>
  )
}

function formatSize(bytes) {
  if (!bytes) return ''
  if (bytes < 1024) return `${bytes}B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)}KB`
  return `${(bytes / 1024 / 1024).toFixed(1)}MB`
}

function formatAction(log) {
  const map = {
    created: '업무 생성',
    updated: '업무 수정',
    status_changed: `상태 변경: ${log.old_value} → ${log.new_value}`,
  }
  return map[log.action] || log.action
}
