import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './hooks/useAuth'
import LoginPage from './pages/Login'
import RegisterPage from './pages/Register'
import VerifyEmailPage from './pages/VerifyEmail'
import ForgotPasswordPage from './pages/ForgotPassword'
import ResetPasswordPage from './pages/ResetPassword'
import DashboardPage from './pages/Dashboard'
import SurveyPage from './pages/Survey'
import IndividualReportPage from './pages/IndividualReport'
import AdminPage from './pages/Admin'
import OnboardingPage from './pages/Onboarding'
import JoinPage from './pages/Join'

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
        {/* Public auth */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/verify-email" element={<VerifyEmailPage />} />
        <Route path="/forgot-password" element={<ForgotPasswordPage />} />
        <Route path="/reset-password" element={<ResetPasswordPage />} />

        {/* Public member experience — no login required */}
        <Route path="/join/:inviteToken" element={<JoinPage />} />
        <Route path="/survey/:instanceId" element={<SurveyPage />} />
        <Route path="/report/:token" element={<IndividualReportPage />} />

        {/* Leadership (authenticated) */}
        <Route path="/onboarding" element={<ProtectedRoute roles={['admin']}><OnboardingPage /></ProtectedRoute>} />
        <Route path="/dashboard" element={<ProtectedRoute roles={['leader', 'admin']}><DashboardPage /></ProtectedRoute>} />
        <Route path="/admin" element={<ProtectedRoute roles={['admin']}><AdminPage /></ProtectedRoute>} />

        <Route path="/" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
