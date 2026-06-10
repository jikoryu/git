import { useEffect, useState } from 'react';
import { Stack, useRouter, useSegments } from 'expo-router';
import { useAuthStore } from '../src/store/authStore';
import { authApi } from '../src/services/api';

/**
 * Root layout with authentication gate.
 * - On mount, validates stored tokens by calling GET /auth/me.
 * - Redirects unauthenticated users to the index (login) screen.
 * - Protects all screens except the login flow.
 */
export default function RootLayout() {
  const { isAuthenticated, accessToken, setUser, logout } = useAuthStore();
  const [isReady, setIsReady] = useState(false);
  const router = useRouter();
  const segments = useSegments();

  // Validate stored token on mount
  useEffect(() => {
    const validate = async () => {
      if (isAuthenticated && accessToken) {
        try {
          const { data } = await authApi.getMe();
          setUser(data);
        } catch {
          // Token invalid or expired — clear auth state
          logout();
        }
      }
      setIsReady(true);
    };
    validate();
  }, []);

  // Redirect logic: protect all screens except index (login screen is index)
  useEffect(() => {
    if (!isReady) return;

    const inProtectedRoute = segments.length > 0 && segments[0] !== 'index';

    if (!isAuthenticated && inProtectedRoute) {
      router.replace('/');
    }
  }, [isAuthenticated, isReady, segments]);

  if (!isReady) return null;

  return (
    <Stack screenOptions={{ headerShown: false }}>
      <Stack.Screen name="index" options={{ title: 'Price Tracker' }} />
      <Stack.Screen name="product/[id]" options={{ title: '商品详情', headerShown: true }} />
      <Stack.Screen name="watchlist" options={{ title: '我的关注' }} />
      <Stack.Screen name="alerts" options={{ title: '降价提醒' }} />
      <Stack.Screen name="profile" options={{ title: '个人中心' }} />
    </Stack>
  );
}
