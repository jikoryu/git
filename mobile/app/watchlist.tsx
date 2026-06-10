import React, { useEffect, useCallback } from 'react';
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  Image,
  ActivityIndicator,
  Alert,
  StyleSheet,
} from 'react-native';
import { useRouter } from 'expo-router';
import { useWatchlistStore } from '../src/store/watchlistStore';
import { WatchlistItem, PLATFORM_LABELS } from '../src/types';
import PriceBadge from '../src/components/PriceBadge';

export default function WatchlistScreen() {
  const { items, isLoading, error, fetch, remove } = useWatchlistStore();
  const router = useRouter();

  useEffect(() => {
    fetch();
  }, []);

  const handleRemove = (item: WatchlistItem) => {
    Alert.alert('取消关注', `确定不再追踪「${item.product_title}」？`, [
      { text: '取消', style: 'cancel' },
      {
        text: '确定',
        style: 'destructive',
        onPress: () => remove(item.id),
      },
    ]);
  };

  const renderItem = ({ item }: { item: WatchlistItem }) => {
    const hasDrop =
      item.current_price !== null &&
      item.current_price !== undefined &&
      item.lowest_price !== null &&
      item.lowest_price !== undefined &&
      item.current_price > item.lowest_price;

    return (
      <TouchableOpacity
        style={styles.card}
        onPress={() => router.push(`/product/${item.product_id}`)}
      >
        <Image
          source={{
            uri: item.product_image || 'https://via.placeholder.com/80',
          }}
          style={styles.image}
          resizeMode="contain"
        />
        <View style={styles.info}>
          <Text style={styles.title} numberOfLines={2}>
            {item.product_title}
          </Text>
          <Text style={styles.platform}>
            {PLATFORM_LABELS[item.platform] || item.platform}
            {item.target_price !== null && item.target_price !== undefined
              ? ` · 目标: ¥${Number(item.target_price).toFixed(2)}`
              : ' · 降价通知'}
          </Text>
          <View style={styles.priceRow}>
            {item.current_price !== null && item.current_price !== undefined ? (
              <Text style={styles.price}>
                ¥{Number(item.current_price).toFixed(2)}
              </Text>
            ) : (
              <Text style={styles.priceNA}>暂无价格</Text>
            )}
          </View>
          {item.current_price !== null && item.current_price !== undefined &&
           item.lowest_price !== null && item.lowest_price !== undefined && (
            <PriceBadge
              currentPrice={Number(item.current_price)}
              lowestPrice={Number(item.lowest_price)}
            />
          )}
        </View>
        <TouchableOpacity
          style={styles.removeBtn}
          onPress={() => handleRemove(item)}
          hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
        >
          <Text style={styles.removeText}>✕</Text>
        </TouchableOpacity>
      </TouchableOpacity>
    );
  };

  if (isLoading && items.length === 0) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color="#1976D2" />
      </View>
    );
  }

  if (items.length === 0) {
    return (
      <View style={styles.centered}>
        <Text style={styles.emptyIcon}>📋</Text>
        <Text style={styles.emptyText}>还没有关注任何商品</Text>
        <Text style={styles.emptySubtext}>
          搜索商品并添加到关注列表
        </Text>
      </View>
    );
  }

  return (
    <FlatList
      data={items}
      keyExtractor={(item) => item.id}
      renderItem={renderItem}
      contentContainerStyle={styles.list}
      onRefresh={fetch}
      refreshing={isLoading}
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
    alignItems: 'center',
  },
  image: { width: 72, height: 72, borderRadius: 8, backgroundColor: '#f5f5f5' },
  info: { flex: 1, marginLeft: 12, marginRight: 8 },
  title: { fontSize: 14, fontWeight: '500', color: '#222', lineHeight: 20 },
  platform: { fontSize: 11, color: '#999', marginTop: 2 },
  priceRow: { flexDirection: 'row', alignItems: 'baseline', marginTop: 6 },
  price: { fontSize: 18, fontWeight: '700', color: '#E53935' },
  priceNA: { fontSize: 14, color: '#999', fontStyle: 'italic' },
  removeBtn: { padding: 6 },
  removeText: { fontSize: 16, color: '#ccc' },
});
