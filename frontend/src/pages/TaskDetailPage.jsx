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

const IMAGE_TYPES = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp', 'image/bmp', 'image/svg+xml']

export default function TaskDetailPage() {
  const { taskId } = useParams()
  const navigate = useNavigate()
  const { user } = useAuthStore()
  const [task, setTask] = useState(null)
  const [logs, setLogs] = useState([])
  const [statusComment, setStatusComment] = useState('')
  const [newComment, setNewComment] = useState('')
  const [progress, setProgress] = useState(0)
  const [showSubtaskModal, setShowSubtaskModal] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [cloning, setCloning] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [loadError, setLoadError] = useState(null)

  // 담당자 변경
  const [showReassign, setShowReassign] = useState(false)
  const [users, setUsers] = useState([])
  const [newAssigneeId, setNewAssigneeId] = useState('')
  const [assigneeSearch, setAssigneeSearch] = useState('')
  const [showUserList, setShowUserList] = useState(false)

  // 댓글 수정
  const [editingLogId, setEditingLogId] = useState(null)
  const [editingText, setEditingText] = useState('')

  // 이미지 미리보기
  const [previewUrl, setPreviewUrl] = useState(null)
  const [previewName, setPreviewName] = useState('')

  useEffect(() => {
    loadTask()
    loadLogs()
  }, [taskId])

  async function loadTask() {
    try {
      const { data } = await api.get(`/api/tasks/${taskId}`)
      setTask(data)
      setProgress(data.progress)
    } catch (err) {
      setLoadError(err.response?.data?.detail || '업무를 불러올 수 없습니다.')
    }
  }

  async function loadLogs() {
    try {
      const { data } = await api.get(`/api/tasks/${taskId}/logs`)
      setLogs(data)
    } catch (err) {
      console.error('이력 로드 실패', err)
    }
  }

  async function changeStatus(newStatus) {
    if (newStatus === 'rejected' && !statusComment.trim()) {
      alert('반려 시 코멘트는 필수입니다.')
      return
    }
    await api.post(`/api/tasks/${taskId}/status`, { status: newStatus, comment: statusComment || null })
    setStatusComment('')
    loadTask()
    loadLogs()
  }

  async function updateProgress() {
    await api.patch(`/api/tasks/${taskId}`, { progress })
    loadTask()
  }

  async function submitComment() {
    if (!newComment.trim()) return
    await api.post(`/api/tasks/${taskId}/comment`, { comment: newComment })
    setNewComment('')
    loadLogs()
  }

  async function handleFileUpload(e) {
    const file = e.target.files[0]
    if (!file) return
    setUploading(true)
    const formData = new FormData()
    formData.append('file', file)
    try {
      await api.post(`/api/attachments/${taskId}`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      loadTask()
    } catch (err) {
      alert(err.response?.data?.detail || '업로드에 실패했습니다.')
    } finally {
      setUploading(false)
      e.target.value = ''
    }
  }

  async function deleteAttachment(attachmentId) {
    if (!confirm('첨부파일을 삭제하시겠습니까?')) return
    try {
      await api.delete(`/api/attachments/${attachmentId}`)
      loadTask()
    } catch (err) {
      alert(err.response?.data?.detail || '삭제에 실패했습니다.')
    }
  }

  async function downloadFile(attachment) {
    const url = `${getApiBase()}/api/attachments/${attachment.id}/download`
    const token = localStorage.getItem('access_token')
    if (window.electronAPI) {
      const result = await window.electronAPI.downloadFile({ url, filename: attachment.filename, token })
      if (result?.success) alert(`저장 완료: ${result.filePath}`)
    } else {
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

  async function previewImage(attachment) {
    const url = `${getApiBase()}/api/attachments/${attachment.id}/download`
    const token = localStorage.getItem('access_token')
    try {
      const res = await fetch(url, { headers: { Authorization: `Bearer ${token}` } })
      if (!res.ok) return
      const blob = await res.blob()
      const blobUrl = URL.createObjectURL(blob)
      setPreviewUrl(blobUrl)
      setPreviewName(attachment.filename)
    } catch {}
  }

  function closePreview() {
    if (previewUrl) URL.revokeObjectURL(previewUrl)
    setPreviewUrl(null)
    setPreviewName('')
  }

  async function openReassign() {
    if (!showReassign) {
      const { data } = await api.get('/api/users/')
      setUsers(data)
      setNewAssigneeId(String(task.assignee?.id || ''))
      setAssigneeSearch(task.assignee?.name || '')
      setShowUserList(false)
    }
    setShowReassign((v) => !v)
  }

  const filteredReassignUsers = users.filter((u) => {
    const q = assigneeSearch.toLowerCase()
    return u.name.toLowerCase().includes(q) || (u.department && u.department.toLowerCase().includes(q))
  })

  async function submitReassign() {
    if (!newAssigneeId) return
    if (parseInt(newAssigneeId) === task.assignee?.id) {
      setShowReassign(false)
      return
    }
    try {
      await api.post(`/api/tasks/${taskId}/reassign`, { assignee_id: parseInt(newAssigneeId) })
      setShowReassign(false)
      loadTask()
      loadLogs()
    } catch (err) {
      alert(err.response?.data?.detail || '담당자 변경에 실패했습니다.')
    }
  }

  async function handleClone() {
    setCloning(true)
    try {
      const { data } = await api.post(`/api/tasks/${taskId}/clone`)
      if (data.id) navigate(`/tasks/${data.id}`)
    } finally {
      setCloning(false)
    }
  }

  async function handleDelete() {
    if (!confirm('업무를 삭제하면 첨부파일, 댓글 등 모든 데이터가 영구 삭제됩니다.\n정말 삭제하시겠습니까?')) return
    setDeleting(true)
    try {
      await api.delete(`/api/tasks/${taskId}`)
      navigate('/')
    } catch (err) {
      alert(err.response?.data?.detail || '삭제에 실패했습니다.')
      setDeleting(false)
    }
  }

  // 댓글 수정 시작
  function startEditComment(log) {
    setEditingLogId(log.id)
    setEditingText(log.comment)
  }

  async function submitEditComment(logId) {
    if (!editingText.trim()) return
    try {
      await api.patch(`/api/tasks/${taskId}/comments/${logId}`, { comment: editingText.trim() })
      setEditingLogId(null)
      setEditingText('')
      loadLogs()
    } catch (err) {
      alert(err.response?.data?.detail || '수정에 실패했습니다.')
    }
  }

  async function deleteComment(logId) {
    if (!confirm('댓글을 삭제하시겠습니까?')) return
    try {
      await api.delete(`/api/tasks/${taskId}/comments/${logId}`)
      loadLogs()
    } catch (err) {
      alert(err.response?.data?.detail || '삭제에 실패했습니다.')
    }
  }

  if (loadError) return (
    <div className="p-8 text-center">
      <p className="text-red-500 mb-3">{loadError}</p>
      <button onClick={() => navigate(-1)} className="text-sm text-primary-600 hover:underline">← 목록으로</button>
    </div>
  )
  if (!task) return <div className="p-8 text-center text-gray-400">불러오는 중...</div>

  const flow = STATUS_FLOW[task.status] || { label: task.status, next: [] }
  const isAssigner = user?.id === task.assigner?.id
  const isAssignee = user?.id === task.assignee?.id
  const canReassign = isAssigner || isAssignee || user?.is_admin  // 지시자·담당자·관리자 모두 가능
  const canChangeStatus =
    (isAssignee && ['pending', 'in_progress', 'rejected'].includes(task.status)) ||
    (isAssigner && task.status === 'review')
  const canDelete = isAssigner || user?.is_admin

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <div className="flex items-center justify-between mb-4">
        <button onClick={() => navigate(-1)} className="text-sm text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 flex items-center gap-1">
          ← 목록으로
        </button>
        <div className="flex items-center gap-2">
          {/* 즐겨찾기 */}
          <button
            onClick={async () => {
              try {
                const { data } = await api.post(`/api/tasks/${taskId}/favorite`)
                setTask((t) => ({ ...t, is_favorite: data.is_favorite }))
              } catch (e) { console.error(e) }
            }}
            className={`text-xl leading-none px-2 py-1 rounded-lg border transition ${
              task.is_favorite
                ? 'text-yellow-400 border-yellow-300 bg-yellow-50 dark:bg-yellow-900/20'
                : 'text-gray-300 dark:text-gray-600 border-gray-200 dark:border-gray-700 hover:text-yellow-300'
            }`}
            title={task.is_favorite ? '즐겨찾기 해제' : '즐겨찾기 추가'}
          >★</button>
          <button
            onClick={handleClone}
            disabled={cloning}
            className="text-xs border border-gray-300 dark:border-gray-600 text-gray-600 dark:text-gray-300 px-3 py-1.5 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50"
          >
            {cloning ? '복사 중...' : '업무 복사'}
          </button>
          {canReassign && (
            <button
              onClick={openReassign}
              className="text-xs border border-gray-300 dark:border-gray-600 text-gray-600 dark:text-gray-300 px-3 py-1.5 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700"
            >
              담당자 변경
            </button>
          )}
          {canDelete && (
            <button
              onClick={handleDelete}
              disabled={deleting}
              className="text-xs border border-red-300 dark:border-red-700 text-red-600 dark:text-red-400 px-3 py-1.5 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20 disabled:opacity-50"
            >
              {deleting ? '삭제 중...' : '업무 삭제'}
            </button>
          )}
        </div>
      </div>

      {/* 담당자 변경 패널 */}
      {showReassign && canReassign && (
        <div className="mb-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-xl p-4">
          <p className="text-sm font-medium text-gray-700 dark:text-gray-200 mb-2">새 담당자 선택</p>
          <div className="flex gap-2 items-start">
            <div className="relative flex-1">
              <input
                type="text"
                value={assigneeSearch}
                onChange={(e) => { setAssigneeSearch(e.target.value); setNewAssigneeId(''); setShowUserList(true) }}
                onFocus={() => setShowUserList(true)}
                placeholder="이름 또는 부서로 검색..."
                autoComplete="off"
                className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-1.5 text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
              {newAssigneeId && <span className="absolute right-3 top-1/2 -translate-y-1/2 text-green-500 text-sm">✓</span>}
              {showUserList && (
                <div className="absolute z-10 w-full mt-1 bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg shadow-lg max-h-48 overflow-y-auto">
                  {filteredReassignUsers.length === 0 ? (
                    <div className="px-3 py-2 text-sm text-gray-400">검색 결과 없음</div>
                  ) : (
                    filteredReassignUsers.map((u) => (
                      <button
                        key={u.id}
                        type="button"
                        onClick={() => { setNewAssigneeId(String(u.id)); setAssigneeSearch(u.name + (u.department ? ` (${u.department})` : '')); setShowUserList(false) }}
                        className={`w-full text-left px-3 py-2 text-sm hover:bg-primary-50 dark:hover:bg-primary-900/30 flex items-center justify-between ${
                          newAssigneeId === String(u.id) ? 'bg-primary-50 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300' : 'text-gray-700 dark:text-gray-200'
                        }`}
                      >
                        <span>{u.name}</span>
                        {u.department && <span className="text-xs text-gray-400">{u.department}</span>}
                      </button>
                    ))
                  )}
                </div>
              )}
            </div>
            <button onClick={submitReassign} disabled={!newAssigneeId} className="bg-primary-600 text-white px-3 py-1.5 rounded-lg text-sm hover:bg-primary-700 disabled:opacity-40 whitespace-nowrap">변경</button>
            <button onClick={() => setShowReassign(false)} className="text-sm text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 whitespace-nowrap">취소</button>
          </div>
        </div>
      )}

      <div className="grid grid-cols-3 gap-6">
        {/* 왼쪽: 업무 상세 */}
        <div className="col-span-2 space-y-4">
          {/* 기본 정보 */}
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
                type="range" min="0" max="100" step="5" value={progress}
                onChange={(e) => setProgress(parseInt(e.target.value))}
                className="flex-1"
              />
              {isAssignee && progress !== task.progress && (
                <button onClick={updateProgress} className="text-sm bg-primary-600 text-white px-3 py-1 rounded-lg hover:bg-primary-700">저장</button>
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
                  <button onClick={() => setShowSubtaskModal(true)} className="text-xs text-primary-600 dark:text-primary-400 hover:text-primary-800 dark:hover:text-primary-200 font-medium">
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
                {task.attachments.map((a) => {
                  const isImage = IMAGE_TYPES.includes(a.mime_type)
                  return (
                    <div key={a.id} className="flex items-center justify-between py-1.5 px-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                      <div className="flex items-center gap-2 min-w-0">
                        {isImage ? (
                          <svg className="w-4 h-4 text-green-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                          </svg>
                        ) : (
                          <svg className="w-4 h-4 text-gray-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                          </svg>
                        )}
                        <span className="text-sm text-gray-700 dark:text-gray-200 truncate">{a.filename}</span>
                        <span className="text-xs text-gray-400 flex-shrink-0">{formatSize(a.file_size)}</span>
                      </div>
                      <div className="flex items-center gap-2 flex-shrink-0 ml-2">
                        {isImage && (
                          <button
                            onClick={() => previewImage(a)}
                            className="text-xs text-green-600 dark:text-green-400 hover:text-green-800 dark:hover:text-green-200 font-medium"
                          >
                            미리보기
                          </button>
                        )}
                        <button
                          onClick={() => downloadFile(a)}
                          className="text-xs text-primary-600 dark:text-primary-400 hover:text-primary-800 dark:hover:text-primary-200 font-medium"
                        >
                          다운로드
                        </button>
                        {(a.uploader_id === user?.id || user?.is_admin) && (
                          <button
                            onClick={() => deleteAttachment(a.id)}
                            className="text-xs text-red-500 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300 font-medium"
                          >
                            삭제
                          </button>
                        )}
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </div>

          {/* 댓글 */}
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700 p-4">
            <h3 className="font-semibold text-gray-700 dark:text-gray-300 text-sm mb-3">댓글</h3>
            <div className="space-y-2 mb-3">
              {logs.filter((l) => l.action === 'comment').length === 0 ? (
                <p className="text-xs text-gray-400">등록된 댓글이 없습니다.</p>
              ) : (
                logs.filter((l) => l.action === 'comment').map((l) => (
                  <div key={l.id} className="bg-gray-50 dark:bg-gray-700 rounded-lg px-3 py-2">
                    <div className="flex items-center justify-between mb-1">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-medium text-gray-700 dark:text-gray-200">{l.user?.name}</span>
                        <span className="text-xs text-gray-400 dark:text-gray-500">{new Date(l.created_at).toLocaleString('ko-KR')}</span>
                      </div>
                      {l.user?.id === user?.id && editingLogId !== l.id && (
                        <div className="flex gap-2">
                          <button
                            onClick={() => startEditComment(l)}
                            className="text-xs text-gray-400 hover:text-primary-600 dark:hover:text-primary-400"
                          >
                            수정
                          </button>
                          <button
                            onClick={() => deleteComment(l.id)}
                            className="text-xs text-gray-400 hover:text-red-500 dark:hover:text-red-400"
                          >
                            삭제
                          </button>
                        </div>
                      )}
                    </div>
                    {editingLogId === l.id ? (
                      <div className="flex gap-2 mt-1">
                        <input
                          type="text"
                          value={editingText}
                          onChange={(e) => setEditingText(e.target.value)}
                          onKeyDown={(e) => e.key === 'Enter' && submitEditComment(l.id)}
                          autoFocus
                          className="flex-1 border border-gray-300 dark:border-gray-600 rounded-lg px-2 py-1 text-sm bg-white dark:bg-gray-600 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-1 focus:ring-primary-500"
                        />
                        <button onClick={() => submitEditComment(l.id)} className="text-xs bg-primary-600 text-white px-2 py-1 rounded hover:bg-primary-700">저장</button>
                        <button onClick={() => setEditingLogId(null)} className="text-xs text-gray-400 hover:text-gray-600 px-1">취소</button>
                      </div>
                    ) : (
                      <p className="text-sm text-gray-700 dark:text-gray-200">{l.comment}</p>
                    )}
                  </div>
                ))
              )}
            </div>
            <div className="flex gap-2">
              <input
                type="text"
                value={newComment}
                onChange={(e) => setNewComment(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && submitComment()}
                placeholder="댓글 입력 (Enter) · @이름으로 멘션"
                className="flex-1 border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-1.5 text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
              <button
                onClick={submitComment}
                disabled={!newComment.trim()}
                className="bg-primary-600 text-white px-3 py-1.5 rounded-lg text-sm hover:bg-primary-700 disabled:opacity-40"
              >
                등록
              </button>
            </div>
          </div>
        </div>

        {/* 오른쪽: 상태 변경 + 이력 */}
        <div className="space-y-4">
          {canChangeStatus && flow.next.length > 0 && (
            <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700 p-4">
              <h3 className="font-semibold text-gray-700 dark:text-gray-300 text-sm mb-3">상태 변경</h3>
              <textarea
                value={statusComment}
                onChange={(e) => setStatusComment(e.target.value)}
                placeholder={flow.next.some((n) => n.value === 'rejected') ? '코멘트 (반려 시 필수)' : '코멘트 (선택사항)'}
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

          {/* 이력 */}
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700 p-4">
            <h3 className="font-semibold text-gray-700 dark:text-gray-300 text-sm mb-3">이력</h3>
            {logs.filter((l) => l.action !== 'comment').length === 0 ? (
              <p className="text-xs text-gray-400">이력이 없습니다.</p>
            ) : (
              <div className="space-y-2">
                {logs.filter((l) => l.action !== 'comment').map((log) => (
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

      {/* 이미지 미리보기 모달 */}
      {previewUrl && (
        <div
          className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4"
          onClick={closePreview}
        >
          <div className="relative max-w-4xl max-h-full" onClick={(e) => e.stopPropagation()}>
            <button
              onClick={closePreview}
              className="absolute -top-10 right-0 text-white text-2xl hover:text-gray-300 font-bold"
            >
              ✕
            </button>
            <p className="text-white text-sm mb-2 text-center">{previewName}</p>
            <img
              src={previewUrl}
              alt={previewName}
              className="max-w-full max-h-[80vh] rounded-lg object-contain"
            />
          </div>
        </div>
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
    reassigned: '담당자 변경',
  }
  return map[log.action] || log.action
}
