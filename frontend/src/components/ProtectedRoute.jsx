import { Navigate, useLocation } from 'react-router-dom'

import { useAuth } from '../context/AuthContext.jsx'
import Spinner from './Spinner.jsx'

export default function ProtectedRoute({ children }) {
  const { user, booting } = useAuth()
  const location = useLocation()

  if (booting) return <Spinner fullPage label="Checking your session…" />
  if (!user) return <Navigate to="/login" state={{ from: location.pathname }} replace />
  return children
}
