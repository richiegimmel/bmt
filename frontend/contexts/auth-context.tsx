'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { authAPI } from '@/lib/api/auth';
import type { User, LoginRequest, RegisterRequest, AuthContextType } from '@/types/auth';

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const TOKEN_KEY = 'access_token';
const REFRESH_TOKEN_KEY = 'refresh_token';

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  // Load user on mount
  useEffect(() => {
    loadUser();
  }, []);

  const loadUser = async () => {
    try {
      const token = localStorage.getItem(TOKEN_KEY);
      if (token) {
        const userData = await authAPI.getCurrentUser(token);
        setUser(userData);
      }
    } catch (error) {
      console.error('Failed to load user:', error);
      // Token might be expired, try to refresh
      await refreshToken();
    } finally {
      setLoading(false);
    }
  };

  const login = async (credentials: LoginRequest) => {
    try {
      const response = await authAPI.login(credentials);
      localStorage.setItem(TOKEN_KEY, response.access_token);
      localStorage.setItem(REFRESH_TOKEN_KEY, response.refresh_token);

      const userData = await authAPI.getCurrentUser(response.access_token);
      setUser(userData);

      router.push('/dashboard');
    } catch (error) {
      console.error('Login failed:', error);
      throw error;
    }
  };

  const register = async (data: RegisterRequest) => {
    try {
      await authAPI.register(data);
      // Auto-login after registration
      await login({
        username: data.username,
        password: data.password,
      });
    } catch (error) {
      console.error('Registration failed:', error);
      throw error;
    }
  };

  const logout = async () => {
    try {
      const token = localStorage.getItem(TOKEN_KEY);
      if (token) {
        await authAPI.logout(token);
      }
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      localStorage.removeItem(TOKEN_KEY);
      localStorage.removeItem(REFRESH_TOKEN_KEY);
      setUser(null);
      router.push('/login');
    }
  };

  const refreshToken = async () => {
    try {
      const refresh = localStorage.getItem(REFRESH_TOKEN_KEY);
      if (!refresh) {
        throw new Error('No refresh token');
      }

      const response = await authAPI.refreshToken(refresh);
      localStorage.setItem(TOKEN_KEY, response.access_token);
      localStorage.setItem(REFRESH_TOKEN_KEY, response.refresh_token);

      const userData = await authAPI.getCurrentUser(response.access_token);
      setUser(userData);
    } catch (error) {
      console.error('Token refresh failed:', error);
      logout();
    }
  };

  const getToken = () => {
    return localStorage.getItem(TOKEN_KEY);
  };

  const value: AuthContextType = {
    user,
    loading,
    login,
    register,
    logout,
    refreshToken,
    getToken,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
