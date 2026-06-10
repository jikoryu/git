import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  FlatList,
  Image,
  ActivityIndicator,
  StyleSheet,
} from 'react-native';
import { alertsApi } from '../src/services/api';
import { PriceAlert, PLATFORM_LABELS } from '../src/types';

export default function AlertsScreen() {
  const [alerts, setAlerts] = useState<PriceAlert[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAlerts = async () => {
    setLoading(true);
    setError(null);
    try {
      const { data } = await alertsApi.getAll();
      setAlerts(data);
    } catch (err: any) {
      setError(err?.response?.data?.detail || '加载失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAlerts();
  }, []);

  if (loading && alerts.length === 0) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color="#1976D2" />
      </View>
    );
  }

  if (alerts.length === 0) {
    return (
      <View style={styles.centered}>
        <Text style={styles.emptyIcon}>🔔</Text>
        <Text style={styles.emptyText}>暂无降价提醒</Text>
        <Text style={styles.emptySubtext}>
          当关注的商品降价时，会显示在这里
        </Text>
      </View>
    );
  }

  const renderItem = ({ item }: { item: PriceAlert }) => (
    <View style={styles.card}>
      {item.product_image && (
        <Image
          source={{ uri: item.product_image }}
          style={styles.image}
          resizeMode="contain"
        />
      )}
      <View style={styles.info}>
        <Text style={styles.title} numberOfLines={2}>
          {item.product_title}
        </Text>
        <Text style={styles.platform}>
          {PLATFORM_LABELS[item.platform] || item.platform}
        </Text>
        <View style={styles.priceRow}>
          <View>
            <Text style={styles.oldPrice}>
              ¥{Number(item.old_price).toFixed(2)}
            </Text>
            <Text style={styles.arrow}>↓</Text>
            <Text style={styles.newPrice}>
              ¥{Number(item.new_price).toFixed(2)}
            </Text>
          </View>
          <View style={styles.dropBadge}>
            <Text style={styles.dropText}>
              -{Number(item.drop_percent).toFixed(1)}%
            </Text>
          </View>
        </View>
        <Text style={styles.date}>
          {new Date(item.created_at).toLocaleDateString('zh-CN', {
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
          })}
          {!item.is_sent && ' · 发送中'}
        </Text>
      </View>
    </View>
  );

  return (
    <FlatList
      data={alerts}
      keyExtractor={(item) => item.id}
      renderItem={renderItem}
      contentContainerStyle={styles.list}
      onRefresh={fetchAlerts}
      refreshing={loading}
    />
  );
}

const styles = StyleSheet.create({
  centered: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 40 },
  emptyIcon: { fontSize: 48, marginBottom: 12 },
  emptyText: { fontSize: 16, color: '#666', fontWeight: '500' },
  emptySubtext: { fontSize: 13, color: '#999', marginTop: 4 },
  list: { padding: 12 },
  card: {
    flexDirection: 'row',
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 12,
    marginBottom: 10,
    shadowColor: '#000',
    shadowOpacity: 0.04,
    shadowRadius: 6,
    elevation: 1,
  },
  image: { width: 60, height: 60, borderRadius: 6, backgroundColor: '#f5f5f5' },
  info: { flex: 1, marginLeft: 12 },
  title: { fontSize: 14, fontWeight: '500', color: '#222', lineHeight: 20 },
  platform: { fontSize: 11, color: '#999', marginTop: 2 },
  priceRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginTop: 8,
  },
  oldPrice: {
    fontSize: 13,
    color: '#999',
    textDecorationLine: 'line-through',
  },
  arrow: { fontSize: 14, color: '#4CAF50', fontWeight: '700', marginVertical: 2 },
  newPrice: { fontSize: 18, fontWeight: '700', color: '#E53935' },
  dropBadge: {
    backgroundColor: '#FFEBEE',
    borderRadius: 8,
    paddingHorizontal: 10,
    paddingVertical: 4,
  },
  dropText: { fontSize: 14, fontWeight: '700', color: '#C62828' },
  date: { fontSize: 11, color: '#bbb', marginTop: 6 },
});
