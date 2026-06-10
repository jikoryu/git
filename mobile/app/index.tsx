import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  FlatList,
  ActivityIndicator,
  StyleSheet,
  KeyboardAvoidingView,
  Platform,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { useAuthStore } from '../src/store/authStore';
import { authApi, productsApi } from '../src/services/api';
import { Product } from '../src/types';
import ProductCard from '../src/components/ProductCard';
import SearchBar from '../src/components/SearchBar';

export default function HomeScreen() {
  const { isAuthenticated, setTokens, setUser } = useAuthStore();
  const router = useRouter();

  // ── Login state ──
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLogin, setIsLogin] = useState(true);
  const [authLoading, setAuthLoading] = useState(false);

  // ── Search state ──
  const [results, setResults] = useState<Product[]>([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);

  // ── Auth handlers ──
  const handleAuth = async () => {
    if (!email.trim() || !password.trim()) {
      Alert.alert('请输入邮箱和密码');
      return;
    }
    setAuthLoading(true);
    try {
      if (isLogin) {
        const { data } = await authApi.login(email.trim(), password);
        setTokens(data.access_token, data.refresh_token);
        const me = await authApi.getMe();
        setUser(me.data);
      } else {
        await authApi.register(email.trim(), password);
        // Auto-login after register
        const { data } = await authApi.login(email.trim(), password);
        setTokens(data.access_token, data.refresh_token);
        const me = await authApi.getMe();
        setUser(me.data);
      }
    } catch (err: any) {
      Alert.alert('错误', err?.response?.data?.detail || '操作失败');
    } finally {
      setAuthLoading(false);
    }
  };

  // ── Search handler ──
  const handleSearch = async (query: string, platform?: string) => {
    setSearchLoading(true);
    setHasSearched(true);
    try {
      const { data } = await productsApi.search(query, platform);
      setResults(data);
    } catch (err: any) {
      Alert.alert('搜索失败', err?.response?.data?.detail || '请重试');
    } finally {
      setSearchLoading(false);
    }
  };

  // ── Product press ──
  const handleProductPress = (product: Product) => {
    router.push(`/product/${product.id}`);
  };

  // ── Login screen ──
  if (!isAuthenticated) {
    return (
      <SafeAreaView style={styles.authContainer}>
        <KeyboardAvoidingView
          behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
          style={styles.authForm}
        >
          <Text style={styles.appTitle}>📉 Price Tracker</Text>
          <Text style={styles.appSubtitle}>商品历史价格查询 & 降价提醒</Text>

          <View style={styles.authCard}>
            <Text style={styles.authTitle}>
              {isLogin ? '登录' : '注册'}
            </Text>

            <TextInput
              style={styles.authInput}
              placeholder="邮箱"
              placeholderTextColor="#999"
              keyboardType="email-address"
              autoCapitalize="none"
              value={email}
              onChangeText={setEmail}
            />
            <TextInput
              style={styles.authInput}
              placeholder="密码"
              placeholderTextColor="#999"
              secureTextEntry
              value={password}
              onChangeText={setPassword}
            />

            <TouchableOpacity
              style={[styles.authBtn, authLoading && styles.authBtnDisabled]}
              onPress={handleAuth}
              disabled={authLoading}
            >
              {authLoading ? (
                <ActivityIndicator color="#fff" />
              ) : (
                <Text style={styles.authBtnText}>
                  {isLogin ? '登录' : '注册'}
                </Text>
              )}
            </TouchableOpacity>

            <TouchableOpacity onPress={() => setIsLogin(!isLogin)}>
              <Text style={styles.switchText}>
                {isLogin ? '没有账号？去注册' : '已有账号？去登录'}
              </Text>
            </TouchableOpacity>
          </View>
        </KeyboardAvoidingView>
      </SafeAreaView>
    );
  }

  // ── Main search screen ──
  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <SearchBar onSearch={handleSearch} isLoading={searchLoading} />

      {searchLoading ? (
        <View style={styles.centered}>
          <ActivityIndicator size="large" color="#1976D2" />
          <Text style={styles.loadingText}>搜索中...</Text>
        </View>
      ) : hasSearched && results.length === 0 ? (
        <View style={styles.centered}>
          <Text style={styles.emptyIcon}>🔍</Text>
          <Text style={styles.emptyText}>未找到相关商品</Text>
          <Text style={styles.emptySubtext}>尝试更换关键词或平台</Text>
        </View>
      ) : !hasSearched ? (
        <View style={styles.centered}>
          <Text style={styles.welcomeIcon}>🛒</Text>
          <Text style={styles.welcomeText}>
            搜索你想追踪的商品
          </Text>
          <Text style={styles.welcomeSubtext}>
            支持京东、淘宝、拼多多
          </Text>
        </View>
      ) : (
        <FlatList
          data={results}
          keyExtractor={(item) => item.id}
          renderItem={({ item }) => (
            <ProductCard product={item} onPress={handleProductPress} />
          )}
          contentContainerStyle={styles.list}
        />
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F5F5F5' },
  // Auth styles
  authContainer: { flex: 1, backgroundColor: '#F5F5F5' },
  authForm: { flex: 1, justifyContent: 'center', paddingHorizontal: 24 },
  appTitle: { fontSize: 32, fontWeight: '800', textAlign: 'center', color: '#1976D2' },
  appSubtitle: { fontSize: 14, color: '#999', textAlign: 'center', marginTop: 4, marginBottom: 32 },
  authCard: {
    backgroundColor: '#fff',
    borderRadius: 16,
    padding: 24,
    shadowColor: '#000',
    shadowOpacity: 0.06,
    shadowRadius: 12,
    elevation: 3,
  },
  authTitle: { fontSize: 22, fontWeight: '700', marginBottom: 20, color: '#222' },
  authInput: {
    height: 48,
    backgroundColor: '#F5F5F5',
    borderRadius: 10,
    paddingHorizontal: 14,
    fontSize: 15,
    color: '#333',
    marginBottom: 12,
  },
  authBtn: {
    height: 48,
    backgroundColor: '#1976D2',
    borderRadius: 10,
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: 8,
  },
  authBtnDisabled: { opacity: 0.5 },
  authBtnText: { color: '#fff', fontSize: 16, fontWeight: '600' },
  switchText: {
    color: '#1976D2',
    textAlign: 'center',
    marginTop: 16,
    fontSize: 14,
  },
  // Content styles
  centered: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 40,
  },
  loadingText: { color: '#999', marginTop: 12, fontSize: 14 },
  emptyIcon: { fontSize: 48, marginBottom: 12 },
  emptyText: { fontSize: 16, color: '#666', fontWeight: '500' },
  emptySubtext: { fontSize: 13, color: '#999', marginTop: 4 },
  welcomeIcon: { fontSize: 48, marginBottom: 12 },
  welcomeText: { fontSize: 18, color: '#333', fontWeight: '600' },
  welcomeSubtext: { fontSize: 14, color: '#999', marginTop: 4 },
  list: { paddingVertical: 8 },
});
