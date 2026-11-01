import { AlertCircle, Loader2 } from 'lucide-react'
import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import AuthShell from '../components/AuthShell.jsx'
import { useAuth } from '../context/AuthContext.jsx'

export default function Register() {
  const { register } = useAuth()
  const navigate = useNavigate()
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(event) {
    event.preventDefault()
    setError('')

    if (password.length < 8) {
      setError('Password must be at least 8 characters long.')
      return
    }

    setSubmitting(true)
    try {
      await register(name.trim(), email.trim(), password)
      navigate('/app', { replace: true })
    } catch (err) {
      setError(err.message || 'Could not create your account.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <AuthShell
      title="Create your account"
      subtitle="Keep your reports private and revisit your analysis at any time."
      footer={
        <>
          Already have an account?{' '}
          <Link to="/login" className="font-semibold text-medical-700 hover:text-medical-800">
            Sign in
          </Link>
        </>
      }
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        {error ? (
          <div className="flex items-start gap-2 rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">
            <AlertCircle size={16} className="mt-0.5 shrink-0" aria-hidden="true" />
            <span>{error}</span>
          </div>
        ) : null}

        <div>
          <label htmlFor="name" className="label">
            Full name
          </label>
          <input
            id="name"
            type="text"
            autoComplete="name"
            required
            maxLength={120}
            value={name}
            onChange={(event) => setName(event.target.value)}
            className="input"
            placeholder="Demo User"
          />
        </div>

        <div>
          <label htmlFor="email" className="label">
            Email address
          </label>
          <input
            id="email"
            type="email"
            autoComplete="email"
            required
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            className="input"
            placeholder="you@example.com"
          />
        </div>

        <div>
          <label htmlFor="password" className="label">
            Password
          </label>
          <input
            id="password"
            type="password"
            autoComplete="new-password"
            required
            minLength={8}
            maxLength={72}
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            className="input"
            placeholder="At least 8 characters"
          />
          <p className="mt-1 text-xs text-slate-500">
            Use a unique password. Medical documents are sensitive.
          </p>
        </div>

        <button type="submit" disabled={submitting} className="btn-primary w-full">
          {submitting ? <Loader2 size={16} className="animate-spin" aria-hidden="true" /> : null}
          {submitting ? 'Creating account…' : 'Create account'}
        </button>
      </form>
    </AuthShell>
  )
}
