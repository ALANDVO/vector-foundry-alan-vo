// Vector Foundry - Login Component
import { useAuth } from '../contexts/AuthContext';

export function Login() {
  const { login, loading } = useAuth();

  const handleLogin = () => {
    login();
  };

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '24px',
      background: 'linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%)'
    }}>
      <div className="card" style={{ width: '100%', maxWidth: '400px' }}>
        <div style={{ textAlign: 'center', marginBottom: '32px' }}>
          <h1 style={{ fontSize: '28px', fontWeight: '700', color: '#1e293b', marginBottom: '8px' }}>
            Vector Foundry
          </h1>
          <p style={{ color: '#64748b', fontSize: '15px' }}>
            Rust compiler feature stabilization tracking
          </p>
        </div>

        <div style={{ marginBottom: '24px', padding: '16px', background: '#f1f5f9', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
          <h3 style={{ fontSize: '13px', fontWeight: '600', color: '#475569', marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Demo Mode
          </h3>
          <p style={{ fontSize: '13px', color: '#64748b', lineHeight: '1.5' }}>
            This application uses Keycloak for authentication. In demo mode, you will be redirected to a local Keycloak instance.
          </p>
        </div>

        <button
          onClick={handleLogin}
          disabled={loading}
          className="btn btn-primary"
          style={{ width: '100%', padding: '14px' }}
          aria-busy={loading}
        >
          {loading ? (
            <>
              <span className="spinner" style={{ width: '20px', height: '20px' }} aria-hidden="true"></span>
              <span>Connecting...</span>
            </>
          ) : (
            'Sign in with Keycloak'
          )}
        </button>

        <footer style={{ marginTop: '32px', textAlign: 'center', fontSize: '12px', color: '#94a3b8' }}>
          <p>Alan Vo &mdash; AI & Machine Learning</p>
          <p><a href="mailto:alanvo@gmail.com" style={{ color: '#64748b' }}>alanvo@gmail.com</a></p>
        </footer>
      </div>
    </div>
  );
}