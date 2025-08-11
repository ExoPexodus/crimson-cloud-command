
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

  const logout = () => {
    apiClient.logout();
    setIsAuthenticated(false);
    setUser(null);
    localStorage.removeItem('user_data');
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
