import { HashRouter, Routes, Route, Navigate, Outlet } from 'react-router-dom'
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import useAuthStore from './store/authStore'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import DashboardPage from './pages/DashboardPage'
import TaskDetailPage from './pages/TaskDetailPage'
import VerifyEmailPage from './pages/VerifyEmailPage'
import AdminPage from './pages/AdminPage'
import SetupPage from './pages/SetupPage'
import ForgotPasswordPage from './pages/ForgotPasswordPage'
import ResetPasswordPage from './pages/ResetPasswordPage'
import NotificationsPage from './pages/NotificationsPage'
import Layout from './components/Layout'
import UpdateBanner from './components/UpdateBanner'

function RequireAuth({ children }) {
  const token = useAuthStore((s) => s.token)
  if (!token) return <Navigate to="/login" replace />
  return children
}

function RequireSetup({ children }) {
  const [checked, setChecked] = useState(false)
  const [configured, setConfigured] = useState(false)

  useEffect(() => {
    async function check() {
      if (!window.electronAPI) {
        setConfigured(true)
        setChecked(true)
        return
      }
      const saved = await window.electronAPI.getServerUrl()
      if (saved) {
        localStorage.setItem('server_url', saved)
        setConfigured(true)
      } else {
        setConfigured(false)
      }
      setChecked(true)
    }
    check()
  }, [])

  if (!checked) return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="w-8 h-8 border-4 border-primary-200 border-t-primary-600 rounded-full animate-spin" />
    </div>
  )

  if (!configured) return <Navigate to="/setup" replace />
  return children
}

function ElectronNavigator() {
  const navigate = useNavigate()
  useEffect(() => {
    if (window.electronAPI) {
      window.electronAPI.onNavigateToTask((taskId) => {
        navigate(`/tasks/${taskId}`)
      })
    }
  }, [navigate])
  return null
}

export default function App() {
  return (
    <HashRouter>
      <ElectronNavigator />
      <UpdateBanner />
      <Routes>
        <Route path="/setup" element={<SetupPage />} />
        <Route path="/verify-email/:token" element={<VerifyEmailPage />} />
        <Route path="/forgot-password" element={<ForgotPasswordPage />} />
        <Route path="/reset-password/:token" element={<ResetPasswordPage />} />

        <Route element={<RequireSetup><Outlet /></RequireSetup>}>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
        </Route>

        <Route
          path="/"
          element={
            <RequireSetup>
              <RequireAuth>
                <Layout />
              </RequireAuth>
            </RequireSetup>
          }
        >
          <Route index element={<DashboardPage />} />
          <Route path="tasks/:taskId" element={<TaskDetailPage />} />
          <Route path="admin" element={<AdminPage />} />
          <Route path="notifications" element={<NotificationsPage />} />
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </HashRouter>
  )
}
