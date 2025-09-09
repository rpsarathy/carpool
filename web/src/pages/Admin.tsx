import { useState, useEffect } from 'react'
import { API_BASE } from '../config'

interface User {
  id: number
  email: string
  profile?: {
    full_name?: string
    first_name?: string
    last_name?: string
    phone?: string
  }
  created_at?: string
}

export default function Admin() {
  const [users, setUsers] = useState<User[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [selectedUsers, setSelectedUsers] = useState<Set<number>>(new Set())

  useEffect(() => {
    fetchUsers()
  }, [])

  async function fetchUsers() {
    try {
      setLoading(true)
      setError(null)
      
      const res = await fetch(`${API_BASE}/admin/users`)
      if (!res.ok) throw new Error(`Failed to fetch users: ${res.status}`)
      
      const data = await res.json()
      setUsers(data.users || [])
    } catch (e: any) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  function toggleUserSelection(userId: number) {
    const newSelected = new Set(selectedUsers)
    if (newSelected.has(userId)) {
      newSelected.delete(userId)
    } else {
      newSelected.add(userId)
    }
    setSelectedUsers(newSelected)
  }

  function selectTestUsers() {
    const testUsers = users.filter(user => 
      user.email.includes('test') || 
      user.email.includes('webapp') ||
      user.email.includes('dummy') ||
      user.email.includes('example.com')
    )
    setSelectedUsers(new Set(testUsers.map(u => u.id)))
  }

  function selectAllUsers() {
    setSelectedUsers(new Set(users.map(u => u.id)))
  }

  function clearSelection() {
    setSelectedUsers(new Set())
  }

  async function deleteSelectedUsers() {
    if (selectedUsers.size === 0) {
      setError('No users selected')
      return
    }

    const confirmed = confirm(`Are you sure you want to delete ${selectedUsers.size} user(s)? This action cannot be undone.`)
    if (!confirmed) return

    try {
      setLoading(true)
      setError(null)
      
      const deletePromises = Array.from(selectedUsers).map(userId =>
        fetch(`${API_BASE}/admin/users/${userId}`, { method: 'DELETE' })
      )
      
      await Promise.all(deletePromises)
      
      setSuccess(`Successfully deleted ${selectedUsers.size} users`)
      setSelectedUsers(new Set())
      await fetchUsers() // Refresh the list
      
    } catch (e: any) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  async function cleanupTestUsers() {
    const confirmed = confirm('This will delete all test users (emails containing "test", "webapp", "dummy", or "example.com"). Continue?')
    if (!confirmed) return

    try {
      setLoading(true)
      setError(null)
      
      const res = await fetch(`${API_BASE}/admin/users/cleanup`, { method: 'POST' })
      if (!res.ok) throw new Error(`Cleanup failed: ${res.status}`)
      
      const data = await res.json()
      setSuccess(data.message)
      setSelectedUsers(new Set())
      await fetchUsers() // Refresh the list
      
    } catch (e: any) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ 
      minHeight: '100vh', 
      padding: '2rem', 
      backgroundColor: '#f7f7f8',
      fontFamily: 'system-ui, sans-serif'
    }}>
      <div style={{ 
        maxWidth: '1200px', 
        margin: '0 auto',
        backgroundColor: 'white',
        padding: '2rem',
        borderRadius: 12,
        boxShadow: '0 10px 30px rgba(0,0,0,0.06)'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
          <h1 style={{ margin: 0, color: '#1f2937' }}>Admin - User Management</h1>
          <button 
            onClick={fetchUsers} 
            disabled={loading}
            style={{ 
              padding: '0.75rem 1.5rem', 
              borderRadius: 8, 
              backgroundColor: '#2563eb', 
              color: 'white', 
              border: 'none', 
              cursor: loading ? 'not-allowed' : 'pointer',
              fontSize: '0.875rem',
              fontWeight: 500
            }}
          >
            {loading ? 'Refreshing...' : 'Refresh'}
          </button>
        </div>

        {error && (
          <div style={{ 
            color: '#dc2626', 
            padding: '1rem', 
            backgroundColor: '#fef2f2', 
            borderRadius: 8, 
            marginBottom: '1rem',
            border: '1px solid #fecaca'
          }}>
            {error}
          </div>
        )}

        {success && (
          <div style={{ 
            color: '#059669', 
            padding: '1rem', 
            backgroundColor: '#ecfdf5', 
            borderRadius: 8, 
            marginBottom: '1rem',
            border: '1px solid #a7f3d0'
          }}>
            {success}
          </div>
        )}

        <div style={{ 
          display: 'flex', 
          gap: '0.75rem', 
          flexWrap: 'wrap', 
          alignItems: 'center',
          marginBottom: '1.5rem',
          padding: '1rem',
          backgroundColor: '#f9fafb',
          borderRadius: 8,
          border: '1px solid #e5e7eb'
        }}>
          <span style={{ fontWeight: 600, color: '#374151' }}>Actions:</span>
          
          <button 
            onClick={selectTestUsers}
            style={{ 
              padding: '0.5rem 1rem', 
              borderRadius: 6, 
              backgroundColor: '#f59e0b', 
              color: 'white', 
              border: 'none', 
              cursor: 'pointer',
              fontSize: '0.875rem'
            }}
          >
            Select Test Users
          </button>
          
          <button 
            onClick={selectAllUsers}
            style={{ 
              padding: '0.5rem 1rem', 
              borderRadius: 6, 
              backgroundColor: '#6b7280', 
              color: 'white', 
              border: 'none', 
              cursor: 'pointer',
              fontSize: '0.875rem'
            }}
          >
            Select All
          </button>
          
          <button 
            onClick={clearSelection}
            style={{ 
              padding: '0.5rem 1rem', 
              borderRadius: 6, 
              backgroundColor: '#9ca3af', 
              color: 'white', 
              border: 'none', 
              cursor: 'pointer',
              fontSize: '0.875rem'
            }}
          >
            Clear Selection
          </button>
          
          <button 
            onClick={deleteSelectedUsers}
            disabled={selectedUsers.size === 0 || loading}
            style={{ 
              padding: '0.5rem 1rem', 
              borderRadius: 6, 
              backgroundColor: selectedUsers.size > 0 ? '#dc2626' : '#d1d5db', 
              color: 'white', 
              border: 'none', 
              cursor: selectedUsers.size > 0 && !loading ? 'pointer' : 'not-allowed',
              fontSize: '0.875rem'
            }}
          >
            Delete Selected ({selectedUsers.size})
          </button>
          
          <button 
            onClick={cleanupTestUsers}
            disabled={loading}
            style={{ 
              padding: '0.5rem 1rem', 
              borderRadius: 6, 
              backgroundColor: '#ef4444', 
              color: 'white', 
              border: 'none', 
              cursor: loading ? 'not-allowed' : 'pointer',
              fontSize: '0.875rem',
              marginLeft: 'auto'
            }}
          >
            🧹 Cleanup All Test Users
          </button>
        </div>

        <div style={{ 
          border: '1px solid #e5e7eb', 
          borderRadius: 8, 
          overflow: 'hidden',
          backgroundColor: 'white'
        }}>
          <div style={{ 
            display: 'grid', 
            gridTemplateColumns: '60px 1fr 200px 150px 120px', 
            gap: '1rem', 
            padding: '1rem', 
            backgroundColor: '#f9fafb', 
            fontWeight: 600,
            borderBottom: '1px solid #e5e7eb',
            color: '#374151'
          }}>
            <div>Select</div>
            <div>Email</div>
            <div>Name</div>
            <div>Created</div>
            <div>Type</div>
          </div>

          {loading && users.length === 0 ? (
            <div style={{ padding: '3rem', textAlign: 'center', color: '#6b7280' }}>
              Loading users...
            </div>
          ) : users.length === 0 ? (
            <div style={{ padding: '3rem', textAlign: 'center', color: '#6b7280' }}>
              No users found
            </div>
          ) : (
            users.map(user => {
              const isTestUser = user.email.includes('test') || 
                               user.email.includes('webapp') || 
                               user.email.includes('dummy') ||
                               user.email.includes('example.com')
              
              const displayName = user.profile?.full_name || 
                                [user.profile?.first_name, user.profile?.last_name].filter(Boolean).join(' ') || 
                                'No name'

              return (
                <div 
                  key={user.id}
                  style={{ 
                    display: 'grid', 
                    gridTemplateColumns: '60px 1fr 200px 150px 120px', 
                    gap: '1rem', 
                    padding: '1rem', 
                    borderBottom: '1px solid #f3f4f6',
                    backgroundColor: selectedUsers.has(user.id) ? '#eff6ff' : 'white',
                    transition: 'background-color 0.2s'
                  }}
                >
                  <div>
                    <input 
                      type="checkbox" 
                      checked={selectedUsers.has(user.id)}
                      onChange={() => toggleUserSelection(user.id)}
                      style={{ width: '16px', height: '16px' }}
                    />
                  </div>
                  <div style={{ 
                    wordBreak: 'break-all', 
                    color: '#374151',
                    fontSize: '0.875rem'
                  }}>
                    {user.email}
                  </div>
                  <div style={{ 
                    color: '#6b7280',
                    fontSize: '0.875rem'
                  }}>
                    {displayName}
                  </div>
                  <div style={{ 
                    fontSize: '0.75rem', 
                    color: '#9ca3af' 
                  }}>
                    {user.created_at ? new Date(user.created_at).toLocaleDateString() : 'Unknown'}
                  </div>
                  <div>
                    <span style={{ 
                      padding: '0.25rem 0.75rem', 
                      borderRadius: 12, 
                      fontSize: '0.75rem', 
                      fontWeight: 500,
                      backgroundColor: isTestUser ? '#fef3c7' : '#dbeafe',
                      color: isTestUser ? '#92400e' : '#1e40af'
                    }}>
                      {isTestUser ? 'Test' : 'Real'}
                    </span>
                  </div>
                </div>
              )
            })
          )}
        </div>

        <div style={{ 
          marginTop: '2rem', 
          padding: '1rem', 
          backgroundColor: '#f9fafb', 
          borderRadius: 8,
          fontSize: '0.875rem', 
          color: '#6b7280' 
        }}>
          <p style={{ margin: '0 0 0.5rem 0', fontWeight: 600 }}>Total Users: {users.length}</p>
          <p style={{ margin: 0 }}>
            Test Users: {users.filter(u => 
              u.email.includes('test') || u.email.includes('webapp') || 
              u.email.includes('dummy') || u.email.includes('example.com')
            ).length}
          </p>
        </div>
      </div>
    </div>
  )
}
