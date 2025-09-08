import { useState } from 'react'
import { API_BASE } from '../config'
import { useNavigate } from 'react-router-dom'

export default function Signup() {
  const navigate = useNavigate()
  // Required core fields
  const [fullName, setFullName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')

  // Optional fields
  const [phone, setPhone] = useState('')
  const [username, setUsername] = useState('')
  const [dob, setDob] = useState('') // yyyy-mm-dd
  const [gender, setGender] = useState('')
  const [city, setCity] = useState('')
  const [state, setState] = useState('')
  const [zip, setZip] = useState('')

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  function validate(): string | null {
    // Full name required
    if (!fullName.trim()) return 'Please provide your Full Name.'

    // Email
    const emailTrim = email.trim()
    if (!emailTrim) return 'Email is required.'
    const emailRe = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    if (!emailRe.test(emailTrim)) return 'Please enter a valid email address.'

    // Password rules: min 8, at least 1 letter, 1 number, 1 special
    if (password.length < 8) return 'Password must be at least 8 characters.'
    if (!/[A-Za-z]/.test(password)) return 'Password must include at least one letter.'
    if (!/\d/.test(password)) return 'Password must include at least one number.'
    if (!/[!@#$%^&*()_+\-=[\]{};':"\\|,.<>/?]/.test(password)) return 'Password must include at least one special character.'

    if (password !== confirmPassword) return 'Passwords do not match.'

    // Optional: simple phone validation (digits, +, -, spaces, parentheses)
    if (phone && !/^[+\d][\d\s().-]{6,}$/.test(phone)) return 'Please enter a valid phone number or leave it blank.'

    // Optional: age check (13+) when DOB provided
    if (dob) {
      const d = new Date(dob)
      if (isNaN(d.getTime())) return 'Please enter a valid date of birth or leave it blank.'
      const now = new Date()
      const age = now.getFullYear() - d.getFullYear() - (now < new Date(d.getFullYear(), d.getMonth(), d.getDate()) ? 1 : 0)
      if (age < 13) return 'You must be at least 13 years old to sign up.'
    }

    // Optional: zip simple validation (US 5 or 5-4)
    if (zip && !/^\d{5}(-\d{4})?$/.test(zip)) return 'Please enter a valid ZIP code or leave it blank.'

    return null
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    setSuccess(null)

    const v = validate()
    if (v) { setError(v); return }

    try {
      setLoading(true)
      const payload: any = {
        email: email.trim(),
        password,
        profile: {
          full_name: fullName.trim(),
          phone: phone.trim() || undefined,
          username: username.trim() || undefined,
          date_of_birth: dob || undefined,
          gender: gender || undefined,
          address: {
            city: city.trim() || undefined,
            state: state.trim() || undefined,
            zip: zip.trim() || undefined,
          }
        }
      }

      const res = await fetch(`${API_BASE}/auth/signup`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })
      if (!res.ok) {
        const body = await res.json().catch(() => ({}))
        // If backend sends structured errors, surface first one
        const detail = (body?.errors && typeof body.errors === 'object')
          ? Object.values(body.errors)[0] as string
          : (body.detail || `Signup failed: ${res.status}`)
        throw new Error(detail)
      }
      setSuccess('Account created! You can now log in.')
      // After a brief delay, take user to login
      setTimeout(() => navigate('/login'), 600)
    } catch (e: any) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={onSubmit} style={{ display: 'grid', gap: '0.75rem', maxWidth: 520 }}>
      <h2 style={{ margin: 0 }}>Sign up</h2>

      {/* Full Name */}
      <label style={{ display: 'grid', gap: '0.25rem' }}>
        <span>Full Name</span>
        <input value={fullName} onChange={e => setFullName(e.target.value)} placeholder="Full Name" required style={{ padding: '0.5rem', borderRadius: 6, border: '1px solid #ccc' }} />
      </label>

      {/* Email */}
      <label style={{ display: 'grid', gap: '0.25rem' }}>
        <span>Email Address</span>
        <input type="email" value={email} onChange={e => setEmail(e.target.value)} required placeholder="name@example.com" style={{ padding: '0.5rem', borderRadius: 6, border: '1px solid #ccc' }} />
        <small style={{ color: '#666' }}>A valid email is crucial for verification, communication, and password resets.</small>
      </label>

      {/* Passwords */}
      <div style={{ display: 'grid', gap: '0.5rem' }}>
        <label style={{ display: 'grid', gap: '0.25rem' }}>
          <span>Password</span>
          <input type="password" value={password} onChange={e => setPassword(e.target.value)} required placeholder="At least 8 chars, include letter, number, special" style={{ padding: '0.5rem', borderRadius: 6, border: '1px solid #ccc' }} />
          <small style={{ color: '#666' }}>It’s important to set password rules (min length, special characters, etc.) to ensure security.</small>
        </label>
        <label style={{ display: 'grid', gap: '0.25rem' }}>
          <span>Confirm Password</span>
          <input type="password" value={confirmPassword} onChange={e => setConfirmPassword(e.target.value)} required style={{ padding: '0.5rem', borderRadius: 6, border: '1px solid #ccc' }} />
          <small style={{ color: '#666' }}>Helps users avoid typos and ensures they enter the same password they intended.</small>
        </label>
      </div>

      {/* Optional section */}
      <fieldset style={{ border: '1px solid #eee', borderRadius: 8, padding: '0.75rem' }}>
        <legend style={{ padding: '0 6px', color: '#555' }}>Optional</legend>
        <div style={{ display: 'grid', gap: '0.5rem' }}>
          <label style={{ display: 'grid', gap: '0.25rem' }}>
            <span>Phone Number</span>
            <input value={phone} onChange={e => setPhone(e.target.value)} placeholder="e.g., +1 415 555 1234" style={{ padding: '0.5rem', borderRadius: 6, border: '1px solid #ccc' }} />
          </label>
          <label style={{ display: 'grid', gap: '0.25rem' }}>
            <span>Username</span>
            <input value={username} onChange={e => setUsername(e.target.value)} placeholder="Choose a unique username" style={{ padding: '0.5rem', borderRadius: 6, border: '1px solid #ccc' }} />
          </label>
          <label style={{ display: 'grid', gap: '0.25rem' }}>
            <span>Date of Birth</span>
            <input type="date" value={dob} onChange={e => setDob(e.target.value)} style={{ padding: '0.5rem', borderRadius: 6, border: '1px solid #ccc' }} />
            <small style={{ color: '#666' }}>For age verification or personalization.</small>
          </label>
          <label style={{ display: 'grid', gap: '0.25rem' }}>
            <span>Gender</span>
            <select value={gender} onChange={e => setGender(e.target.value)} style={{ padding: '0.5rem', borderRadius: 6, border: '1px solid #ccc', background: 'white' }}>
              <option value="">Prefer not to say</option>
              <option value="female">Female</option>
              <option value="male">Male</option>
              <option value="nonbinary">Non-binary</option>
              <option value="other">Other</option>
            </select>
          </label>
          <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
            <label style={{ display: 'grid', gap: '0.25rem', flex: '1 1 160px' }}>
              <span>City</span>
              <input value={city} onChange={e => setCity(e.target.value)} style={{ padding: '0.5rem', borderRadius: 6, border: '1px solid #ccc' }} />
            </label>
            <label style={{ display: 'grid', gap: '0.25rem', flex: '1 1 140px' }}>
              <span>State</span>
              <input value={state} onChange={e => setState(e.target.value)} style={{ padding: '0.5rem', borderRadius: 6, border: '1px solid #ccc' }} />
            </label>
            <label style={{ display: 'grid', gap: '0.25rem', flex: '1 1 120px' }}>
              <span>Zip Code</span>
              <input value={zip} onChange={e => setZip(e.target.value)} placeholder="12345 or 12345-6789" style={{ padding: '0.5rem', borderRadius: 6, border: '1px solid #ccc' }} />
            </label>
          </div>
        </div>
      </fieldset>

      <button type="submit" disabled={loading} style={{ padding: '0.6rem 1rem', borderRadius: 6, backgroundColor: '#2563eb', color: 'white', border: 'none', cursor: loading ? 'not-allowed' : 'pointer' }}>{loading ? 'Creating account...' : 'Sign up'}</button>
      {error && <div style={{ color: '#b00020' }}>{error}</div>}
      {success && <div style={{ color: '#0a7d28' }}>{success}</div>}
    </form>
  )
}
