import { Outlet, useNavigate } from 'react-router-dom'
import { useState, useEffect } from 'react'
import useAuthStore from '../store/authStore'
import api from '../utils/api'
import VerificationBanner from './VerificationBanner'
import { toggleDarkMode, isDark } from '../utils/darkMode'

export default function Layout() {
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()
  const [unreadCount, setUnreadCount] = useState(0)
  const [notifications, setNotifications] = useState([])
  const [showNotifPanel, setShowNotifPanel] = useState(false)
  const [dark, setDark] = useState(() => isDark())

  useEffect(() => {
    fetchUnread()
    const interval = setInterval(fetchUnread, 30000)
    return () => clearInterval(interval)
  }, [])

  async function fetchUnread() {
    try {
      const { data } = await api.get('/api/notifications/unread-count')
      const prev = unreadCount
      setUnreadCount(data.count)
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

  function handleToggleDark() {
    const isDarkNow = toggleDarkMode()
    setDark(isDarkNow)
  }

  function handleLogout() {
    logout()
    navigate('/login')
  }

  return (
    <div className="flex flex-col h-screen bg-gray-50 dark:bg-slate-900">
      {/* 상단 헤더 */}
      <header className="bg-primary-600 text-white px-6 py-3 flex items-center justify-between shadow z-10 flex-shrink-0">
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate('/')}
            className="font-bold text-lg hover:text-primary-100 transition"
          >
            CollabTodo
          </button>
        </div>
        <div className="flex items-center gap-4">
          {/* 관리자 메뉴 */}
          {user?.is_admin && (
            <button
              onClick={() => navigate('/admin')}
              className="text-sm text-primary-200 hover:text-white transition flex items-center gap-1"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
              사용자 관리
            </button>
          )}

          {/* 다크모드 토글 */}
          <button
            onClick={handleToggleDark}
            className="p-2 rounded-full hover:bg-primary-700 transition"
            title={dark ? '라이트 모드' : '다크 모드'}
          >
            {dark ? (
              /* 해(라이트로 전환) */
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364-6.364l-.707.707M6.343 17.657l-.707.707M17.657 17.657l-.707-.707M6.343 6.343l-.707-.707M12 8a4 4 0 100 8 4 4 0 000-8z" />
              </svg>
            ) : (
              /* 달(다크로 전환) */
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
              </svg>
            )}
          </button>

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
              <div className="absolute right-0 mt-2 w-80 bg-white dark:bg-gray-800 rounded-xl shadow-xl border border-gray-100 dark:border-gray-700 z-50 max-h-96 overflow-y-auto">
                <div className="p-3 border-b border-gray-100 dark:border-gray-700 font-semibold text-gray-700 dark:text-gray-200">알림</div>
                {notifications.length === 0 ? (
                  <div className="p-4 text-center text-gray-400 text-sm">알림이 없습니다.</div>
                ) : (
                  notifications.map((n) => (
                    <div
                      key={n.id}
                      className={`p-3 border-b border-gray-100 dark:border-gray-700 text-sm cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700 ${!n.is_read ? 'bg-blue-50 dark:bg-blue-900/30' : ''}`}
                      onClick={() => {
                        if (n.task_id) navigate(`/tasks/${n.task_id}`)
                        setShowNotifPanel(false)
                      }}
                    >
                      <p className="text-gray-800 dark:text-gray-200">{n.message}</p>
                      <p className="text-gray-400 text-xs mt-1">{new Date(n.created_at).toLocaleString('ko-KR')}</p>
                    </div>
                  ))
                )}
              </div>
            )}
          </div>

          {/* 사용자 정보 (직급 제거) */}
          <div className="text-sm">
            <span className="font-medium">{user?.name}</span>
            <span className="text-primary-200 ml-1 text-xs">{user?.department}</span>
          </div>

          <button onClick={handleLogout} className="text-sm text-primary-200 hover:text-white transition">
            로그아웃
          </button>
        </div>
      </header>

      {/* 이메일 인증 배너 */}
      <VerificationBanner />

      {/* 메인 컨텐츠 */}
      <main className="flex-1 overflow-y-auto">
        <Outlet />
      </main>
    </div>
  )
}
