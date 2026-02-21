import { Outlet, useNavigate } from 'react-router-dom'
import { useState, useEffect, useRef } from 'react'
import useAuthStore from '../store/authStore'
import api from '../utils/api'
import VerificationBanner from './VerificationBanner'
import { toggleDarkMode, isDark } from '../utils/darkMode'

export default function Layout() {
  const { user, logout, updateProfile } = useAuthStore()
  const navigate = useNavigate()
  const [unreadCount, setUnreadCount] = useState(0)
  const [notifications, setNotifications] = useState([])
  const [showNotifPanel, setShowNotifPanel] = useState(false)
  const [dark, setDark] = useState(() => isDark())
  const [showUserMenu, setShowUserMenu] = useState(false)
  const [showProfileModal, setShowProfileModal] = useState(false)
  const [showPasswordModal, setShowPasswordModal] = useState(false)
  const userMenuRef = useRef(null)

  useEffect(() => {
    fetchUnread()
    const interval = setInterval(fetchUnread, 30000)
    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    function handleClick(e) {
      if (userMenuRef.current && !userMenuRef.current.contains(e.target)) {
        setShowUserMenu(false)
      }
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [])

  async function fetchUnread() {
    try {
      const { data } = await api.get('/api/notifications/unread-count')
      setUnreadCount(data.count)
    } catch {}
  }

  async function openNotifications() {
    const isOpening = !showNotifPanel
    setShowNotifPanel((v) => !v)
    if (isOpening) {
      const { data } = await api.get('/api/notifications/')
      setNotifications(data)
    }
  }

  async function markOneRead(n) {
    if (!n.is_read) {
      await api.post(`/api/notifications/${n.id}/read`)
      setNotifications((prev) => prev.map((x) => x.id === n.id ? { ...x, is_read: true } : x))
      setUnreadCount((c) => Math.max(0, c - 1))
    }
    if (n.task_id) navigate(`/tasks/${n.task_id}`)
    setShowNotifPanel(false)
  }

  async function markAllRead() {
    await api.post('/api/notifications/read-all')
    setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })))
    setUnreadCount(0)
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
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364-6.364l-.707.707M6.343 17.657l-.707.707M17.657 17.657l-.707-.707M6.343 6.343l-.707-.707M12 8a4 4 0 100 8 4 4 0 000-8z" />
              </svg>
            ) : (
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
                <div className="p-3 border-b border-gray-100 dark:border-gray-700 flex items-center justify-between">
                  <span className="font-semibold text-gray-700 dark:text-gray-200">알림</span>
                  {unreadCount > 0 && (
                    <button
                      onClick={markAllRead}
                      className="text-xs text-primary-600 dark:text-primary-400 hover:text-primary-800 dark:hover:text-primary-200 font-medium"
                    >
                      모두 읽음
                    </button>
                  )}
                </div>
                {notifications.length === 0 ? (
                  <div className="p-4 text-center text-gray-400 text-sm">알림이 없습니다.</div>
                ) : (
                  notifications.map((n) => (
                    <div
                      key={n.id}
                      className={`p-3 border-b border-gray-100 dark:border-gray-700 text-sm cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700 ${!n.is_read ? 'bg-blue-50 dark:bg-blue-900/30' : ''}`}
                      onClick={() => markOneRead(n)}
                    >
                      <div className="flex items-start gap-2">
                        {!n.is_read && <span className="w-2 h-2 rounded-full bg-blue-500 mt-1.5 flex-shrink-0" />}
                        <div>
                          <p className="text-gray-800 dark:text-gray-200">{n.message}</p>
                          <p className="text-gray-400 text-xs mt-1">{new Date(n.created_at).toLocaleString('ko-KR')}</p>
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            )}
          </div>

          {/* 사용자 메뉴 */}
          <div className="relative" ref={userMenuRef}>
            <button
              onClick={() => setShowUserMenu((v) => !v)}
              className="text-sm flex items-center gap-1 hover:text-primary-100 transition"
            >
              <span className="font-medium">{user?.name}</span>
              <span className="text-primary-200 text-xs">{user?.department}</span>
              <svg className="w-4 h-4 text-primary-200 ml-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>
            {showUserMenu && (
              <div className="absolute right-0 mt-2 w-44 bg-white dark:bg-gray-800 rounded-xl shadow-xl border border-gray-100 dark:border-gray-700 z-50 py-1">
                <button
                  onClick={() => { setShowProfileModal(true); setShowUserMenu(false) }}
                  className="w-full text-left px-4 py-2 text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-700"
                >
                  내 프로필 편집
                </button>
                <button
                  onClick={() => { setShowPasswordModal(true); setShowUserMenu(false) }}
                  className="w-full text-left px-4 py-2 text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-700"
                >
                  비밀번호 변경
                </button>
                <hr className="border-gray-100 dark:border-gray-700 my-1" />
                <button
                  onClick={handleLogout}
                  className="w-full text-left px-4 py-2 text-sm text-red-600 dark:text-red-400 hover:bg-gray-50 dark:hover:bg-gray-700"
                >
                  로그아웃
                </button>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* 이메일 인증 배너 */}
      <VerificationBanner />

      {/* 메인 컨텐츠 */}
      <main className="flex-1 overflow-y-auto">
        <Outlet />
      </main>

      {/* 프로필 편집 모달 */}
      {showProfileModal && (
        <ProfileModal
          user={user}
          onClose={() => setShowProfileModal(false)}
          onSaved={(updated) => { updateProfile(updated); setShowProfileModal(false) }}
        />
      )}

      {/* 비밀번호 변경 모달 */}
      {showPasswordModal && (
        <PasswordModal onClose={() => setShowPasswordModal(false)} />
      )}
    </div>
  )
}

function ProfileModal({ user, onClose, onSaved }) {
  const DEPARTMENTS = ['현장소장', '공무팀', '공사팀', '안전팀', '품질팀', '직영팀']
  const [name, setName] = useState(user?.name || '')
  const [jobTitle, setJobTitle] = useState(user?.job_title || '')
  const [department, setDepartment] = useState(user?.department || '')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  async function handleSave() {
    if (!name.trim()) { setError('이름을 입력해주세요.'); return }
    setSaving(true)
    setError('')
    try {
      const { data } = await api.patch('/api/users/me', {
        name: name.trim(),
        job_title: jobTitle.trim(),
        department_name: department,
      })
      onSaved({ name: data.name, job_title: data.job_title, department: data.department })
    } catch (e) {
      setError(e.response?.data?.detail || '저장에 실패했습니다.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl p-6 w-96">
        <h3 className="font-bold text-gray-900 dark:text-gray-100 mb-4">내 프로필 편집</h3>
        <div className="space-y-3">
          <div>
            <label className="text-xs text-gray-500 dark:text-gray-400 mb-1 block">이름</label>
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>
          <div>
            <label className="text-xs text-gray-500 dark:text-gray-400 mb-1 block">직책</label>
            <input
              value={jobTitle}
              onChange={(e) => setJobTitle(e.target.value)}
              placeholder="예: 팀장, 대리..."
              className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>
          <div>
            <label className="text-xs text-gray-500 dark:text-gray-400 mb-1 block">부서</label>
            <select
              value={department}
              onChange={(e) => setDepartment(e.target.value)}
              className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              {DEPARTMENTS.map((d) => (
                <option key={d} value={d}>{d}</option>
              ))}
            </select>
          </div>
          {error && <p className="text-xs text-red-500">{error}</p>}
        </div>
        <div className="flex gap-3 mt-5">
          <button onClick={onClose} className="flex-1 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700">
            취소
          </button>
          <button onClick={handleSave} disabled={saving} className="flex-1 py-2 bg-primary-600 text-white rounded-lg text-sm font-medium hover:bg-primary-700 disabled:opacity-50">
            {saving ? '저장 중...' : '저장'}
          </button>
        </div>
      </div>
    </div>
  )
}

function PasswordModal({ onClose }) {
  const [current, setCurrent] = useState('')
  const [next, setNext] = useState('')
  const [confirm, setConfirm] = useState('')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)

  async function handleSave() {
    if (!current || !next || !confirm) { setError('모든 항목을 입력해주세요.'); return }
    if (next !== confirm) { setError('새 비밀번호가 일치하지 않습니다.'); return }
    if (next.length < 6) { setError('새 비밀번호는 6자 이상이어야 합니다.'); return }
    setSaving(true)
    setError('')
    try {
      await api.post('/api/auth/change-password', { current_password: current, new_password: next })
      setSuccess(true)
    } catch (e) {
      setError(e.response?.data?.detail || '비밀번호 변경에 실패했습니다.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl p-6 w-96">
        <h3 className="font-bold text-gray-900 dark:text-gray-100 mb-4">비밀번호 변경</h3>
        {success ? (
          <div>
            <p className="text-sm text-green-600 dark:text-green-400 mb-4">비밀번호가 변경되었습니다.</p>
            <button onClick={onClose} className="w-full py-2 bg-primary-600 text-white rounded-lg text-sm font-medium hover:bg-primary-700">닫기</button>
          </div>
        ) : (
          <div className="space-y-3">
            <div>
              <label className="text-xs text-gray-500 dark:text-gray-400 mb-1 block">현재 비밀번호</label>
              <input type="password" value={current} onChange={(e) => setCurrent(e.target.value)}
                className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500" />
            </div>
            <div>
              <label className="text-xs text-gray-500 dark:text-gray-400 mb-1 block">새 비밀번호 (6자 이상)</label>
              <input type="password" value={next} onChange={(e) => setNext(e.target.value)}
                className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500" />
            </div>
            <div>
              <label className="text-xs text-gray-500 dark:text-gray-400 mb-1 block">새 비밀번호 확인</label>
              <input type="password" value={confirm} onChange={(e) => setConfirm(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSave()}
                className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500" />
            </div>
            {error && <p className="text-xs text-red-500">{error}</p>}
            <div className="flex gap-3 mt-2">
              <button onClick={onClose} className="flex-1 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700">
                취소
              </button>
              <button onClick={handleSave} disabled={saving} className="flex-1 py-2 bg-primary-600 text-white rounded-lg text-sm font-medium hover:bg-primary-700 disabled:opacity-50">
                {saving ? '변경 중...' : '변경'}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
