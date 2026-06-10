import React from 'react';
import { View, Text, StyleSheet } from 'react-native';

interface Props {
  currentPrice: number;
  lowestPrice: number | null;
}

export default function PriceBadge({ currentPrice, lowestPrice }: Props) {
  if (lowestPrice === null || currentPrice === lowestPrice) {
    return (
      <View style={[styles.badge, styles.normalBadge]}>
        <Text style={styles.normalText}>当前最低</Text>
      </View>
    );
  }

  const diff = currentPrice - lowestPrice;
  const percent = ((diff / lowestPrice) * 100).toFixed(1);

  if (diff > 0) {
    return (
      <View style={[styles.badge, styles.higherBadge]}>
        <Text style={styles.higherText}>
          高于最低 ¥{diff.toFixed(0)} ({percent}%)
        </Text>
      </View>
    );
  }

  return (
    <View style={[styles.badge, styles.lowerBadge]}>
      <Text style={styles.lowerText}>
        ↓ 新低! ¥{Math.abs(diff).toFixed(0)} ({Math.abs(Number(percent))}%)
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  badge: {
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 12,
    alignSelf: 'flex-start',
  },
  normalBadge: { backgroundColor: '#E8F5E9' },
  higherBadge: { backgroundColor: '#FFF3E0' },
  lowerBadge: { backgroundColor: '#FFEBEE' },
  normalText: { color: '#2E7D32', fontSize: 11, fontWeight: '600' },
  higherText: { color: '#E65100', fontSize: 11, fontWeight: '600' },
  lowerText: { color: '#C62828', fontSize: 11, fontWeight: '600' },
});
