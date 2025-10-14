/**
 * Runtime configuration service
 * Reads configuration from window.RUNTIME_CONFIG (injected at container startup)
 * Falls back to import.meta.env for development
 */

interface RuntimeConfig {
  KEYCLOAK_URL?: string;
  KEYCLOAK_REALM?: string;
  KEYCLOAK_CLIENT_ID?: string;
  API_BASE_URL?: string;
}

declare global {
  interface Window {
    RUNTIME_CONFIG?: RuntimeConfig;
  }
}

export const runtimeConfig = {
  getKeycloakUrl(): string | undefined {
    return window.RUNTIME_CONFIG?.KEYCLOAK_URL || import.meta.env.VITE_KEYCLOAK_URL;
  },

  getKeycloakRealm(): string | undefined {
    return window.RUNTIME_CONFIG?.KEYCLOAK_REALM || import.meta.env.VITE_KEYCLOAK_REALM;
  },

  getKeycloakClientId(): string | undefined {
    return window.RUNTIME_CONFIG?.KEYCLOAK_CLIENT_ID || import.meta.env.VITE_KEYCLOAK_CLIENT_ID;
  },

  getApiBaseUrl(): string | undefined {
    return window.RUNTIME_CONFIG?.API_BASE_URL || import.meta.env.VITE_API_BASE_URL;
  }
};
