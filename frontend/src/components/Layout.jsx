import { Outlet, useNavigate } from 'react-router-dom'
import { useState, useEffect } from 'react'
import useAuthStore from '../store/authStore'
import api from '../utils/api'

export default function Layout() {
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()
  const [unreadCount, setUnreadCount] = useState(0)
  const [notifications, setNotifications] = useState([])
  const [showNotifPanel, setShowNotifPanel] = useState(false)

  useEffect(() => {
    fetchUnread()
    const interval = setInterval(fetchUnread, 30000) // 30초마다 폴링
    return () => clearInterval(interval)
  }, [])

  async function fetchUnread() {
    try {
      const { data } = await api.get('/api/notifications/unread-count')
      const prev = unreadCount
      setUnreadCount(data.count)
      // 새 알림이 생기면 데스크톱 푸시
      if (data.count > prev && window.electronAPI) {
        const { data: notifs } = await api.get('/api/notifications/')
        const newest = notifs[0]
        if (newest && !newest.is_read) {
          window.electronAPI.showNotification({
            title: 'CollabTodo 알림',
            body: newest.message,
            taskId: newest.task_id,
          })
        }
      }
    } catch {}
  }

  async function openNotifications() {
    setShowNotifPanel((v) => !v)
    const { data } = await api.get('/api/notifications/')
    setNotifications(data)
    if (unreadCount > 0) {
      await api.post('/api/notifications/read-all')
      setUnreadCount(0)
    }
  }

  function handleLogout() {
    logout()
    navigate('/login')
  }

  return (
    <div className="flex flex-col h-screen">
      {/* 상단 헤더 */}
      <header className="bg-primary-600 text-white px-6 py-3 flex items-center justify-between shadow z-10">
        <div className="flex items-center gap-3">
          <span className="font-bold text-lg">CollabTodo</span>
        </div>
        <div className="flex items-center gap-4">
          {/* 알림 버튼 */}
          <div className="relative">
            <button
              onClick={openNotifications}
              className="relative p-2 rounded-full hover:bg-primary-700 transition"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
              </svg>
              {unreadCount > 0 && (
                <span className="absolute top-0 right-0 bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
                  {unreadCount > 9 ? '9+' : unreadCount}
                </span>
              )}
            </button>

            {showNotifPanel && (
              <div className="absolute right-0 mt-2 w-80 bg-white rounded-xl shadow-xl border border-gray-100 z-50 max-h-96 overflow-y-auto">
                <div className="p-3 border-b font-semibold text-gray-700">알림</div>
                {notifications.length === 0 ? (
                  <div className="p-4 text-center text-gray-400 text-sm">알림이 없습니다.</div>
                ) : (
                  notifications.map((n) => (
                    <div
                      key={n.id}
                      className={`p-3 border-b text-sm cursor-pointer hover:bg-gray-50 ${!n.is_read ? 'bg-blue-50' : ''}`}
                      onClick={() => {
                        if (n.task_id) navigate(`/tasks/${n.task_id}`)
                        setShowNotifPanel(false)
                      }}
                    >
                      <p className="text-gray-800">{n.message}</p>
                      <p className="text-gray-400 text-xs mt-1">{new Date(n.created_at).toLocaleString('ko-KR')}</p>
                    </div>
                  ))
                )}
              </div>
            )}
          </div>

          {/* 사용자 정보 */}
          <div className="text-sm">
            <span className="font-medium">{user?.name}</span>
            <span className="text-primary-200 ml-1 text-xs">{user?.department} · {user?.job_title}</span>
          </div>

          <button onClick={handleLogout} className="text-sm text-primary-200 hover:text-white transition">
            로그아웃
          </button>
        </div>
      </header>

      {/* 메인 컨텐츠 */}
      <main className="flex-1 overflow-y-auto">
        <Outlet />
      </main>
    </div>
  )
}
