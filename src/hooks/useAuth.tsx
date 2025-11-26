import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { apiClient } from '@/lib/api';

interface User {
  id: number;
  email: string;
  full_name: string;
  role: 'USER' | 'DEVOPS' | 'ADMIN';
  auth_provider: 'local' | 'keycloak';
  keycloak_user_id?: string;
  is_active: boolean;
  created_at: string;
}

interface AuthContextType {
  isAuthenticated: boolean;
  user: User | null;
  login: (email: string, password: string) => Promise<boolean>;
  loginWithKeycloak: (code: string, redirectUri: string) => Promise<boolean>;
  logout: () => void;
  loading: boolean;
  hasRole: (role: 'USER' | 'DEVOPS' | 'ADMIN') => boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check if user is already logged in
    const token = localStorage.getItem('access_token');
    const userData = localStorage.getItem('user_data');
    
    if (token && userData) {
      try {
        const parsedUser = JSON.parse(userData);
        setUser(parsedUser);
        setIsAuthenticated(true);
      } catch (error) {
        console.error('Failed to parse user data:', error);
        localStorage.removeItem('access_token');
        localStorage.removeItem('user_data');
      }
    }
    setLoading(false);
  }, []);

  const login = async (email: string, password: string): Promise<boolean> => {
    try {
      const result = await apiClient.login(email, password);
      if (result.data) {
        setIsAuthenticated(true);
        setUser(result.data.user);
        localStorage.setItem('user_data', JSON.stringify(result.data.user));
        return true;
      }
      return false;
    } catch (error) {
      console.error('Login failed:', error);
      return false;
    }
  };

  const loginWithKeycloak = async (code: string, redirectUri: string): Promise<boolean> => {
    try {
      const result = await apiClient.loginWithKeycloak(code, redirectUri);
      if (result.data) {
        console.group('🔐 Keycloak Login Success');
        console.log('User Data:', result.data.user);
        console.log('Access Token:', result.data.access_token);
        if ((result.data as any).keycloak_data) console.log('Keycloak Data:', (result.data as any).keycloak_data);
        if ((result.data as any).roles) console.log('Keycloak Roles:', (result.data as any).roles);
        if ((result.data as any).groups) console.log('Keycloak Groups:', (result.data as any).groups);
        if ((result.data as any).token_data) console.log('Token Data:', (result.data as any).token_data);
        console.log('Full Response:', result.data);
        console.groupEnd();
        
        setIsAuthenticated(true);
        setUser(result.data.user);
        localStorage.setItem('user_data', JSON.stringify(result.data.user));
        return true;
      }
      return false;
    } catch (error) {
      console.error('Keycloak login failed:', error);
      return false;
    }
  };

  const logout = () => {
    apiClient.logout();
    setIsAuthenticated(false);
    setUser(null);
    localStorage.removeItem('user_data');
  };

  const hasRole = (role: 'USER' | 'DEVOPS' | 'ADMIN'): boolean => {
    if (!user) return false;
    
    const roleHierarchy = { USER: 1, DEVOPS: 2, ADMIN: 3 } as const;
    const userLevel = roleHierarchy[user.role] || 0;
    const requiredLevel = roleHierarchy[role] || 0;
    
    return userLevel >= requiredLevel;
  };

  return (
    <AuthContext.Provider value={{ 
      isAuthenticated, 
      user, 
      login, 
      loginWithKeycloak, 
      logout, 
      loading, 
      hasRole 
    }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
