import { Button } from '@/components/ui/button';
import { useAuth } from '@/hooks/useAuth';
import { useEffect, useState } from 'react';
import { apiClient } from '@/lib/api';
import { runtimeConfig } from '@/lib/runtimeConfig';

interface KCConfig {
  keycloak_enabled: boolean;
  keycloak_url: string;
  keycloak_realm: string;
  keycloak_client_id: string;
}

export function KeycloakLoginButton() {
  const { loginWithKeycloak } = useAuth();
  const [isLoading, setIsLoading] = useState(false);
  const [kcConfig, setKcConfig] = useState<KCConfig | null>(null);
  const [configError, setConfigError] = useState<string | null>(null);

  // Load runtime config on mount
  useEffect(() => {
    console.group('🔧 Keycloak Runtime Config');
    apiClient.getPublicConfig()
      .then((res) => {
        if (res.data) {
          console.log('✅ Loaded public config from backend:', res.data);
          setKcConfig(res.data);
          if (!res.data.keycloak_enabled) {
            console.warn('⚠️ Keycloak is not enabled by backend config. Button will be disabled.');
          }
        } else {
          console.error('❌ Failed to load public config:', res.error);
          setConfigError(res.error || 'Failed to load runtime config');
        }
      })
      .catch((err) => {
        console.error('❌ Error fetching public config:', err);
        setConfigError(err instanceof Error ? err.message : 'Unknown error');
      })
      .finally(() => console.groupEnd());
  }, []);

  const handleKeycloakLogin = async () => {
    setIsLoading(true);
    console.group('🔐 Keycloak Login');

    try {
      // Priority: API config > Runtime config > Build-time env (dev only)
      const cfg = kcConfig;
      const keycloakUrl = cfg?.keycloak_url || runtimeConfig.getKeycloakUrl();
      const realm = cfg?.keycloak_realm || runtimeConfig.getKeycloakRealm();
      const clientId = cfg?.keycloak_client_id || runtimeConfig.getKeycloakClientId();

      console.log('⚙️ Using Keycloak settings:', { keycloakUrl, realm, clientId, fromRuntime: !!cfg });

      if (!keycloakUrl || !realm || !clientId) {
        console.error('❌ Missing Keycloak configuration. Ensure backend /config provides values or VITE_* envs are set.');
        setIsLoading(false);
        return;
      }

      const redirectUri = `${window.location.origin}/auth/keycloak/callback`;
      console.log('↩️ Redirect URI:', redirectUri);

      const authUrl = new URL(`${keycloakUrl.replace(/\/$/, '')}/realms/${realm}/protocol/openid-connect/auth`);
      authUrl.searchParams.set('client_id', clientId);
      authUrl.searchParams.set('redirect_uri', redirectUri);
      authUrl.searchParams.set('response_type', 'code');
      authUrl.searchParams.set('scope', 'openid profile email');

      const finalUrl = authUrl.toString();
      console.log('➡️ Redirecting to Keycloak:', finalUrl);
      window.location.href = finalUrl;
    } catch (e) {
      console.error('❌ Unexpected error during Keycloak login:', e);
      setIsLoading(false);
    } finally {
      console.groupEnd();
    }
  };

  // Handle Keycloak callback
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const code = urlParams.get('code');

    if (code && window.location.pathname === '/auth/keycloak/callback') {
      const redirectUri = `${window.location.origin}/auth/keycloak/callback`;
      console.group('🔄 Keycloak Callback');
      console.log('📥 Received authorization code');

      loginWithKeycloak(code, redirectUri).then((success) => {
        if (success) {
          console.log('✅ Keycloak login successful, redirecting to /');
          window.history.replaceState({}, document.title, '/');
        } else {
          console.error('❌ Keycloak login failed');
          window.history.replaceState({}, document.title, '/');
        }
        console.groupEnd();
      }).catch((err) => {
        console.error('❌ Error handling Keycloak callback:', err);
        console.groupEnd();
        window.history.replaceState({}, document.title, '/');
      });
    }
  }, [loginWithKeycloak]);

  const disabled = isLoading || (kcConfig && !kcConfig.keycloak_enabled);
  const title = configError
    ? `Config error: ${configError}`
    : (kcConfig && !kcConfig.keycloak_enabled ? 'Keycloak is not enabled in backend config' : undefined);

  return (
    <Button 
      onClick={handleKeycloakLogin} 
      disabled={disabled}
      variant="outline"
      className="w-full"
      title={title}
    >
      {isLoading ? 'Redirecting...' : 'Login with Keycloak'}
    </Button>
  );
}