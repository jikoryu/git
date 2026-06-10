import React, { useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Dimensions } from 'react-native';
import { CartesianChart, Line, useChartPressState } from 'victory-native';
import { Circle, useFont } from '@shopify/react-native-skia';
import { PricePoint } from '../types';

interface Props {
  priceHistory: PricePoint[];
}

type Range = 30 | 90 | 365;

const RANGES: { key: Range; label: string }[] = [
  { key: 30, label: '30天' },
  { key: 90, label: '90天' },
  { key: 365, label: '1年' },
];

const CHART_HEIGHT = 220;
const { width: SCREEN_WIDTH } = Dimensions.get('window');

export default function PriceChart({ priceHistory }: Props) {
  const [range, setRange] = useState<Range>(30);

  if (priceHistory.length < 2) {
    return (
      <View style={styles.emptyContainer}>
        <Text style={styles.emptyText}>价格数据不足，无法绘制图表</Text>
        <Text style={styles.emptySubtext}>请等待更多价格数据被收集</Text>
      </View>
    );
  }

  // Filter by selected range
  const cutoff = Date.now() - range * 24 * 60 * 60 * 1000;
  const filtered = priceHistory.filter(
    (p) => new Date(p.recorded_at).getTime() >= cutoff
  );

  const data = filtered.map((p) => ({
    x: new Date(p.recorded_at).getTime(),
    y: p.price,
  }));

  const minPrice = Math.min(...data.map((d) => d.y));
  const maxPrice = Math.max(...data.map((d) => d.y));
  const priceDiff = maxPrice - minPrice;

  // Format date for x-axis
  const formatDate = (ts: number) => {
    const d = new Date(ts);
    return `${d.getMonth() + 1}/${d.getDate()}`;
  };

  return (
    <View style={styles.container}>
      <View style={styles.rangeRow}>
        {RANGES.map((r) => (
          <TouchableOpacity
            key={r.key}
            style={[styles.rangeBtn, range === r.key && styles.rangeBtnActive]}
            onPress={() => setRange(r.key)}
          >
            <Text
              style={[
                styles.rangeText,
                range === r.key && styles.rangeTextActive,
              ]}
            >
              {r.label}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      <View style={styles.chartWrapper}>
        {data.length >= 2 ? (
          <CartesianChart
            data={data}
            xKey="x"
            yKeys={['y']}
            domainPadding={{ left: 10, right: 10, top: 20, bottom: 10 }}
            axisOptions={{
              font: undefined,
              labelColor: '#999',
              lineColor: '#E0E0E0',
              tickCount: { x: 5, y: 5 },
              formatXLabel: (ms) => formatDate(Number(ms)),
              formatYLabel: (price) => `¥${Number(price).toFixed(0)}`,
            }}
          >
            {({ points, chartBounds }) => (
              <Line
                points={points.y}
                color="#1976D2"
                strokeWidth={2}
                animate={{ type: 'timing', duration: 300 }}
              />
            )}
          </CartesianChart>
        ) : (
          <Text style={styles.noDataText}>该时间段内数据不足</Text>
        )}
      </View>

      <View style={styles.stats}>
        <View style={styles.statItem}>
          <Text style={styles.statLabel}>当前</Text>
          <Text style={styles.statValue}>
            ¥{data[data.length - 1]?.y.toFixed(2) || '-'}
          </Text>
        </View>
        <View style={styles.statItem}>
          <Text style={styles.statLabel}>最低</Text>
          <Text style={[styles.statValue, { color: '#2E7D32' }]}>
            ¥{minPrice.toFixed(2)}
          </Text>
        </View>
        <View style={styles.statItem}>
          <Text style={styles.statLabel}>最高</Text>
          <Text style={[styles.statValue, { color: '#C62828' }]}>
            ¥{maxPrice.toFixed(2)}
          </Text>
        </View>
        <View style={styles.statItem}>
          <Text style={styles.statLabel}>波动</Text>
          <Text style={styles.statValue}>
            ¥{priceDiff.toFixed(2)}
          </Text>
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { backgroundColor: '#fff', borderRadius: 12, margin: 12, padding: 16 },
  rangeRow: { flexDirection: 'row', gap: 8, marginBottom: 12 },
  rangeBtn: {
    paddingHorizontal: 14,
    paddingVertical: 6,
    borderRadius: 16,
    backgroundColor: '#F0F0F0',
  },
  rangeBtnActive: { backgroundColor: '#1976D2' },
  rangeText: { fontSize: 13, color: '#666' },
  rangeTextActive: { color: '#fff', fontWeight: '600' },
  chartWrapper: { height: CHART_HEIGHT, marginBottom: 12 },
  noDataText: { textAlign: 'center', color: '#999', marginTop: 80 },
  stats: { flexDirection: 'row', justifyContent: 'space-around', paddingTop: 8, borderTopWidth: 1, borderTopColor: '#F0F0F0' },
  statItem: { alignItems: 'center' },
  statLabel: { fontSize: 11, color: '#999', marginBottom: 2 },
  statValue: { fontSize: 16, fontWeight: '600', color: '#333' },
  emptyContainer: {
    backgroundColor: '#fff',
    margin: 12,
    borderRadius: 12,
    padding: 40,
    alignItems: 'center',
  },
  emptyText: { fontSize: 15, color: '#999', marginBottom: 4 },
  emptySubtext: { fontSize: 12, color: '#bbb' },
});
