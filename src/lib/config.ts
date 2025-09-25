// Runtime configuration helper
declare global {
  interface Window {
    ENV?: {
      VITE_API_BASE_URL?: string;
      VITE_KEYCLOAK_URL?: string;
      VITE_KEYCLOAK_REALM?: string;
      VITE_KEYCLOAK_CLIENT_ID?: string;
    };
  }
}

export const getEnvVar = (key: string): string | undefined => {
  // In development, use Vite's env vars
  if (import.meta.env.DEV) {
    return import.meta.env[key];
  }
  
  // In production, use runtime env vars from window.ENV
  const envKey = key.replace('VITE_', '');
  return window.ENV?.[key as keyof typeof window.ENV];
};

export const config = {
  get apiBaseUrl() {
    return getEnvVar('VITE_API_BASE_URL') || 'http://localhost:8000';
  },
  get keycloakUrl() {
    return getEnvVar('VITE_KEYCLOAK_URL');
  },
  get keycloakRealm() {
    return getEnvVar('VITE_KEYCLOAK_REALM');
  },
  get keycloakClientId() {
    return getEnvVar('VITE_KEYCLOAK_CLIENT_ID');
  }
};