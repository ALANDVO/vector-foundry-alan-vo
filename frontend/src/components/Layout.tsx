// Vector Foundry - Layout Component
import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

export function Layout() {
  const { user, logout, isAuthenticated } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const navigation = [
    { path: '/', label: 'Dashboard', icon: '📊' },
    { path: '/compare', label: 'Compare', icon: '⚖️' },
  ];

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <header style={{
        background: '#ffffff',
        borderBottom: '1px solid #e2e8f0',
        position: 'sticky',
        top: 0,
        zIndex: 100,
      }}>
        <div className="container" style={{ height: '64px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <NavLink to="/" style={{
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
              fontSize: '20px',
              fontWeight: '700',
              color: '#1e293b',
              textDecoration: 'none',
            }}>
              <span style={{
                width: '36px',
                height: '36px',
                borderRadius: '10px',
                background: 'linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'white',
                fontSize: '18px',
              }}>
                ⟲
              </span>
              Vector Foundry
            </NavLink>
          </div>

          <nav style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            {navigation.map((item) => (
              <NavLink
                key={item.path}
                to={item.path}
                style={({ isActive }) => ({
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '10px 16px',
                  borderRadius: '8px',
                  fontWeight: 500,
                  fontSize: '14px',
                  color: isActive ? '#2563eb' : '#475569',
                  background: isActive ? '#dbeafe' : 'transparent',
                  textDecoration: 'none',
                  transition: 'all 0.15s ease',
                })}
                end={item.path === '/'}
              >
                <span aria-hidden="true">{item.icon}</span>
                {item.label}
              </NavLink>
            ))}

            {isAuthenticated && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginLeft: '16px', paddingLeft: '16px', borderLeft: '1px solid #e2e8f0' }}>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: '13px', fontWeight: '600', color: '#1e293b' }}>
                    {user?.name || user?.username}
                  </div>
                  <div style={{ fontSize: '11px', color: '#64748b', textTransform: 'capitalize' }}>
                    {user?.roles?.join(', ') || 'viewer'}
                  </div>
                </div>
                <button
                  onClick={handleLogout}
                  className="btn btn-ghost"
                  style={{ padding: '8px 12px', fontSize: '13px' }}
                >
                  Logout
                </button>
              </div>
            )}
          </nav>
        </div>
      </header>

      <main style={{ flex: 1, padding: '24px 0' }}>
        <div className="container">
          <Outlet />
        </div>
      </main>

      <footer style={{
        background: '#ffffff',
        borderTop: '1px solid #e2e8f0',
        padding: '16px 0',
        marginTop: 'auto',
      }}>
        <div className="container" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '12px', color: '#94a3b8' }}>
          <span>Vector Foundry &mdash; Rust compiler feature stabilization tracking</span>
          <span>Alan Vo | AI & Machine Learning</span>
        </div>
      </footer>
    </div>
  );
}