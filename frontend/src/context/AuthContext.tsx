import React, { createContext, useContext, useState, useEffect } from 'react';
import { User } from '../types';
import { apiService } from '../services/api';

interface AuthContextType {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  login: (email: string, pass: string) => Promise<void>;
  register: (data: any) => Promise<void>;
  logout: () => void;
  switchDemoAccount: (role: 'admin' | 'moderator' | 'creator' | 'viewer') => Promise<void>;
  isAuthModalOpen: boolean;
  openAuthModal: () => void;
  closeAuthModal: () => void;
  isUploadModalOpen: boolean;
  openUploadModal: () => void;
  closeUploadModal: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(localStorage.getItem('yt_token'));
  const [isLoading, setIsLoading] = useState(true);
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);

  useEffect(() => {
    const fetchUser = async () => {
      if (token) {
        try {
          const userData = await apiService.getMe();
          setUser(userData);
        } catch (e) {
          console.error("Auth check failed:", e);
          localStorage.removeItem('yt_token');
          setToken(null);
          setUser(null);
        }
      }
      setIsLoading(false);
    };
    fetchUser();
  }, [token]);

  const login = async (email: string, pass: string) => {
    const data = await apiService.login(email, pass);
    localStorage.setItem('yt_token', data.access_token);
    setToken(data.access_token);
    setUser(data.user);
    setIsAuthModalOpen(false);
  };

  const register = async (regData: any) => {
    const data = await apiService.register(regData);
    localStorage.setItem('yt_token', data.access_token);
    setToken(data.access_token);
    setUser(data.user);
    setIsAuthModalOpen(false);
  };

  const logout = () => {
    localStorage.removeItem('yt_token');
    setToken(null);
    setUser(null);
  };

  const switchDemoAccount = async (role: 'admin' | 'moderator' | 'creator' | 'viewer') => {
    const credentials = {
      admin: { email: 'admin@youtube.local', pass: 'AdminPass123!' },
      moderator: { email: 'moderator@youtube.local', pass: 'ModPass123!' },
      creator: { email: 'creator@youtube.local', pass: 'CreatorPass123!' },
      viewer: { email: 'viewer@youtube.local', pass: 'ViewerPass123!' },
    };
    const creds = credentials[role];
    await login(creds.email, creds.pass);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isLoading,
        login,
        register,
        logout,
        switchDemoAccount,
        isAuthModalOpen,
        openAuthModal: () => setIsAuthModalOpen(true),
        closeAuthModal: () => setIsAuthModalOpen(false),
        isUploadModalOpen,
        openUploadModal: () => {
          if (!user) {
            setIsAuthModalOpen(true);
          } else {
            setIsUploadModalOpen(true);
          }
        },
        closeUploadModal: () => setIsUploadModalOpen(false),
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
