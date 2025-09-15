
import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { apiClient } from '@/lib/api';

interface User {
  id: number;
  email: string;
  full_name: string;
  role: 'user' | 'devops' | 'admin';
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
  register: (email: string, password: string, fullName: string) => Promise<boolean>;
  logout: () => void;
  loading: boolean;
  hasRole: (role: 'user' | 'devops' | 'admin') => boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const logout = () => {
    setIsAuthenticated(false);
    setUser(null);
    localStorage.removeItem('access_token');
    localStorage.removeItem('user_data');
    apiClient.setToken(null);
  };

  useEffect(() => {
    // Set up the logout callback for the API client
    apiClient.setLogoutCallback(logout);
    
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
        // Log all Keycloak data to browser console
        console.group('🔐 Keycloak Login Success');
        console.log('User Data:', result.data.user);
        console.log('Access Token:', result.data.access_token);
        
        // Log any additional Keycloak-specific data if present
        if ((result.data as any).keycloak_data) {
          console.log('Keycloak Data:', (result.data as any).keycloak_data);
        }
        if ((result.data as any).roles) {
          console.log('Keycloak Roles:', (result.data as any).roles);
        }
        if ((result.data as any).groups) {
          console.log('Keycloak Groups:', (result.data as any).groups);
        }
        if ((result.data as any).token_data) {
          console.log('Token Data:', (result.data as any).token_data);
        }
        
        // Log the entire response for debugging
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

  const register = async (email: string, password: string, fullName: string): Promise<boolean> => {
    try {
      const result = await apiClient.register(email, password, fullName);
      if (result.data) {
        // Auto-login after registration
        return await login(email, password);
      }
      return false;
    } catch (error) {
      console.error('Registration failed:', error);
      return false;
    }
  };

  const hasRole = (role: 'user' | 'devops' | 'admin'): boolean => {
    if (!user) return false;
    
    const roleHierarchy = { user: 1, devops: 2, admin: 3 };
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
      register, 
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
