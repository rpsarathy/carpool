import { Component, type ErrorInfo, type ReactNode } from 'react'

interface Props {
  children: ReactNode
  fallback?: ReactNode
}

interface State {
  hasError: boolean
  error?: Error
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false
  }

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo)
  }

  public render() {
    if (this.state.hasError) {
      return this.props.fallback || (
        <div style={{ 
          padding: '2rem', 
          textAlign: 'center', 
          background: '#fff3cd', 
          border: '1px solid #ffeaa7', 
          borderRadius: 8,
          margin: '1rem'
        }}>
          <h2 style={{ color: '#856404', marginBottom: '1rem' }}>Something went wrong</h2>
          <p style={{ color: '#856404', marginBottom: '1rem' }}>
            The application encountered an error. Please refresh the page to try again.
          </p>
          <button 
            onClick={() => window.location.reload()} 
            style={{ 
              padding: '0.5rem 1rem', 
              backgroundColor: '#007bff', 
              color: 'white', 
              border: 'none', 
              borderRadius: 4, 
              cursor: 'pointer' 
            }}
          >
            Refresh Page
          </button>
          {this.state.error && (
            <details style={{ marginTop: '1rem', textAlign: 'left' }}>
              <summary style={{ cursor: 'pointer', color: '#856404' }}>Error Details</summary>
              <pre style={{ 
                background: '#f8f9fa', 
                padding: '1rem', 
                borderRadius: 4, 
                overflow: 'auto',
                fontSize: '0.875rem',
                color: '#495057'
              }}>
                {this.state.error.stack}
              </pre>
            </details>
          )}
        </div>
      )
    }

    return this.props.children
  }
}
