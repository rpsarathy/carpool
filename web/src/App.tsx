import { useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Link, Navigate, Route, Routes, useLocation } from 'react-router-dom'
import { API_BASE, GOOGLE_API_KEY } from './config'
import Login from './pages/Login'
import Signup from './pages/Signup'
import MyAccount from './pages/MyAccount'
import Admin from './pages/Admin'

// Minimal ambient to prevent TS errors when Google JS hasn't loaded at type-check time
declare const google: any

interface Member {
  name: string
  email?: string | null
}

interface Group {
  id: number
  name: string
  members: Member[]
  days?: string[]
  cycle_days?: number
}

interface ScheduleItem {
  date: string // ISO date
  driver: string
}

interface StoredSchedule {
  start_date: string
  end_date: string
  items: ScheduleItem[]
}

export default function App() {
  const navigate = useNavigate()
  type Mode = 'regular' | 'on_demand'
  const [mode, setMode] = useState<Mode>('regular')
  const [name, setName] = useState('')
  const [members, setMembers] = useState<Member[]>([{ name: '', email: '' }])
  const [days, setDays] = useState<string[]>([])
  const [cycleDays, setCycleDays] = useState<number>(10)
  const [groups, setGroups] = useState<Group[]>([])
  const [selectedGroup, setSelectedGroup] = useState<string>('')
  const [startDate, setStartDate] = useState<string>(() => new Date().toISOString().slice(0, 10))
  const [schedule, setSchedule] = useState<ScheduleItem[] | null>(null)
  const [savedSchedule, setSavedSchedule] = useState<StoredSchedule | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [schedError, setSchedError] = useState<string | null>(null)
  const [odDest, setOdDest] = useState<string>('')
  const [odOrigin, setOdOrigin] = useState<{ lat: number; lng: number } | null>(null)
  const [odDestCoord, setOdDestCoord] = useState<{ lat: number; lng: number } | null>(null)
  const [odStatus, setOdStatus] = useState<string | null>(null)
  const [odError, setOdError] = useState<string | null>(null)
  const [odDate, setOdDate] = useState<string>('')
  const [odDriver, setOdDriver] = useState<string>('')
  const [odDriverEnabled, setOdDriverEnabled] = useState<boolean>(false)
  const [availableDrivers, setAvailableDrivers] = useState<string[]>([])
  const [odRequests, setOdRequests] = useState<Array<{ id: number; origin_lat: number; origin_lng: number; destination: string; dest_lat: number; dest_lng: number; created_at: string }>>([])
  const [odSearch, setOdSearch] = useState('')
  const [odPage, setOdPage] = useState(1)
  const [odPageSize, setOdPageSize] = useState(10)
  const [originAddrCache, setOriginAddrCache] = useState<Record<string, string>>({})

  // Google Places Autocomplete state (widget-based)
  const [gPlacesReady, setGPlacesReady] = useState(false)
  const destInputRef = useRef<HTMLInputElement | null>(null)
  const autocompleteRef = useRef<any>(null)
  const [odDestPlaceId, setOdDestPlaceId] = useState<string | null>(null)
  const [odDestAddress, setOdDestAddress] = useState<string | null>(null)

  // Simple frontend auth gate
  const [authed, setAuthed] = useState<boolean>(() => !!localStorage.getItem('auth_user'))
  const [meName, setMeName] = useState<string | null>(null)
  
  // Function to update auth state manually
  const updateAuthState = () => {
    setAuthed(!!localStorage.getItem('auth_user'))
  }
  
  useEffect(() => {
    const onStorage = (e: StorageEvent) => {
      if (e.key === 'auth_user') {
        setAuthed(!!localStorage.getItem('auth_user'))
      }
    }
    
    // Listen for both storage events and custom auth events
    window.addEventListener('storage', onStorage)
    window.addEventListener('auth-updated', updateAuthState)
    
    return () => {
      window.removeEventListener('storage', onStorage)
      window.removeEventListener('auth-updated', updateAuthState)
    }
  }, [])

  // Fetch current user profile to show name in header
  useEffect(() => {
    if (!authed) { setMeName(null); return }
    const email = localStorage.getItem('auth_user')
    if (!email) { setMeName(null); return }
    ;(async () => {
      try {
        const res = await fetch(`${API_BASE}/auth/me`, { headers: { 'X-User-Email': email } })
        if (!res.ok) return
        const data = await res.json()
        const p = data?.profile || {}
        const name = p.full_name || [p.first_name, p.last_name].filter(Boolean).join(' ') || data?.email || null
        setMeName(name)
      } catch {
        setMeName(null)
      }
    })()
  }, [authed])

  const cleanedMembers = useMemo(() =>
    members
      .map(m => ({ name: m.name?.trim() ?? '', email: (m.email ?? '').toString().trim() }))
      .filter(m => m.name),
    [members]
  )

  const WEEKDAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'] as const

  function toggleDay(day: string) {
    setDays(prev => (prev.includes(day) ? prev.filter(d => d !== day) : [...prev, day]))
  }

  function addMemberRow() {
    setMembers(prev => [...prev, { name: '', email: '' }])
  }

  function updateMember(index: number, field: 'name' | 'email', value: string) {
    setMembers(prev => prev.map((m, i) => (i === index ? { ...m, [field]: value } : m)))
  }

  function removeMember(index: number) {
    setMembers(prev => prev.filter((_, i) => i !== index))
  }

  async function fetchGroups() {
    try {
      setLoading(true)
      const res = await fetch(`${API_BASE}/groups`)
      if (!res.ok) throw new Error(`Failed to fetch groups: ${res.status}`)
      const data: Group[] = await res.json()
      setGroups(data)
      if (data.length > 0 && !selectedGroup) setSelectedGroup(data[0].name)
    } catch (e: any) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchGroups()
  }, [])

  useEffect(() => {
    async function fetchSaved() {
      if (!selectedGroup) {
        setSavedSchedule(null)
        return
      }
      try {
        const res = await fetch(`${API_BASE}/groups/${encodeURIComponent(selectedGroup)}/schedule`)
        if (res.status === 404) {
          setSavedSchedule(null)
          return
        }
        if (!res.ok) throw new Error(`Failed to load saved schedule: ${res.status}`)
        const data: StoredSchedule = await res.json()
        setSavedSchedule(data)
        setSchedule(data.items) // show saved schedule by default
      } catch (e: any) {
        // Don't hard-block UI; just show nothing
        console.error(e)
      }
    }
    fetchSaved()
  }, [selectedGroup])

  useEffect(() => {
    if (mode !== 'on_demand') return
    ;(async () => {
      try {
        const res = await fetch(`${API_BASE}/on_demand/requests`)
        if (!res.ok) throw new Error(`Failed to load requests: ${res.status}`)
        const data = await res.json()
        setOdRequests(data)
        setOdPage(1)
      } catch (e: any) {
        console.warn(e)
      }
    })()
  }, [mode])

  // Load Google Maps JS with Places library when needed
  useEffect(() => {
    if (mode !== 'on_demand') return
    if (gPlacesReady) return
    if (!GOOGLE_API_KEY) return
    const exists = document.querySelector('script[data-g-places="1"]') as HTMLScriptElement | null
    if (exists) {
      if ((window as any).google?.maps?.places) setGPlacesReady(true)
      return
    }
    const s = document.createElement('script')
    s.src = `https://maps.googleapis.com/maps/api/js?key=${GOOGLE_API_KEY}&libraries=places&v=weekly`
    s.async = true
    s.defer = true
    s.dataset.gPlaces = '1'
    s.onload = () => {
      if ((window as any).google?.maps?.places) setGPlacesReady(true)
    }
    s.onerror = () => {
      console.warn('Failed to load Google Maps JS')
    }
    document.head.appendChild(s)
  }, [mode, gPlacesReady])

  // Initialize Places Autocomplete widget on destination input
  useEffect(() => {
    if (!gPlacesReady) return
    if (!destInputRef.current) return
    // Avoid re-initialization
    if (autocompleteRef.current) return
    try {
      const ac = new google.maps.places.Autocomplete(destInputRef.current, {
        // Request needed fields on getPlace()
        fields: ['place_id', 'formatted_address', 'geometry', 'name'],
        // Optional: types: ['establishment', 'geocode']
      })
      autocompleteRef.current = ac
      ac.addListener('place_changed', () => {
        const place = ac.getPlace()
        if (!place) return
        const addr = place.formatted_address || place.name || ''
        const id = place.place_id || null
        const loc = place.geometry?.location
        if (addr) setOdDest(addr)
        if (id) setOdDestPlaceId(id)
        if (addr) setOdDestAddress(addr)
        if (loc) {
          const lat = typeof loc.lat === 'function' ? loc.lat() : (loc as any).lat
          const lng = typeof loc.lng === 'function' ? loc.lng() : (loc as any).lng
          setOdDestCoord({ lat, lng })
          setOdStatus('Destination located')
        } else {
          setOdDestCoord(null)
        }
      })
    } catch (e) {
      console.warn('Failed to init Places Autocomplete', e)
    }
  }, [gPlacesReady])

  // Apply location bias near detected origin when it changes
  useEffect(() => {
    if (!autocompleteRef.current) return
    if (!odOrigin) return
    try {
      autocompleteRef.current.setOptions({
        locationBias: { center: { lat: odOrigin.lat, lng: odOrigin.lng }, radiusMeters: 20000 },
      })
    } catch {}
  }, [odOrigin?.lat, odOrigin?.lng])

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    setSuccess(null)

    if (!name.trim() || cleanedMembers.length === 0) {
      setError('Please provide a group name and at least one member.')
      return
    }
    if (days.length === 0) {
      setError('Please select at least one weekday.')
      return
    }

    try {
      setLoading(true)
      const res = await fetch(`${API_BASE}/groups`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: name.trim(), members: cleanedMembers, days, cycle_days: cycleDays })
      })

      if (res.status === 409) {
        const body = await res.json().catch(() => ({}))
        throw new Error(body.detail || 'Group name already exists')
      }
      if (!res.ok) {
        const body = await res.json().catch(() => ({}))
        throw new Error(body.detail || `Failed to create group: ${res.status}`)
      }

      setSuccess('Group created')
      setName('')
      setMembers([{ name: '', email: '' }])
      setDays([])
      setCycleDays(10)
      await fetchGroups()
    } catch (e: any) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  async function onDeleteGroup(groupName: string) {
    if (!confirm(`Delete carpool "${groupName}"? This cannot be undone.`)) return
    try {
      setLoading(true)
      const res = await fetch(`${API_BASE}/groups/${encodeURIComponent(groupName)}`, { method: 'DELETE' })
      if (!res.ok && res.status !== 204) {
        const body = await res.json().catch(() => ({}))
        throw new Error(body.detail || `Failed to delete group: ${res.status}`)
      }
      // Refresh
      await fetchGroups()
      if (selectedGroup === groupName) {
        setSelectedGroup(() => (groups.find(g => g.name !== groupName)?.name ?? ''))
      }
    } catch (e: any) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  async function onGenerateSchedule() {
    setSchedError(null)
    setSchedule(null)
    if (!selectedGroup) {
      setSchedError('Please select a group')
      return
    }
    if (!startDate) {
      setSchedError('Please pick a start date')
      return
    }
    // Prevent regeneration locally if current cycle is still active
    const activeUntil = savedSchedule ? new Date(savedSchedule.end_date) : null
    if (activeUntil && new Date() <= activeUntil) {
      setSchedError(`Schedule already active until ${activeUntil.toLocaleDateString()}`)
      if (savedSchedule) setSchedule(savedSchedule.items)
      return
    }
    try {
      setLoading(true)
      const res = await fetch(`${API_BASE}/groups/${encodeURIComponent(selectedGroup)}/schedule`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ start_date: startDate })
      })
      if (!res.ok) {
        // If server blocks with 409, it may include the existing schedule in detail
        if (res.status === 409) {
          const body = await res.json().catch(() => ({}))
          const message = (typeof body.detail === 'string') ? body.detail : (body.detail?.message || 'Schedule already active')
          const existing = (typeof body.detail === 'object') ? body.detail.schedule : undefined
          setSchedError(message)
          if (existing?.items) {
            const ss: StoredSchedule = {
              start_date: existing.start_date,
              end_date: existing.end_date,
              items: existing.items,
            }
            setSavedSchedule(ss)
            setSchedule(ss.items)
          }
          return
        }
        const body = await res.json().catch(() => ({}))
        throw new Error(body.detail || `Failed to generate schedule: ${res.status}`)
      }
      const items: ScheduleItem[] = await res.json()
      setSchedule(items.map(i => ({ ...i, date: i.date })))
      // Save freshly generated schedule in local state so UI reflects lock-out
      const end = items.length ? items[items.length - 1].date : startDate
      setSavedSchedule({ start_date: startDate, end_date: end, items })
    } catch (e: any) {
      setSchedError(e.message)
    } finally {
      setLoading(false)
    }
  }

  async function detectCurrentLocationOd() {
    setOdError(null)
    setOdStatus('Detecting current location...')
    // Use browser geolocation only. Many API keys with HTTP referrer restrictions cannot call Google Geolocation API from the browser.
    const geoPromise = () => new Promise<GeolocationPosition>((resolve, reject) => {
      if (!navigator.geolocation) reject(new Error('Geolocation not supported on this browser'))
      navigator.geolocation.getCurrentPosition(resolve, reject, { enableHighAccuracy: true, timeout: 10000 })
    })
    try {
      const pos = await geoPromise()
      setOdOrigin({ lat: pos.coords.latitude, lng: pos.coords.longitude })
      setOdStatus('Current location detected')
    } catch (e: any) {
      const msg = e?.message?.toLowerCase?.() || ''
      if (msg.includes('permission') || msg.includes('denied')) {
        setOdError('Location permission denied. Please allow location access in your browser settings and try again.')
      } else if (msg.includes('timeout')) {
        setOdError('Timed out detecting location. Try again from a spot with better GPS/Wi‑Fi reception.')
      } else {
        setOdError('Failed to detect current location on this device')
      }
      setOdStatus(null)
    }
  }

  // Input change: keep local value in sync and clear previous selection
  function onDestInputChange(val: string) {
    setOdDest(val)
    setOdDestCoord(null)
    setOdDestPlaceId(null)
    setOdDestAddress(null)
  }

  async function submitOnDemandRequestOd() {
    setOdError(null)
    setOdStatus('Submitting request...')
    if (!authed) {
      setOdError('Please log in to request a carpool')
      setOdStatus(null)
      navigate('/login')
      return
    }
    if (!odOrigin) {
      setOdError('Please detect your current location first')
      setOdStatus(null)
      return
    }
    if (!odDestCoord || !odDest.trim()) {
      setOdError('Please enter and geocode a destination')
      setOdStatus(null)
      return
    }
    if (!odDate) {
      setOdError('Please select a date')
      setOdStatus(null)
      return
    }
    if (odDriverEnabled && !odDriver) {
      setOdError('Please select a driver')
      setOdStatus(null)
      return
    }
    try {
      const res = await fetch(`${API_BASE}/on-demand/requests`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          origin_lat: odOrigin.lat,
          origin_lng: odOrigin.lng,
          destination: odDest.trim(),
          dest_lat: odDestCoord.lat,
          dest_lng: odDestCoord.lng,
          dest_place_id: odDestPlaceId,
          dest_address: odDestAddress || odDest.trim(),
          date: odDate,
          driver: odDriverEnabled ? odDriver : null,
        })
      })
      if (!res.ok) {
        const body = await res.json().catch(() => ({}))
        throw new Error(body.detail || `Failed to submit request: ${res.status}`)
      }
      setOdStatus('Request submitted successfully!')
      // Clear form
      setOdDest('')
      setOdDestCoord(null)
      setOdDate('')
      setOdDriver('')
      setOdDriverEnabled(false)
      setOdOrigin(null)
      // refresh list
      const list = await fetch(`${API_BASE}/on_demand/requests`).then(r => r.json()).catch(() => [])
      setOdRequests(Array.isArray(list) ? list : [])
    } catch (e: any) {
      setOdError(e.message || 'Failed to submit request')
      setOdStatus(null)
    }
  }

  async function reverseGeocode(lat: number, lng: number): Promise<string | null> {
    const key = `${lat.toFixed(5)},${lng.toFixed(5)}`
    if (originAddrCache[key]) return originAddrCache[key]
    try {
      const url = `https://maps.googleapis.com/maps/api/geocode/json?latlng=${lat},${lng}&key=${GOOGLE_API_KEY}`
      const res = await fetch(url)
      if (!res.ok) throw new Error(`Reverse geocode failed: ${res.status}`)
      const data = await res.json()
      if (data.status !== 'OK' || !data.results?.length) return null
      const addr = data.results[0]?.formatted_address || null
      if (addr) setOriginAddrCache(prev => ({ ...prev, [key]: addr }))
      return addr
    } catch (e) {
      return null
    }
  }

  useEffect(() => {
    if (mode !== 'on_demand' || odRequests.length === 0) return
    const filtered = odRequests.filter(r => {
      const q = odSearch.trim().toLowerCase()
      if (!q) return true
      const addrKey = `${r.origin_lat.toFixed(5)},${r.origin_lng.toFixed(5)}`
      const addr = originAddrCache[addrKey]
      return (
        r.destination.toLowerCase().includes(q) ||
        addr.toLowerCase().includes(q)
      )
    })
    const total = filtered.length
    const totalPages = Math.max(1, Math.ceil(total / odPageSize))
    const page = Math.min(odPage, totalPages)
    const start = (page - 1) * odPageSize
    const pageItems = filtered.slice(start, start + odPageSize)
    // Prefetch reverse geocodes in parallel (best-effort)
    pageItems.forEach(item => {
      const key = `${item.origin_lat.toFixed(5)},${item.origin_lng.toFixed(5)}`
      if (!originAddrCache[key]) reverseGeocode(item.origin_lat, item.origin_lng)
    })
  }, [mode, odRequests, odSearch, odPage, odPageSize])

  function Nav() {
    const loc = useLocation()
    const isActive = (path: string) => (loc.pathname === path ? { background: '#eef2ff', color: '#1f3a8a' } : {})
    
    const handleLogout = () => {
      localStorage.removeItem('auth_user')
      setAuthed(false)
      setMeName(null)
      navigate('/login')
    }
    
    return (
      <nav style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem' }}>
        {authed && mode === 'regular' && (
          <>
            <Link to="/details" style={{ padding: '0.5rem 0.75rem', borderRadius: 8, border: '1px solid #ddd', textDecoration: 'none', color: '#111', ...isActive('/details') }}>
              Car Pool Details
            </Link>
            <Link to="/schedule" style={{ padding: '0.5rem 0.75rem', borderRadius: 8, border: '1px solid #ddd', textDecoration: 'none', color: '#111', ...isActive('/schedule') }}>
              Generate Car Pool Schedule
            </Link>
          </>
        )}
        {authed && mode === 'on_demand' && (
          <>
            <Link to="/on-demand" style={{ padding: '0.5rem 0.75rem', borderRadius: 8, border: '1px solid #ddd', textDecoration: 'none', color: '#111', ...isActive('/on-demand') }}>
              Request Carpool
            </Link>
            <Link to="/on-demand/manage" style={{ padding: '0.5rem 0.75rem', borderRadius: 8, border: '1px solid #ddd', textDecoration: 'none', color: '#111', ...isActive('/on-demand/manage') }}>
              Manage On-Demand
            </Link>
          </>
        )}
        <span style={{ flex: 1 }} />
        {authed && meName && (
          <span style={{ alignSelf: 'center', color: '#333' }}>Welcome, {meName}</span>
        )}
        {authed ? (
          <>
            <Link to="/account" style={{ padding: '0.5rem 0.75rem', borderRadius: 8, border: '1px solid #ddd', textDecoration: 'none', color: '#111', ...isActive('/account') }}>
              My Account
            </Link>
            <Link to="/admin" style={{ padding: '0.5rem 0.75rem', borderRadius: 8, border: '1px solid #ddd', textDecoration: 'none', color: '#111', ...isActive('/admin') }}>
              Admin
            </Link>
            <button 
              onClick={handleLogout} 
              style={{ padding: '0.5rem 0.75rem', borderRadius: 8, border: '1px solid #ddd', backgroundColor: 'transparent', color: '#111', cursor: 'pointer', textDecoration: 'none' }}
            >
              Log out
            </button>
          </>
        ) : (
          <>
            <Link to="/login" style={{ padding: '0.5rem 0.75rem', borderRadius: 8, border: '1px solid #ddd', textDecoration: 'none', color: '#111', ...isActive('/login') }}>
              Log in
            </Link>
            <Link to="/signup" style={{ padding: '0.5rem 0.75rem', borderRadius: 8, border: '1px solid #ddd', textDecoration: 'none', color: '#111', ...isActive('/signup') }}>
              Sign up
            </Link>
          </>
        )}
      </nav>
    )
  }

  return (
    <div style={{ minHeight: '100vh', display: 'grid', placeItems: 'center', background: '#f7f7f8' }}>
      <div style={{ width: 'min(900px, 92vw)', background: '#fff', padding: '1.5rem', borderRadius: 12, boxShadow: '0 10px 30px rgba(0,0,0,0.06)', fontFamily: 'system-ui, sans-serif' }}>
        <h1 style={{ marginTop: 0, marginBottom: '1rem' }}>Carpool</h1>
        {/* Schedule type selector */}
        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center', marginBottom: '0.75rem' }}>
          <span style={{ fontWeight: 600 }}>Schedule type:</span>
          <label style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
            <input type="radio" name="mode" checked={mode === 'regular'} onChange={() => setMode('regular')} /> Regular
          </label>
          <label style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
            <input type="radio" name="mode" checked={mode === 'on_demand'} onChange={() => setMode('on_demand')} /> On-Demand
          </label>
        </div>
        <Nav />

        {/* On-demand UI is rendered in Routes under /on-demand and /on-demand/manage */}

        <Routes>
          <Route path="/" element={<Navigate to={authed ? (mode === 'regular' ? '/details' : '/on-demand') : '/login'} replace />} />
          {mode === 'regular' && authed && (
            <Route path="/details" element={
              <form onSubmit={onSubmit} style={{ display: 'grid', gap: '0.75rem', marginBottom: '1.5rem' }}>
                <label style={{ display: 'grid', gap: '0.25rem' }}>
                  <span>Carpool name</span>
                  <input
                    value={name}
                    onChange={e => setName(e.target.value)}
                    placeholder="e.g., Office Commute"
                    required
                    style={{ width: '100%', padding: '0.5rem', borderRadius: 6, border: '1px solid #ccc' }}
                  />
                </label>

                <div style={{ display: 'grid', gap: '0.5rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <span>Members</span>
                    <button type="button" onClick={addMemberRow} style={{ padding: '0.35rem 0.65rem', borderRadius: 6, backgroundColor: '#2563eb', color: 'white', border: 'none', cursor: 'pointer' }}>+ Add member</button>
                  </div>
                  <div style={{ display: 'grid', gap: '0.5rem' }}>
                    {members.map((m, idx) => (
                      <div key={idx} style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', alignItems: 'center' }}>
                        <input
                          placeholder="Name"
                          value={m.name}
                          onChange={e => updateMember(idx, 'name', e.target.value)}
                          required={idx === 0}
                          style={{ flex: '1 1 220px', minWidth: 0, padding: '0.5rem', borderRadius: 6, border: '1px solid #ccc' }}
                        />
                        <input
                          placeholder="Email (optional)"
                          value={m.email ?? ''}
                          onChange={e => updateMember(idx, 'email', e.target.value)}
                          style={{ flex: '1 1 260px', minWidth: 0, padding: '0.5rem', borderRadius: 6, border: '1px solid #ccc' }}
                        />
                        <button type="button" onClick={() => removeMember(idx)} aria-label="Remove member" style={{ padding: '0.4rem 0.6rem', borderRadius: 6, whiteSpace: 'nowrap', backgroundColor: '#2563eb', color: 'white', border: 'none', cursor: 'pointer' }}>Remove</button>
                      </div>
                    ))}
                  </div>
                  <small style={{ color: '#666' }}>Email is optional. At least one member name is required.</small>
                </div>

                <div style={{ display: 'grid', gap: '0.5rem' }}>
                  <span>Carpool days</span>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                    {WEEKDAYS.map(d => (
                      <label key={d} style={{ display: 'inline-flex', alignItems: 'center', gap: '0.35rem', padding: '0.35rem 0.5rem', border: '1px solid #ddd', borderRadius: 8 }}>
                        <input
                          type="checkbox"
                          checked={days.includes(d)}
                          onChange={() => toggleDay(d)}
                        />
                        <span>{d}</span>
                      </label>
                    ))}
                  </div>
                </div>

                <label style={{ display: 'grid', gap: '0.25rem', maxWidth: 220 }}>
                  <span>Carpool cycle (days)</span>
                  <select
                    value={cycleDays}
                    onChange={e => setCycleDays(parseInt(e.target.value))}
                    style={{ width: '100%', padding: '0.5rem', borderRadius: 6, border: '1px solid #ccc', background: 'white' }}
                  >
                    <option value={10}>10 days</option>
                    <option value={20}>20 days</option>
                    <option value={30}>30 days</option>
                  </select>
                </label>

                <button type="submit" disabled={loading} style={{ padding: '0.6rem 1rem', borderRadius: 6, backgroundColor: '#2563eb', color: 'white', border: 'none', cursor: loading ? 'not-allowed' : 'pointer' }}>
                  {loading ? 'Saving...' : 'Create carpool'}
                </button>

                {error && (
                  <div style={{ color: '#b00020' }}>
                    {error}
                  </div>
                )}
                {success && (
                  <div style={{ color: '#0a7d28' }}>
                    {success}
                  </div>
                )}

                <h2>Existing carpools</h2>
                {loading && groups.length === 0 ? (
                  <div>Loading...</div>
                ) : groups.length === 0 ? (
                  <div>No groups yet.</div>
                ) : (
                  <ul style={{ paddingLeft: '1rem' }}>
                    {groups.map(g => (
                      <li key={g.id} style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', flexWrap: 'wrap' }}>
                        <div style={{ flex: 1 }}>
                          <strong>{g.name}</strong>: {g.members.map(m => m.email ? `${m.name} (${m.email})` : m.name).join(', ')}
                          {Array.isArray(g.days) && g.days.length > 0 ? (
                            <> — Days: {g.days.join(', ')}</>
                          ) : null}
                          {typeof g.cycle_days === 'number' ? (
                            <> — Cycle: {g.cycle_days} days</>
                          ) : null}
                        </div>
                        <button type="button" onClick={() => onDeleteGroup(g.name)} style={{ padding: '0.4rem 0.6rem', borderRadius: 6, backgroundColor: '#2563eb', color: 'white', border: 'none', cursor: 'pointer' }}>Delete</button>
                      </li>
                    ))}
                  </ul>
                )}
              </form>
            } />
          )}
          {mode === 'regular' && authed && (
            <Route path="/schedule" element={
              <div style={{ display: 'grid', gap: '0.75rem' }}>
                <label style={{ display: 'grid', gap: '0.25rem', maxWidth: 360 }}>
                  <span>Select group</span>
                  <select
                    value={selectedGroup}
                    onChange={e => setSelectedGroup(e.target.value)}
                    style={{ width: '100%', padding: '0.5rem', borderRadius: 6, border: '1px solid #ccc', background: 'white' }}
                  >
                    {groups.map(g => (
                      <option key={g.id} value={g.name}>{g.name}</option>
                    ))}
                  </select>
                </label>
                <label style={{ display: 'grid', gap: '0.25rem', maxWidth: 220 }}>
                  <span>Start date</span>
                  <input type="date" value={startDate} onChange={e => setStartDate(e.target.value)}
                    style={{ width: '100%', padding: '0.5rem', borderRadius: 6, border: '1px solid #ccc' }} />
                </label>
                <div>
                  <button
                    onClick={onGenerateSchedule}
                    disabled={
                      loading || groups.length === 0 || (
                        savedSchedule ? (new Date() <= new Date(savedSchedule.end_date)) : false
                      )
                    }
                    style={{ padding: '0.6rem 1rem', borderRadius: 6, backgroundColor: '#2563eb', color: 'white', border: 'none', cursor: (loading || groups.length === 0 || (savedSchedule ? (new Date() <= new Date(savedSchedule.end_date)) : false)) ? 'not-allowed' : 'pointer' }}
                  >
                    {loading ? 'Generating...' : 'Generate schedule'}
                  </button>
                </div>
                {schedError && <div style={{ color: '#b00020' }}>{schedError}</div>}

                {/* Show saved/active notice */}
                {savedSchedule && (
                  <div style={{ color: '#1f3a8a' }}>
                    Active schedule from {new Date(savedSchedule.start_date).toLocaleDateString()} to {new Date(savedSchedule.end_date).toLocaleDateString()}
                  </div>
                )}

                {schedule && (
                  <div style={{ marginTop: '0.5rem' }}>
                    <h3 style={{ margin: '0 0 0.5rem' }}>Schedule</h3>
                    <ul style={{ paddingLeft: '1rem' }}>
                      {schedule.map((item, idx) => (
                        <li key={idx}>
                          {new Date((item.date.includes('T') ? item.date : `${item.date}T00:00:00`)).toLocaleDateString(undefined, { day: '2-digit', month: 'short', year: 'numeric', weekday: 'short' })}
                          {': '}<strong>{item.driver}</strong>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            } />
          )}
          {mode === 'regular' && authed && (
            <Route path="/admin" element={<Admin />} />
          )}
          {authed && (
            <Route path="/on-demand" element={
              <div style={{ display: 'grid', gap: '0.75rem' }}>
                <h2>Request Carpool (On-Demand)</h2>
                <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                  <button type="button" onClick={detectCurrentLocationOd} style={{ padding: '0.5rem 0.75rem', borderRadius: 6, backgroundColor: '#2563eb', color: 'white', border: 'none', cursor: 'pointer' }}>Use My Current Location</button>
                  {odOrigin && (
                    <a href={`https://www.google.com/maps?q=${odOrigin.lat},${odOrigin.lng}`} target="_blank" rel="noreferrer" style={{ textDecoration: 'none' }}>
                      View Origin on Maps ↗
                    </a>
                  )}
                </div>

                <label style={{ display: 'grid', gap: '0.25rem' }}>
                  <span>Destination</span>
                  <input
                    ref={destInputRef}
                    value={odDest}
                    onChange={e => onDestInputChange(e.target.value)}
                    placeholder="Start typing a destination..."
                    autoComplete="off"
                    style={{ width: '100%', padding: '0.5rem', borderRadius: 6, border: '1px solid #ccc' }}
                  />
                </label>
                {odDestCoord && (
                  <div style={{ marginTop: 6 }}>
                    <a href={`https://www.google.com/maps?q=${odDestCoord.lat},${odDestCoord.lng}`} target="_blank" rel="noreferrer" style={{ textDecoration: 'none' }}>
                      View Destination on Maps ↗
                    </a>
                  </div>
                )}
                <label style={{ display: 'grid', gap: '0.25rem', maxWidth: 220 }}>
                  <span>Date</span>
                  <input type="date" value={odDate} onChange={e => setOdDate(e.target.value)}
                    style={{ width: '100%', padding: '0.5rem', borderRadius: 6, border: '1px solid #ccc' }} />
                </label>
                <label style={{ display: 'grid', gap: '0.25rem', maxWidth: 220 }}>
                  <span>Preferred Driver (Optional)</span>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <input 
                      type="checkbox" 
                      checked={odDriverEnabled} 
                      onChange={e => setOdDriverEnabled(e.target.checked)}
                      id="driver-checkbox"
                    />
                    <label htmlFor="driver-checkbox" style={{ fontSize: '0.9rem' }}>
                      Request specific driver
                    </label>
                  </div>
                  {odDriverEnabled && (
                    <select
                      value={odDriver}
                      onChange={e => setOdDriver(e.target.value)}
                      style={{ width: '100%', padding: '0.5rem', borderRadius: 6, border: '1px solid #ccc', background: 'white' }}
                    >
                      <option value="">Select a driver</option>
                      {availableDrivers.map(d => (
                        <option key={d} value={d}>{d}</option>
                      ))}
                    </select>
                  )}
                </label>
                <div>
                  <button
                    type="button"
                    onClick={submitOnDemandRequestOd}
                    disabled={!authed || !odOrigin || !odDestCoord || !odDate || (odDriverEnabled && !odDriver)}
                    style={{ padding: '0.6rem 1rem', borderRadius: 6, backgroundColor: '#2563eb', color: 'white', border: 'none', cursor: (!authed || !odOrigin || !odDestCoord || !odDate || (odDriverEnabled && !odDriver)) ? 'not-allowed' : 'pointer' }}
                  >
                    {authed ? 'Request Carpool' : 'Log in to Request'}
                  </button>
                  {!authed && (
                    <span style={{ marginLeft: 8, fontSize: 13 }}>
                      <Link to="/login">Log in</Link> or <Link to="/signup">Sign up</Link> to request a carpool
                    </span>
                  )}
                </div>

                {odError && <div style={{ color: '#b00020' }}>{odError}</div>}
                {odStatus && <div style={{ color: '#0a7d28' }}>{odStatus}</div>}
              </div>
            } />
          )}
          {authed && (
            <Route path="/on-demand/manage" element={
              <div style={{ display: 'grid', gap: '0.75rem' }}>
                <h2>Manage On-Demand Requests</h2>
                {/* Manage toolbar */}
                <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', flexWrap: 'wrap', marginBottom: '0.5rem' }}>
                  <input
                    placeholder="Search destination or origin address..."
                    value={odSearch}
                    onChange={e => { setOdSearch(e.target.value); setOdPage(1) }}
                    style={{ flex: '1 1 260px', minWidth: 200, padding: '0.5rem', borderRadius: 6, border: '1px solid #ccc' }}
                  />
                  <label style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                    <span>Page size</span>
                    <select value={odPageSize} onChange={e => { setOdPageSize(parseInt(e.target.value)); setOdPage(1) }} style={{ padding: '0.35rem 0.5rem', borderRadius: 6, border: '1px solid #ccc', background: 'white' }}>
                      <option value={5}>5</option>
                      <option value={10}>10</option>
                      <option value={20}>20</option>
                    </select>
                  </label>
                </div>

                {/* List with pagination */}
                {(() => {
                  const q = odSearch.trim().toLowerCase()
                  const filtered = odRequests.filter(r => {
                    const addr = originAddrCache[`${r.origin_lat.toFixed(5)},${r.origin_lng.toFixed(5)}`] || ''
                    return !q || r.destination.toLowerCase().includes(q) || addr.toLowerCase().includes(q)
                  })
                  const total = filtered.length
                  const totalPages = Math.max(1, Math.ceil(total / odPageSize))
                  const page = Math.min(odPage, totalPages)
                  const start = (page - 1) * odPageSize
                  const pageItems = filtered.slice(start, start + odPageSize)
                  return (
                    <div>
                      {pageItems.length === 0 ? (
                        <div>No requests found.</div>
                      ) : (
                        <ul style={{ paddingLeft: '1rem' }}>
                          {pageItems.map((r) => {
                            const key = `${r.origin_lat.toFixed(5)},${r.origin_lng.toFixed(5)}`
                            const addr = originAddrCache[key]
                            return (
                              <li key={r.id}>
                                <strong>{new Date(r.created_at).toLocaleString()}</strong>
                                {' — To '}{r.destination}
                                {' — Origin: '}
                                {addr ? (
                                  <span>{addr}</span>
                                ) : (
                                  <a href={`https://www.google.com/maps?q=${r.origin_lat},${r.origin_lng}`} target="_blank" rel="noreferrer">{r.origin_lat.toFixed(5)},{r.origin_lng.toFixed(5)}</a>
                                )}
                                {' — Dest: '}<a href={`https://www.google.com/maps?q=${r.dest_lat},${r.dest_lng}`} target="_blank" rel="noreferrer">{r.dest_lat.toFixed(5)},{r.dest_lng.toFixed(5)}</a>
                              </li>
                            )
                          })}
                        </ul>
                      )}
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginTop: '0.5rem' }}>
                        <button type="button" disabled={page <= 1} onClick={() => setOdPage(p => Math.max(1, p - 1))} style={{ padding: '0.35rem 0.6rem', borderRadius: 6, backgroundColor: '#2563eb', color: 'white', border: 'none', cursor: page <= 1 ? 'not-allowed' : 'pointer' }}>Prev</button>
                        <span>Page {page} / {totalPages} ({total} total)</span>
                        <button type="button" disabled={page >= totalPages} onClick={() => setOdPage(p => Math.min(totalPages, p + 1))} style={{ padding: '0.35rem 0.6rem', borderRadius: 6, backgroundColor: '#2563eb', color: 'white', border: 'none', cursor: page >= totalPages ? 'not-allowed' : 'pointer' }}>Next</button>
                      </div>
                    </div>
                  )
                })()}
              </div>
            } />
          )}
          <Route path="/account" element={<MyAccount />} />
          {!authed && <Route path="/login" element={<Login />} />}
          {!authed && <Route path="/signup" element={<Signup />} />}

          <Route path="*" element={<Navigate to={authed ? (mode === 'regular' ? '/details' : '/on-demand') : '/login'} replace />} />
        </Routes>

        <footer style={{ marginTop: '2rem', fontSize: 12, color: '#666' }}>
          API base: {API_BASE}
        </footer>
      </div>
    </div>
  )
}
