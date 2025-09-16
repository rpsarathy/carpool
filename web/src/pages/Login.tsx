import { useState, useEffect } from 'react'
import { API_BASE } from '../config'
import { useNavigate } from 'react-router-dom'
import { initializeGoogleAuth, renderGoogleButton, type GoogleUser } from '../utils/googleAuth'

export default function Login() {
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  useEffect(() => {
    // Initialize Google Auth when component mounts
    initializeGoogleAuth().then(() => {
      renderGoogleButton('google-signin-button', handleGoogleSuccess)
    }).catch(err => {
      console.error('Failed to initialize Google Auth:', err)
    })
  }, [])

  const handleGoogleSuccess = (user: GoogleUser) => {
    setSuccess(`Welcome ${user.name}!`)
    
    // Store additional user info for session
    localStorage.setItem('auth_user', user.email)
    localStorage.setItem('user_name', user.name)
    
    // Trigger storage event for same-tab updates
    window.dispatchEvent(new StorageEvent('storage', {
      key: 'auth_user',
      newValue: user.email,
      storageArea: localStorage
    }))
    
    setTimeout(() => {
      navigate('/')
    }, 1000)
  }

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
      const res = await fetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: email.trim(), password })
      })
      if (!res.ok) {
        const body = await res.json().catch(() => ({}))
        throw new Error(body.detail || `Login failed: ${res.status}`)
      }
      setSuccess('Logged in!')
      // Frontend-only gate: mark user as authenticated
      localStorage.setItem('auth_user', email.trim())
      
      // Trigger storage event for same-tab updates
      window.dispatchEvent(new StorageEvent('storage', {
        key: 'auth_user',
        newValue: email.trim(),
        storageArea: localStorage
      }))
      
      // Small delay to ensure state updates before navigation
      setTimeout(() => {
        navigate('/')
      }, 100)
    } catch (e: any) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ display: 'grid', gap: '1rem', maxWidth: 420 }}>
      <div style={{ textAlign: 'center', marginBottom: '1rem' }}>
        <img src="/logo.svg" alt="Carpool" style={{ height: '60px', width: 'auto', marginBottom: '0.5rem' }} />
        <h2 style={{ margin: 0, color: '#1e40af' }}>Welcome to Carpool</h2>
        <p style={{ margin: '0.5rem 0 0 0', color: '#666', fontSize: '0.9rem' }}>Sign in to your account</p>
      </div>
      
      {/* Google Sign-In Button */}
      <div style={{ display: 'grid', gap: '0.5rem' }}>
        <div id="google-signin-button" style={{ width: '100%' }}></div>
      </div>
      
      {/* Divider */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', margin: '0.5rem 0' }}>
        <hr style={{ flex: 1, border: 'none', borderTop: '1px solid #ccc' }} />
        <span style={{ color: '#666', fontSize: '0.9rem' }}>or</span>
        <hr style={{ flex: 1, border: 'none', borderTop: '1px solid #ccc' }} />
      </div>

      {/* Traditional Login Form */}
      <form onSubmit={onSubmit} style={{ display: 'grid', gap: '0.75rem' }}>
        <label style={{ display: 'grid', gap: '0.25rem' }}>
          <span>Email</span>
          <input type="email" value={email} onChange={e => setEmail(e.target.value)} required style={{ padding: '0.5rem', borderRadius: 6, border: '1px solid #ccc' }} />
        </label>
        <label style={{ display: 'grid', gap: '0.25rem' }}>
          <span>Password</span>
          <input type="password" value={password} onChange={e => setPassword(e.target.value)} required style={{ padding: '0.5rem', borderRadius: 6, border: '1px solid #ccc' }} />
        </label>
        <button type="submit" disabled={loading} style={{ padding: '0.6rem 1rem', borderRadius: 6, backgroundColor: '#2563eb', color: 'white', border: 'none', cursor: loading ? 'not-allowed' : 'pointer' }}>{loading ? 'Logging in...' : 'Log in'}</button>
      </form>
      
      {error && <div style={{ color: '#b00020' }}>{error}</div>}
      {success && <div style={{ color: '#0a7d28' }}>{success}</div>}
    </div>
  )
}
