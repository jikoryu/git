import { create } from 'zustand';
import { User } from '../types';
import { tokenStorage } from '../services/auth';

interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;

  setTokens: (access: string, refresh: string) => void;
  setUser: (user: User) => void;
  logout: () => void;
  initialize: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  accessToken: null,
  refreshToken: null,
  isLoading: true,
  isAuthenticated: false,

  setTokens: async (access, refresh) => {
    await tokenStorage.saveAccessToken(access);
    await tokenStorage.saveRefreshToken(refresh);
    set({ accessToken: access, refreshToken: refresh, isAuthenticated: true });
  },

  setUser: (user) => set({ user }),

  logout: async () => {
    await tokenStorage.clear();
    set({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
    });
  },

  initialize: async () => {
    try {
      const [access, refresh] = await Promise.all([
        tokenStorage.getAccessToken(),
        tokenStorage.getRefreshToken(),
      ]);
      if (access && refresh) {
        set({
          accessToken: access,
          refreshToken: refresh,
          isAuthenticated: true,
        });
        // The _layout auth gate will validate the token by calling /auth/me
      }
    } catch {
      // Tokens not found or error — stay logged out
    } finally {
      set({ isLoading: false });
    }
  },
}));
