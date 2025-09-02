import { useState } from 'react'
import { API_BASE } from '../config'

export default function Signup() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    setSuccess(null)
    if (!email.trim() || !password) {
      setError('Email and password are required')
      return
    }
    try {
      setLoading(true)
      const res = await fetch(`${API_BASE}/auth/signup`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: email.trim(), password })
      })
      if (!res.ok) {
        const body = await res.json().catch(() => ({}))
        throw new Error(body.detail || `Signup failed: ${res.status}`)
      }
      setSuccess('Account created! You can now log in.')
    } catch (e: any) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={onSubmit} style={{ display: 'grid', gap: '0.75rem', maxWidth: 420 }}>
      <h2 style={{ margin: 0 }}>Sign up</h2>
      <label style={{ display: 'grid', gap: '0.25rem' }}>
        <span>Email</span>
        <input type="email" value={email} onChange={e => setEmail(e.target.value)} required style={{ padding: '0.5rem', borderRadius: 6, border: '1px solid #ccc' }} />
      </label>
      <label style={{ display: 'grid', gap: '0.25rem' }}>
        <span>Password</span>
        <input type="password" value={password} onChange={e => setPassword(e.target.value)} required style={{ padding: '0.5rem', borderRadius: 6, border: '1px solid #ccc' }} />
      </label>
      <button type="submit" disabled={loading} style={{ padding: '0.6rem 1rem', borderRadius: 6 }}>{loading ? 'Creating account...' : 'Sign up'}</button>
      {error && <div style={{ color: '#b00020' }}>{error}</div>}
      {success && <div style={{ color: '#0a7d28' }}>{success}</div>}
    </form>
  )
}
