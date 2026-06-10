import { create } from 'zustand';
import { WatchlistItem } from '../types';
import { watchlistApi } from '../services/api';

interface WatchlistState {
  items: WatchlistItem[];
  isLoading: boolean;
  error: string | null;

  fetch: () => Promise<void>;
  add: (productId: string, targetPrice?: number) => Promise<void>;
  remove: (itemId: string) => Promise<void>;
}

export const useWatchlistStore = create<WatchlistState>((set, get) => ({
  items: [],
  isLoading: false,
  error: null,

  fetch: async () => {
    set({ isLoading: true, error: null });
    try {
      const { data } = await watchlistApi.getAll();
      set({ items: data, isLoading: false });
    } catch (err: any) {
      set({
        error: err?.response?.data?.detail || 'Failed to load watchlist',
        isLoading: false,
      });
    }
  },

  add: async (productId, targetPrice) => {
    set({ error: null });
    try {
      await watchlistApi.add(productId, targetPrice);
      // Refresh the whole list
      await get().fetch();
    } catch (err: any) {
      set({ error: err?.response?.data?.detail || 'Failed to add to watchlist' });
      throw err;
    }
  },

  remove: async (itemId) => {
    set({ error: null });
    try {
      await watchlistApi.remove(itemId);
      set({ items: get().items.filter((i) => i.id !== itemId) });
    } catch (err: any) {
      set({ error: err?.response?.data?.detail || 'Failed to remove from watchlist' });
    }
  },
}));
