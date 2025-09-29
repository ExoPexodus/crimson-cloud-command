// Runtime configuration that gets loaded from window object
interface RuntimeConfig {
  keycloakUrl?: string;
  keycloakRealm?: string;
  keycloakClientId?: string;
}

// Get runtime configuration injected by the container
export function getRuntimeConfig(): RuntimeConfig {
  if (typeof window !== 'undefined') {
    return (window as any).__RUNTIME_CONFIG__ || {};
  }
  return {};
}

// Get Keycloak configuration with fallback to build-time env vars
export function getKeycloakConfig() {
  const runtimeConfig = getRuntimeConfig();
  
  return {
    url: runtimeConfig.keycloakUrl || import.meta.env.VITE_KEYCLOAK_URL,
    realm: runtimeConfig.keycloakRealm || import.meta.env.VITE_KEYCLOAK_REALM,
    clientId: runtimeConfig.keycloakClientId || import.meta.env.VITE_KEYCLOAK_CLIENT_ID,
  };
}