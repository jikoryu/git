import React, { useState } from 'react';
import {
  View,
  TextInput,
  TouchableOpacity,
  Text,
  StyleSheet,
} from 'react-native';

interface Props {
  onSearch: (query: string, platform?: string) => void;
  isLoading?: boolean;
}

const PLATFORMS = [
  { key: undefined, label: '全部' },
  { key: 'jd', label: '京东' },
  { key: 'taobao', label: '淘宝' },
  { key: 'pdd', label: '拼多多' },
];

export default function SearchBar({ onSearch, isLoading }: Props) {
  const [query, setQuery] = useState('');
  const [platform, setPlatform] = useState<string | undefined>(undefined);

  const handleSearch = () => {
    if (query.trim()) {
      onSearch(query.trim(), platform);
    }
  };

  return (
    <View style={styles.container}>
      <View style={styles.inputRow}>
        <TextInput
          style={styles.input}
          placeholder="搜索商品名称..."
          placeholderTextColor="#999"
          value={query}
          onChangeText={setQuery}
          onSubmitEditing={handleSearch}
          returnKeyType="search"
        />
        <TouchableOpacity
          style={[styles.button, isLoading && styles.buttonDisabled]}
          onPress={handleSearch}
          disabled={isLoading}
        >
          <Text style={styles.buttonText}>搜索</Text>
        </TouchableOpacity>
      </View>

      <View style={styles.filters}>
        {PLATFORMS.map((p) => (
          <TouchableOpacity
            key={p.label}
            style={[
              styles.filterChip,
              platform === p.key && styles.filterChipActive,
            ]}
            onPress={() => setPlatform(p.key)}
          >
            <Text
              style={[
                styles.filterText,
                platform === p.key && styles.filterTextActive,
              ]}
            >
              {p.label}
            </Text>
          </TouchableOpacity>
        ))}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { padding: 12, backgroundColor: '#fff' },
  inputRow: { flexDirection: 'row', gap: 8 },
  input: {
    flex: 1,
    height: 44,
    backgroundColor: '#F5F5F5',
    borderRadius: 10,
    paddingHorizontal: 14,
    fontSize: 15,
    color: '#333',
  },
  button: {
    backgroundColor: '#1976D2',
    borderRadius: 10,
    paddingHorizontal: 20,
    justifyContent: 'center',
  },
  buttonDisabled: { opacity: 0.5 },
  buttonText: { color: '#fff', fontSize: 15, fontWeight: '600' },
  filters: {
    flexDirection: 'row',
    marginTop: 10,
    gap: 8,
  },
  filterChip: {
    paddingHorizontal: 14,
    paddingVertical: 6,
    borderRadius: 16,
    backgroundColor: '#F0F0F0',
  },
  filterChipActive: { backgroundColor: '#E3F2FD' },
  filterText: { fontSize: 13, color: '#666' },
  filterTextActive: { color: '#1976D2', fontWeight: '600' },
});
