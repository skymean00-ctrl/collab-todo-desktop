import { HashRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import useAuthStore from './store/authStore'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import DashboardPage from './pages/DashboardPage'
import TaskDetailPage from './pages/TaskDetailPage'
import VerifyEmailPage from './pages/VerifyEmailPage'
import AdminPage from './pages/AdminPage'
import Layout from './components/Layout'
import UpdateBanner from './components/UpdateBanner'

function RequireAuth({ children }) {
  const token = useAuthStore((s) => s.token)
  if (!token) return <Navigate to="/login" replace />
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
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/verify-email/:token" element={<VerifyEmailPage />} />
        <Route
          path="/"
          element={
            <RequireAuth>
              <Layout />
            </RequireAuth>
          }
        >
          <Route index element={<DashboardPage />} />
          <Route path="tasks/:taskId" element={<TaskDetailPage />} />
          <Route path="admin" element={<AdminPage />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </HashRouter>
  )
}
