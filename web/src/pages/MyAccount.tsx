import { useEffect, useState } from 'react'
import { API_BASE } from '../config'
import { Link } from 'react-router-dom'

export default function MyAccount() {
  const [me, setMe] = useState<any | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const email = localStorage.getItem('auth_user')
    if (!email) {
      setLoading(false)
      setMe(null)
      return
    }
    ;(async () => {
      try {
        setLoading(true)
        const res = await fetch(`${API_BASE}/auth/me`, {
          headers: { 'X-User-Email': email },
        })
        if (!res.ok) {
          const body = await res.json().catch(() => ({}))
          throw new Error(body.detail || `Failed to load profile: ${res.status}`)
        }
        const data = await res.json()
        setMe(data)
      } catch (e: any) {
        setError(e.message)
      } finally {
        setLoading(false)
      }
    })()
  }, [])

  if (!localStorage.getItem('auth_user')) {
    return (
      <div style={{ display: 'grid', gap: '0.5rem' }}>
        <h2 style={{ margin: 0 }}>My Account</h2>
        <div>You are not logged in.</div>
        <div>
          <Link to="/login">Log in</Link> or <Link to="/signup">Sign up</Link>
        </div>
      </div>
    )
  }

  if (loading) return <div>Loading profile…</div>
  if (error) return <div style={{ color: '#b00020' }}>{error}</div>
  if (!me) return <div>No profile found.</div>

  const p = me.profile || {}
  const name = p.full_name || [p.first_name, p.last_name].filter(Boolean).join(' ') || me.email

  return (
    <div style={{ display: 'grid', gap: '0.75rem' }}>
      <h2 style={{ margin: 0 }}>My Account</h2>
      <div style={{ border: '1px solid #eee', borderRadius: 8, padding: '0.75rem', display: 'grid', gap: '0.5rem' }}>
        <div><strong>Name:</strong> {name || '—'}</div>
        <div><strong>Email:</strong> {me.email}</div>
        <div><strong>Username:</strong> {p.username || '—'}</div>
        <div><strong>Phone:</strong> {p.phone || '—'}</div>
        <div><strong>Date of Birth:</strong> {p.date_of_birth || '—'}</div>
        <div><strong>Gender:</strong> {p.gender || '—'}</div>
        <div>
          <strong>Address:</strong>{' '}
          {p.address?.city || p.address?.state || p.address?.zip ? (
            <span>
              {[p.address?.city, p.address?.state, p.address?.zip].filter(Boolean).join(', ')}
            </span>
          ) : '—'}
        </div>
      </div>
    </div>
  )
}
