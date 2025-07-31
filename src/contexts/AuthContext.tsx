import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { User, LoginCredentials } from '../types';
import { setToken, getToken, removeToken, setUser, getUser, clearAuth } from '../utils/auth';
import api from '../services/api';
import socketService from '../services/socket';

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => Promise<void>;
  updateUser: (user: User) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUserState] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  
  useEffect(() => {
    // Check for existing auth on mount
    const initAuth = async () => {
      const token = getToken();
      const savedUser = getUser();
      
      if (token && savedUser) {
        setUserState(savedUser);
        
        try {
          // Verify token is still valid
          const response = await api.getProfile();
          if (response.success) {
            setUserState(response.data);
            setUser(response.data);
          } else {
            clearAuth();
          }
        } catch (error) {
          console.error('Auth verification failed:', error);
          clearAuth();
        }
      }
      
      setIsLoading(false);
    };
    
    initAuth();
  }, []);
  
  const login = async (credentials: LoginCredentials) => {
    try {
      const response = await api.login(credentials.email, credentials.password);
      
      if (response.success) {
        const { token, user } = response.data;
        
        setToken(token);
        setUser(user);
        setUserState(user);
        
        // Connect to socket after login
        socketService.connect();
      } else {
        throw new Error(response.error?.message || 'Login failed');
      }
    } catch (error: any) {
      console.error('Login error:', error);
      throw error;
    }
  };
  
  const logout = async () => {
    try {
      await api.logout();
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      clearAuth();
      setUserState(null);
      socketService.disconnect();
    }
  };
  
  const updateUser = (updatedUser: User) => {
    setUser(updatedUser);
    setUserState(updatedUser);
  };
  
  const value = {
    user,
    isLoading,
    isAuthenticated: !!user,
    login,
    logout,
    updateUser
  };
  
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};