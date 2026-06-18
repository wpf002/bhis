import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './hooks/useAuth'
import LoginPage from './pages/Login'
import DashboardPage from './pages/Dashboard'
import SurveyPage from './pages/Survey'
import IndividualReportPage from './pages/IndividualReport'
import AdminPage from './pages/Admin'
import OnboardingPage from './pages/Onboarding'

function ProtectedRoute({ children, roles }: { children: React.ReactNode; roles?: string[] }) {
  const { isAuthenticated, role } = useAuthStore()
  if (!isAuthenticated()) return <Navigate to="/login" replace />
  if (roles && role && !roles.includes(role)) return <Navigate to="/dashboard" replace />
  return <>{children}</>
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/onboarding" element={<ProtectedRoute roles={['admin']}><OnboardingPage /></ProtectedRoute>} />
        <Route path="/dashboard" element={<ProtectedRoute roles={['leader', 'admin']}><DashboardPage /></ProtectedRoute>} />
        <Route path="/admin" element={<ProtectedRoute roles={['admin']}><AdminPage /></ProtectedRoute>} />
        <Route path="/survey/:instanceId" element={<ProtectedRoute><SurveyPage /></ProtectedRoute>} />
        <Route path="/report/:sessionId" element={<ProtectedRoute><IndividualReportPage /></ProtectedRoute>} />
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
