import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import { type UserRead, OpenAPI } from '../generated/api';

interface AuthState {
  token: string | null;
  user: UserRead | null;
  setToken: (token: string | null, user: UserRead | null) => void;
  clearToken: () => void;
  _hasHydrated: boolean;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      _hasHydrated: false, 
      setToken: (token, user) => {
        OpenAPI.TOKEN = token ?? undefined; 
        set({ token, user });
      },
      clearToken: () => {
        OpenAPI.TOKEN = undefined;
        set({ token: null, user: null }); 
      },
    }),
    {
      name: 'auth-storage',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        token: state.token,
        user: state.user,
      }),
    }
  )
);

const storePersist = useAuthStore.persist;

async function initializeAuthAndSetToken() {
  try {
    if (storePersist && typeof storePersist.rehydrate === 'function') {
      await storePersist.rehydrate();
    }
  } catch (error) {
    // It's good practice to at least log critical errors in production if they affect core functionality
    // For now, as per request, removing all logs. Consider adding a more robust error handling/logging strategy for production.
  } finally {
    const currentState = useAuthStore.getState();
    if (currentState.token) {
      OpenAPI.TOKEN = currentState.token ?? undefined;
    } else {
      OpenAPI.TOKEN = undefined;
    }
    useAuthStore.setState({ _hasHydrated: true });
  }
}

if (storePersist) {
  initializeAuthAndSetToken();
} else {
  useAuthStore.setState({ _hasHydrated: true }); 
}
