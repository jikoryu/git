import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  Image,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
  StyleSheet,
} from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { productsApi, watchlistApi } from '../../src/services/api';
import { Product, ProductHistory, PLATFORM_LABELS, PLATFORM_COLORS } from '../../src/types';
import PriceChart from '../../src/components/PriceChart';
import PriceBadge from '../../src/components/PriceBadge';
import AlertForm from '../../src/components/AlertForm';

export default function ProductDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();

  const [product, setProduct] = useState<Product | null>(null);
  const [history, setHistory] = useState<ProductHistory | null>(null);
  const [loading, setLoading] = useState(true);
  const [alertVisible, setAlertVisible] = useState(false);
  const [alertLoading, setAlertLoading] = useState(false);

  useEffect(() => {
    loadData();
  }, [id]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [prodRes, histRes] = await Promise.all([
        productsApi.getById(id!),
        productsApi.getHistory(id!),
      ]);
      setProduct(prodRes.data);
      setHistory(histRes.data);
    } catch (err: any) {
      Alert.alert('加载失败', err?.response?.data?.detail || '请重试');
      router.back();
    } finally {
      setLoading(false);
    }
  };

  const handleAddWatchlist = async (targetPrice?: number, notifyOnAnyDrop?: boolean) => {
    if (!product) return;
    setAlertLoading(true);
    try {
      await watchlistApi.add(product.id, targetPrice, notifyOnAnyDrop);
      setAlertVisible(false);
      Alert.alert('添加成功', '商品已添加到你的关注列表，降价时会通知你');
    } catch (err: any) {
      Alert.alert('添加失败', err?.response?.data?.detail || '请重试');
    } finally {
      setAlertLoading(false);
    }
  };

  if (loading) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color="#1976D2" />
      </View>
    );
  }

  if (!product) return null;

  const platformColor = PLATFORM_COLORS[product.platform] || '#999';
  const platformLabel = PLATFORM_LABELS[product.platform] || product.platform;

  return (
    <ScrollView style={styles.container}>
      {/* Product header */}
      <View style={styles.header}>
        <Image
          source={{
            uri: product.image_url || 'https://via.placeholder.com/200',
          }}
          style={styles.image}
          resizeMode="contain"
        />
        {/* Platform chip */}
        <View style={[styles.platformChip, { backgroundColor: platformColor }]}>
          <Text style={styles.platformChipText}>{platformLabel}</Text>
        </View>
      </View>

      {/* Product info */}
      <View style={styles.infoSection}>
        <Text style={styles.title}>{product.title}</Text>

        {product.shop_name && (
          <Text style={styles.shop}>{product.shop_name}</Text>
        )}

        <View style={styles.priceRow}>
          {product.current_price !== null && product.current_price !== undefined ? (
            <Text style={styles.price}>
              ¥{product.current_price.toFixed(2)}
            </Text>
          ) : (
            <Text style={styles.priceNA}>暂无报价</Text>
          )}
          {product.lowest_price !== null && product.lowest_price !== undefined && (
            <Text style={styles.lowest}>
              历史最低 ¥{product.lowest_price.toFixed(2)}
            </Text>
          )}
        </View>

        {product.current_price !== null && product.current_price !== undefined &&
         product.lowest_price !== null && product.lowest_price !== undefined && (
          <PriceBadge
            currentPrice={product.current_price}
            lowestPrice={product.lowest_price}
          />
        )}
      </View>

      {/* Price chart */}
      {history && history.price_history.length >= 2 ? (
        <PriceChart priceHistory={history.price_history} />
      ) : (
        <View style={styles.noChartCard}>
          <Text style={styles.noChartText}>价格数据采集中...</Text>
          <Text style={styles.noChartSubtext}>
            系统将定期更新此商品的价格
          </Text>
        </View>
      )}

      {/* Add to watchlist button */}
      <View style={styles.actions}>
        <TouchableOpacity
          style={styles.watchBtn}
          onPress={() => setAlertVisible(true)}
        >
          <Text style={styles.watchBtnText}>➕ 添加到关注列表</Text>
        </TouchableOpacity>
      </View>

      {/* Price history table */}
      {history && history.price_history.length > 0 && (
        <View style={styles.historySection}>
          <Text style={styles.sectionTitle}>近期价格记录</Text>
          {history.price_history
            .slice(0, 15)
            .map((point, index) => (
              <View key={index} style={styles.historyRow}>
                <Text style={styles.historyPrice}>
                  ¥{point.price.toFixed(2)}
                </Text>
                <Text style={styles.historyDate}>
                  {new Date(point.recorded_at).toLocaleDateString('zh-CN', {
                    month: '2-digit',
                    day: '2-digit',
                    hour: '2-digit',
                    minute: '2-digit',
                  })}
                </Text>
              </View>
            ))}
        </View>
      )}

      <View style={{ height: 40 }} />

      {/* Alert form modal */}
      <AlertForm
        visible={alertVisible}
        onClose={() => setAlertVisible(false)}
        onSubmit={handleAddWatchlist}
        currentPrice={
          product.current_price !== null && product.current_price !== undefined
            ? product.current_price
            : null
        }
        isLoading={alertLoading}
      />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F5F5F5' },
  centered: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  header: {
    backgroundColor: '#fff',
    alignItems: 'center',
    padding: 24,
    position: 'relative',
  },
  image: { width: 200, height: 200, borderRadius: 8, backgroundColor: '#f5f5f5' },
  platformChip: {
    position: 'absolute',
    top: 12,
    right: 12,
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
  },
  platformChipText: { color: '#fff', fontSize: 12, fontWeight: '700' },
  infoSection: { backgroundColor: '#fff', padding: 16, marginTop: 1 },
  title: { fontSize: 16, fontWeight: '600', color: '#222', lineHeight: 24 },
  shop: { fontSize: 13, color: '#999', marginTop: 4 },
  priceRow: {
    flexDirection: 'row',
    alignItems: 'baseline',
    gap: 10,
    marginTop: 12,
  },
  price: { fontSize: 28, fontWeight: '800', color: '#E53935' },
  priceNA: { fontSize: 20, color: '#999', fontStyle: 'italic' },
  lowest: { fontSize: 13, color: '#999' },
  noChartCard: {
    backgroundColor: '#fff',
    margin: 12,
    borderRadius: 12,
    padding: 32,
    alignItems: 'center',
  },
  noChartText: { fontSize: 14, color: '#999' },
  noChartSubtext: { fontSize: 12, color: '#bbb', marginTop: 4 },
  actions: { padding: 16 },
  watchBtn: {
    backgroundColor: '#1976D2',
    borderRadius: 12,
    height: 50,
    justifyContent: 'center',
    alignItems: 'center',
  },
  watchBtnText: { color: '#fff', fontSize: 16, fontWeight: '600' },
  historySection: {
    backgroundColor: '#fff',
    marginHorizontal: 12,
    borderRadius: 12,
    padding: 16,
  },
  sectionTitle: {
    fontSize: 15,
    fontWeight: '600',
    color: '#333',
    marginBottom: 12,
  },
  historyRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 8,
    borderBottomWidth: 0.5,
    borderBottomColor: '#F0F0F0',
  },
  historyPrice: { fontSize: 15, fontWeight: '600', color: '#333' },
  historyDate: { fontSize: 12, color: '#999' },
});
