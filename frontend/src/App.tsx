import { lazy, Suspense } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './hooks/useAuth'

// Route-level code splitting: the heavy dashboard (recharts) is kept out of the
// member survey/report bundle.
const LoginPage = lazy(() => import('./pages/Login'))
const RegisterPage = lazy(() => import('./pages/Register'))
const VerifyEmailPage = lazy(() => import('./pages/VerifyEmail'))
const ForgotPasswordPage = lazy(() => import('./pages/ForgotPassword'))
const ResetPasswordPage = lazy(() => import('./pages/ResetPassword'))
const DashboardPage = lazy(() => import('./pages/Dashboard'))
const SurveyPage = lazy(() => import('./pages/Survey'))
const IndividualReportPage = lazy(() => import('./pages/IndividualReport'))
const AdminPage = lazy(() => import('./pages/Admin'))
const OnboardingPage = lazy(() => import('./pages/Onboarding'))
const JoinPage = lazy(() => import('./pages/Join'))

function Loading() {
  return (
    <div className="min-h-screen bg-[#0A0C10] flex items-center justify-center">
      <div className="text-white/40 text-sm" style={{ fontFamily: 'sans-serif' }}>Loading…</div>
    </div>
  )
}

function ProtectedRoute({ children, roles }: { children: React.ReactNode; roles?: string[] }) {
  const { isAuthenticated, role } = useAuthStore()
  if (!isAuthenticated()) return <Navigate to="/login" replace />
  if (roles && role && !roles.includes(role)) return <Navigate to="/dashboard" replace />
  return <>{children}</>
}

export default function App() {
  return (
    <BrowserRouter>
      <Suspense fallback={<Loading />}>
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
      </Suspense>
    </BrowserRouter>
  )
}
