import { Button } from '@/components/ui/button';
import { useAuth } from '@/hooks/useAuth';
import { useState, useEffect } from 'react';

export function KeycloakLoginButton() {
  const { loginWithKeycloak } = useAuth();
  const [isLoading, setIsLoading] = useState(false);

  const handleKeycloakLogin = () => {
    setIsLoading(true);
    
    const keycloakConfig = {
      server: import.meta.env.VITE_KEYCLOAK_SERVER_URL || 'https://uat-auth.kocharsoft.com/auth',
      realm: import.meta.env.VITE_KEYCLOAK_REALM || 'kocharsoft',
      clientId: import.meta.env.VITE_KEYCLOAK_CLIENT_ID || 'autoscaling-frontend'
    };

    const redirectUri = `${window.location.origin}/auth/keycloak/callback`;
    
    const authUrl = `${keycloakConfig.server}/realms/${keycloakConfig.realm}/protocol/openid-connect/auth` +
      `?client_id=${keycloakConfig.clientId}` +
      `&redirect_uri=${encodeURIComponent(redirectUri)}` +
      `&response_type=code` +
      `&scope=openid profile email`;

    console.log('🔗 Redirecting to Keycloak:', authUrl);
    console.log('🔗 Redirect URI:', redirectUri);
    
    // Redirect to Keycloak
    window.location.href = authUrl;
  };

  // Check for Keycloak callback on component mount
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const code = urlParams.get('code');
    const error = urlParams.get('error');
    
    console.log('🔍 Keycloak callback check:', { 
      code: code ? 'present' : 'none', 
      error,
      pathname: window.location.pathname 
    });
    
    if (error) {
      console.error('🚨 Keycloak error:', error);
      setIsLoading(false);
      window.history.replaceState({}, document.title, '/');
      return;
    }
    
    if (code && window.location.pathname === '/auth/keycloak/callback') {
      console.log('🔄 Processing Keycloak callback...');
      setIsLoading(true);
      const redirectUri = `${window.location.origin}/auth/keycloak/callback`;
      
      console.log('📞 Calling loginWithKeycloak with:', { code: code.slice(0, 10) + '...', redirectUri });
      
      loginWithKeycloak(code, redirectUri).then((success) => {
        console.log('✅ Keycloak login result:', success);
        if (success) {
          // Clear URL parameters and redirect to app
          window.history.replaceState({}, document.title, '/');
          window.location.href = '/'; // Force a full redirect to ensure auth state updates
        } else {
          console.error('❌ Keycloak login failed');
          setIsLoading(false);
          window.history.replaceState({}, document.title, '/');
        }
      }).catch((error) => {
        console.error('❌ Keycloak login error:', error);
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