import { useEffect } from 'react';
import { Slot } from 'expo-router';
import { useAuthStore } from './src/store/authStore';

export default function Root() {
  const initialize = useAuthStore((s) => s.initialize);
  const isLoading = useAuthStore((s) => s.isLoading);

  useEffect(() => {
    initialize();
  }, []);

  if (isLoading) return null;

  return <Slot />;
}
