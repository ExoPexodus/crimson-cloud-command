import { Button } from '@/components/ui/button';
import { useAuth } from '@/hooks/useAuth';
import { useState, useEffect } from 'react';

export function KeycloakLoginButton() {
  const { loginWithKeycloak } = useAuth();
  const [isLoading, setIsLoading] = useState(false);

  const handleKeycloakLogin = () => {
    setIsLoading(true);
    
    // Get Keycloak configuration from environment
    const keycloakUrl = import.meta.env.VITE_KEYCLOAK_URL;
    const realm = import.meta.env.VITE_KEYCLOAK_REALM;
    const clientId = import.meta.env.VITE_KEYCLOAK_CLIENT_ID;
    
    if (!keycloakUrl || !realm || !clientId) {
      console.error('Keycloak configuration missing');
      setIsLoading(false);
      return;
    }
    
    // Construct redirect URI
    const redirectUri = `${window.location.origin}/auth/keycloak/callback`;
    
    // Construct Keycloak authorization URL
    const authUrl = new URL(`${keycloakUrl}/realms/${realm}/protocol/openid-connect/auth`);
    authUrl.searchParams.set('client_id', clientId);
    authUrl.searchParams.set('redirect_uri', redirectUri);
    authUrl.searchParams.set('response_type', 'code');
    authUrl.searchParams.set('scope', 'openid profile email');
    
    // Redirect to Keycloak
    window.location.href = authUrl.toString();
  };

  // Check for Keycloak callback on component mount
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const code = urlParams.get('code');
    
    if (code && window.location.pathname === '/auth/keycloak/callback') {
      setIsLoading(true);
      const redirectUri = `${window.location.origin}/auth/keycloak/callback`;
      
      loginWithKeycloak(code, redirectUri).then((success) => {
        if (success) {
          // Clear URL parameters and redirect to app
          window.history.replaceState({}, document.title, '/');
          window.location.href = '/'; // Force a full redirect to ensure auth state updates
        } else {
          console.error('Keycloak login failed');
          setIsLoading(false);
          window.history.replaceState({}, document.title, '/');
        }
      }).catch((error) => {
        console.error('Keycloak login error:', error);
        setIsLoading(false);
        window.history.replaceState({}, document.title, '/');
      });
    }
  }, [loginWithKeycloak]);

  return (
    <Button 
      onClick={handleKeycloakLogin} 
      disabled={isLoading}
      variant="outline"
      className="w-full"
    >
      {isLoading ? 'Redirecting...' : 'Login with Keycloak'}
    </Button>
  );
}