import { create } from 'zustand';

interface UIState {
  isBetaModalOpen: boolean;
  openBetaModal: () => void;
  closeBetaModal: () => void;
}

export const useUIStore = create<UIState>((set) => ({
  isBetaModalOpen: false,
  openBetaModal: () => set({ isBetaModalOpen: true }),
  closeBetaModal: () => set({ isBetaModalOpen: false }),
}));
