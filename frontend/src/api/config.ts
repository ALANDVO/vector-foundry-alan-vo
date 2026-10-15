// Vector Foundry - API Configuration
export const API_CONFIG = {
  baseUrl: import.meta.env.VITE_API_BASE_URL || '',
  timeout: 30000,
};

export const AUTH_CONFIG = {
  keycloakUrl: import.meta.env.VITE_KEYCLOAK_URL || 'http://localhost:8080',
  realm: import.meta.env.VITE_KEYCLOAK_REALM || 'vector-foundry',
  clientId: import.meta.env.VITE_KEYCLOAK_CLIENT_ID || 'vector-foundry-frontend',
};