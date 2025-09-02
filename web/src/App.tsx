import { useEffect, useMemo, useState } from 'react'
import { Link, Navigate, Route, Routes, useLocation } from 'react-router-dom'
import { API_BASE } from './config'
import Login from './pages/Login'
import Signup from './pages/Signup'

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
      setSchedule(savedSchedule.items)
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

  function Nav() {
    const loc = useLocation()
    const isActive = (path: string) => (loc.pathname === path ? { background: '#eef2ff', color: '#1f3a8a' } : {})
    return (
      <nav style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem' }}>
        {mode === 'regular' && (
          <>
            <Link to="/details" style={{ padding: '0.5rem 0.75rem', borderRadius: 8, border: '1px solid #ddd', textDecoration: 'none', color: '#111', ...isActive('/details') }}>
              Car Pool Details
            </Link>
            <Link to="/schedule" style={{ padding: '0.5rem 0.75rem', borderRadius: 8, border: '1px solid #ddd', textDecoration: 'none', color: '#111', ...isActive('/schedule') }}>
              Generate Car Pool Schedule
            </Link>
          </>
        )}
        <span style={{ flex: 1 }} />
        <Link to="/login" style={{ padding: '0.5rem 0.75rem', borderRadius: 8, border: '1px solid #ddd', textDecoration: 'none', color: '#111', ...isActive('/login') }}>
          Log in
        </Link>
        <Link to="/signup" style={{ padding: '0.5rem 0.75rem', borderRadius: 8, border: '1px solid #ddd', textDecoration: 'none', color: '#111', ...isActive('/signup') }}>
          Sign up
        </Link>
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

        {/* When On-Demand is selected, show placeholder and hide regular routes UI */}
        {mode === 'on_demand' ? (
          <div style={{ padding: '0.75rem', borderRadius: 8, background: '#fff7ed', border: '1px solid #fed7aa', color: '#7c2d12', marginBottom: '0.5rem' }}>
            On-Demand carpool scheduling is coming soon. For now, switch back to Regular to manage carpool details and generate a recurring schedule.
          </div>
        ) : null}

        <Routes>
          <Route path="/" element={<Navigate to={mode === 'regular' ? '/details' : '/login'} replace />} />
          {mode === 'regular' && (
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
                    <button type="button" onClick={addMemberRow} style={{ padding: '0.35rem 0.65rem', borderRadius: 6 }}>+ Add member</button>
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
                        <button type="button" onClick={() => removeMember(idx)} aria-label="Remove member" style={{ padding: '0.4rem 0.6rem', borderRadius: 6, whiteSpace: 'nowrap' }}>Remove</button>
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

                <button type="submit" disabled={loading} style={{ padding: '0.6rem 1rem', borderRadius: 6 }}>
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
                        <button type="button" onClick={() => onDeleteGroup(g.name)} style={{ padding: '0.4rem 0.6rem', borderRadius: 6 }}>Delete</button>
                      </li>
                    ))}
                  </ul>
                )}
              </form>
            } />
          )}
          {mode === 'regular' && (
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
                    style={{ padding: '0.6rem 1rem', borderRadius: 6 }}
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
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<Signup />} />

          <Route path="*" element={<Navigate to="/details" replace />} />
        </Routes>

        <footer style={{ marginTop: '2rem', fontSize: 12, color: '#666' }}>
          API base: {API_BASE}
        </footer>
      </div>
    </div>
  )
}
