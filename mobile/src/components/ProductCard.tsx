import React from 'react';
import {
  View,
  Text,
  Image,
  TouchableOpacity,
  StyleSheet,
} from 'react-native';
import { Product } from '../types';
import { PLATFORM_LABELS, PLATFORM_COLORS } from '../types';
import PriceBadge from './PriceBadge';

interface Props {
  product: Product;
  onPress: (product: Product) => void;
}

export default function ProductCard({ product, onPress }: Props) {
  const platformColor = PLATFORM_COLORS[product.platform] || '#999';
  const platformLabel = PLATFORM_LABELS[product.platform] || product.platform;

  return (
    <TouchableOpacity style={styles.card} onPress={() => onPress(product)}>
      <Image
        source={{
          uri: product.image_url || 'https://via.placeholder.com/120',
        }}
        style={styles.image}
        resizeMode="contain"
      />
      <View style={styles.info}>
        <Text style={styles.title} numberOfLines={2}>
          {product.title}
        </Text>
        <View style={styles.meta}>
          <View style={[styles.platformTag, { borderColor: platformColor }]}>
            <Text style={[styles.platformText, { color: platformColor }]}>
              {platformLabel}
            </Text>
          </View>
          {product.shop_name && (
            <Text style={styles.shop} numberOfLines={1}>
              {product.shop_name}
            </Text>
          )}
        </View>
        <View style={styles.priceRow}>
          {product.current_price !== null && product.current_price !== undefined ? (
            <Text style={styles.currentPrice}>
              ¥{product.current_price.toFixed(2)}
            </Text>
          ) : (
            <Text style={styles.naPrice}>暂无价格</Text>
          )}
          {product.lowest_price !== null && product.lowest_price !== undefined &&
           product.current_price !== null && product.current_price !== undefined && (
            <Text style={styles.lowestPrice}>
              最低 ¥{product.lowest_price.toFixed(2)}
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
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  card: {
    flexDirection: 'row',
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 12,
    marginHorizontal: 12,
    marginVertical: 6,
    shadowColor: '#000',
    shadowOpacity: 0.06,
    shadowRadius: 8,
    shadowOffset: { width: 0, height: 2 },
    elevation: 2,
  },
  image: { width: 100, height: 100, borderRadius: 8, backgroundColor: '#f5f5f5' },
  info: { flex: 1, marginLeft: 12, justifyContent: 'space-between' },
  title: { fontSize: 14, fontWeight: '500', color: '#222', lineHeight: 20 },
  meta: { flexDirection: 'row', alignItems: 'center', gap: 8, marginTop: 4 },
  platformTag: {
    borderWidth: 1,
    borderRadius: 4,
    paddingHorizontal: 6,
    paddingVertical: 2,
  },
  platformText: { fontSize: 10, fontWeight: '600' },
  shop: { fontSize: 11, color: '#999', flex: 1 },
  priceRow: {
    flexDirection: 'row',
    alignItems: 'baseline',
    gap: 8,
    marginTop: 6,
  },
  currentPrice: {
    fontSize: 20,
    fontWeight: '700',
    color: '#E53935',
  },
  lowestPrice: {
    fontSize: 12,
    color: '#999',
    textDecorationLine: 'line-through',
  },
  naPrice: {
    fontSize: 15,
    color: '#999',
    fontStyle: 'italic',
  },
});
