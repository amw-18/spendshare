import { create } from 'zustand';
import { UserRead } from '../generated/api';

interface AuthState {
  token: string | null;
  user: UserRead | null;
  setToken: (token: string, user: UserRead) => void;
  clearToken: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  token: null,
  user: null,
  setToken: (token, user) => set({ token, user }),
  clearToken: () => set({ token: null, user: null }),
}));
