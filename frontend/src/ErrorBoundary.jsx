import React from 'react';

export class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('Error caught by boundary:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: '2rem', color: '#ff4444', background: '#1a1a1a', height: '100vh' }}>
          <h2>⚠️ Something went wrong</h2>
          <pre style={{ whiteSpace: 'pre-wrap', fontSize: '0.9rem' }}>{this.state.error?.toString()}</pre>
          <button onClick={() => window.location.reload()} className="btn-primary" style={{ marginTop: '1rem' }}>
            Reload Page
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

export default ErrorBoundary;
