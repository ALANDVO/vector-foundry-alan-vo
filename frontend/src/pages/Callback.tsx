// Vector Foundry - OAuth Callback Page
// Handles the OIDC callback from Keycloak, stores tokens, and redirects to dashboard.

import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiClient } from '../api/client';

export function Callback() {
  const navigate = useNavigate();

  useEffect(() => {
    const handleCallback = async () => {
      // Extract tokens from URL fragment
      const fragment = window.location.hash.substring(1);
      const params = new URLSearchParams(fragment);
      
      const accessToken = params.get('access_token');
      const refreshToken = params.get('refresh_token');
      const idToken = params.get('id_token');
      const expiresIn = params.get('expires_in');
      
      if (!accessToken) {
        // No token in fragment, redirect to login
        navigate('/login');
        return;
      }
      
      const expiresAt = Date.now() + (parseInt(expiresIn || '300', 10) * 1000);
      
      // Store tokens and user info
      const tokenData = {
        accessToken,
        refreshToken: refreshToken || undefined,
        idToken: idToken || undefined,
        expiresAt,
      };
      
      sessionStorage.setItem('vector-foundry-tokens', JSON.stringify(tokenData));
      apiClient.setAccessToken(accessToken);
      
      // Fetch user info
      try {
        const userData = await apiClient.get<{ id: string; username: string; email: string; roles: string[] }>('/auth/me');
        const user = {
          id: userData.id,
          username: userData.username,
          email: userData.email,
          roles: userData.roles,
        };
        sessionStorage.setItem('vector-foundry-auth', JSON.stringify(user));
      } catch {
        // If user fetch fails, clear tokens and redirect to login
        sessionStorage.removeItem('vector-foundry-tokens');
        sessionStorage.removeItem('vector-foundry-auth');
        apiClient.setAccessToken(null);
        navigate('/login');
        return;
      }
      
      // Redirect to dashboard (or stored redirect)
      navigate('/');
    };
    
    handleCallback();
  }, [navigate]);

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%)'
    }}>
      <div className="card" style={{ textAlign: 'center', padding: '48px' }}>
        <div className="spinner" style={{ width: '40px', height: '40px', margin: '0 auto 24px' }} aria-hidden="true"></div>
        <p style={{ color: '#64748b', fontSize: '15px' }}>Completing sign in...</p>
      </div>
    </div>
  );
}