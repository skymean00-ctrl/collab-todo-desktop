import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../utils/api'

const TYPE_LABELS = {
  assigned: '업무 배정',
  status_changed: '상태 변경',
  due_soon_3d: '마감 3일 전',
  due_soon_1d: '마감 1일 전',
  reassigned: '담당자 변경',
  mentioned: '멘션',
  commented: '새 댓글',
  announcement: '공지',
}

const TYPE_COLORS = {
  assigned: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
  status_changed: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
  due_soon_3d: 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200',
  due_soon_1d: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
  reassigned: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200',
  mentioned: 'bg-pink-100 text-pink-800 dark:bg-pink-900 dark:text-pink-200',
  commented: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200',
  announcement: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
}

function formatDate(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  const now = new Date()
  const diff = Math.floor((now - d) / 1000)
  if (diff < 60) return '방금 전'
  if (diff < 3600) return `${Math.floor(diff / 60)}분 전`
  if (diff < 86400) return `${Math.floor(diff / 3600)}시간 전`
  return d.toLocaleDateString('ko-KR', { month: 'long', day: 'numeric' })
}

export default function NotificationsPage() {
  const navigate = useNavigate()
  const [notifications, setNotifications] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [unreadOnly, setUnreadOnly] = useState(false)
  const [loading, setLoading] = useState(false)
  const PAGE_SIZE = 20

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const { data } = await api.get('/api/notifications/', {
        params: { page, page_size: PAGE_SIZE, unread_only: unreadOnly },
      })
      setNotifications(data.items || [])
      setTotal(data.total || 0)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }, [page, unreadOnly])

  useEffect(() => { load() }, [load])

  async function markRead(id) {
    await api.post(`/api/notifications/${id}/read`)
    setNotifications((prev) => prev.map((n) => n.id === id ? { ...n, is_read: true } : n))
  }

  async function markAllRead() {
    await api.post('/api/notifications/read-all')
    setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })))
  }

  async function deleteNotif(id) {
    await api.delete(`/api/notifications/${id}`)
    setNotifications((prev) => prev.filter((n) => n.id !== id))
    setTotal((t) => t - 1)
  }

  function handleClick(n) {
    if (!n.is_read) markRead(n.id)
    if (n.task_id) navigate(`/tasks/${n.task_id}`)
  }

  const totalPages = Math.ceil(total / PAGE_SIZE)

  return (
    <div className="max-w-2xl mx-auto px-4 py-6">
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-xl font-bold text-gray-900 dark:text-white">전체 알림</h1>
        <div className="flex items-center gap-3">
          <label className="flex items-center gap-1.5 text-sm text-gray-600 dark:text-gray-400 cursor-pointer">
            <input
              type="checkbox" checked={unreadOnly}
              onChange={(e) => { setUnreadOnly(e.target.checked); setPage(1) }}
              className="rounded"
            />
            읽지 않은 알림만
          </label>
          <button
            onClick={markAllRead}
            className="text-sm text-primary-600 hover:underline"
          >
            모두 읽음
          </button>
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center py-12">
          <div className="w-8 h-8 border-4 border-primary-200 border-t-primary-600 rounded-full animate-spin" />
        </div>
      ) : notifications.length === 0 ? (
        <div className="text-center text-gray-400 dark:text-gray-500 py-16">
          <p className="text-4xl mb-3">🔔</p>
          <p>{unreadOnly ? '읽지 않은 알림이 없습니다.' : '알림이 없습니다.'}</p>
        </div>
      ) : (
        <div className="space-y-2">
          {notifications.map((n) => (
            <div
              key={n.id}
              onClick={() => handleClick(n)}
              className={`flex items-start gap-3 p-4 rounded-xl border cursor-pointer transition-colors ${
                n.is_read
                  ? 'bg-white dark:bg-gray-800 border-gray-100 dark:border-gray-700 opacity-70'
                  : 'bg-blue-50 dark:bg-blue-950 border-blue-100 dark:border-blue-900'
              } hover:border-primary-300`}
            >
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${TYPE_COLORS[n.type] || 'bg-gray-100 text-gray-700'}`}>
                    {TYPE_LABELS[n.type] || n.type}
                  </span>
                  {!n.is_read && (
                    <span className="w-2 h-2 rounded-full bg-blue-500 flex-shrink-0" />
                  )}
                  <span className="text-xs text-gray-400 ml-auto">{formatDate(n.created_at)}</span>
                </div>
                <p className="text-sm text-gray-800 dark:text-gray-200 truncate">{n.message}</p>
              </div>
              <button
                onClick={(e) => { e.stopPropagation(); deleteNotif(n.id) }}
                className="text-gray-300 hover:text-red-400 text-lg leading-none flex-shrink-0"
                title="삭제"
              >
                ×
              </button>
            </div>
          ))}
        </div>
      )}

      {/* 페이지네이션 */}
      {totalPages > 1 && (
        <div className="flex justify-center items-center gap-2 mt-6">
          <button
            disabled={page <= 1}
            onClick={() => setPage(page - 1)}
            className="px-3 py-1.5 rounded text-sm border border-gray-300 dark:border-gray-600 disabled:opacity-40"
          >
            이전
          </button>
          <span className="text-sm text-gray-600 dark:text-gray-400">
            {page} / {totalPages}
          </span>
          <button
            disabled={page >= totalPages}
            onClick={() => setPage(page + 1)}
            className="px-3 py-1.5 rounded text-sm border border-gray-300 dark:border-gray-600 disabled:opacity-40"
          >
            다음
          </button>
        </div>
      )}
    </div>
  )
}
