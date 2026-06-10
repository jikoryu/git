import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  Switch,
  StyleSheet,
  Modal,
} from 'react-native';

interface Props {
  visible: boolean;
  onClose: () => void;
  onSubmit: (targetPrice?: number, notifyOnAnyDrop?: boolean) => void;
  currentPrice: number | null;
  isLoading?: boolean;
}

export default function AlertForm({
  visible,
  onClose,
  onSubmit,
  currentPrice,
  isLoading,
}: Props) {
  const [mode, setMode] = useState<'any_drop' | 'target'>('any_drop');
  const [targetPrice, setTargetPrice] = useState('');

  const handleSubmit = () => {
    if (mode === 'target' && targetPrice) {
      onSubmit(parseFloat(targetPrice), false);
    } else {
      onSubmit(undefined, true);
    }
  };

  return (
    <Modal visible={visible} transparent animationType="slide">
      <View style={styles.overlay}>
        <View style={styles.sheet}>
          <Text style={styles.title}>设置降价提醒</Text>

          {currentPrice !== null && currentPrice !== undefined && (
            <Text style={styles.currentPrice}>
              当前价格: ¥{currentPrice.toFixed(2)}
            </Text>
          )}

          {/* Mode: Any drop */}
          <TouchableOpacity
            style={[styles.option, mode === 'any_drop' && styles.optionActive]}
            onPress={() => setMode('any_drop')}
          >
            <View style={styles.optionContent}>
              <Text style={styles.optionTitle}>任何降价都通知</Text>
              <Text style={styles.optionDesc}>
                只要价格下降就会收到通知
              </Text>
            </View>
            <View
              style={[
                styles.radio,
                mode === 'any_drop' && styles.radioActive,
              ]}
            />
          </TouchableOpacity>

          {/* Mode: Target price */}
          <TouchableOpacity
            style={[styles.option, mode === 'target' && styles.optionActive]}
            onPress={() => setMode('target')}
          >
            <View style={styles.optionContent}>
              <Text style={styles.optionTitle}>设置目标价格</Text>
              <Text style={styles.optionDesc}>
                低于目标价格时通知我
              </Text>
            </View>
            <View
              style={[
                styles.radio,
                mode === 'target' && styles.radioActive,
              ]}
            />
          </TouchableOpacity>

          {mode === 'target' && (
            <View style={styles.targetInput}>
              <Text style={styles.yenSign}>¥</Text>
              <TextInput
                style={styles.input}
                placeholder="输入目标价格"
                placeholderTextColor="#ccc"
                keyboardType="decimal-pad"
                value={targetPrice}
                onChangeText={setTargetPrice}
              />
            </View>
          )}

          <View style={styles.actions}>
            <TouchableOpacity style={styles.cancelBtn} onPress={onClose}>
              <Text style={styles.cancelText}>取消</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[
                styles.submitBtn,
                isLoading && styles.submitBtnDisabled,
              ]}
              onPress={handleSubmit}
              disabled={isLoading}
            >
              <Text style={styles.submitText}>
                {isLoading ? '添加中...' : '确认添加'}
              </Text>
            </TouchableOpacity>
          </View>
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.4)',
    justifyContent: 'flex-end',
  },
  sheet: {
    backgroundColor: '#fff',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    padding: 20,
    paddingBottom: 40,
  },
  title: {
    fontSize: 18,
    fontWeight: '700',
    color: '#222',
    marginBottom: 4,
  },
  currentPrice: {
    fontSize: 14,
    color: '#E53935',
    marginBottom: 16,
    fontWeight: '500',
  },
  option: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 14,
    borderRadius: 10,
    borderWidth: 1.5,
    borderColor: '#E0E0E0',
    marginBottom: 10,
  },
  optionActive: {
    borderColor: '#1976D2',
    backgroundColor: '#F5F9FF',
  },
  optionContent: { flex: 1 },
  optionTitle: { fontSize: 15, fontWeight: '600', color: '#333' },
  optionDesc: { fontSize: 12, color: '#999', marginTop: 2 },
  radio: {
    width: 20,
    height: 20,
    borderRadius: 10,
    borderWidth: 2,
    borderColor: '#ccc',
  },
  radioActive: {
    borderColor: '#1976D2',
    backgroundColor: '#1976D2',
  },
  targetInput: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 8,
    marginBottom: 8,
    backgroundColor: '#F5F5F5',
    borderRadius: 10,
    paddingHorizontal: 14,
  },
  yenSign: { fontSize: 18, color: '#333', marginRight: 4 },
  input: { flex: 1, height: 48, fontSize: 18, color: '#333' },
  actions: {
    flexDirection: 'row',
    gap: 12,
    marginTop: 16,
  },
  cancelBtn: {
    flex: 1,
    height: 46,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#E0E0E0',
    justifyContent: 'center',
    alignItems: 'center',
  },
  cancelText: { fontSize: 15, color: '#666' },
  submitBtn: {
    flex: 1,
    height: 46,
    borderRadius: 10,
    backgroundColor: '#1976D2',
    justifyContent: 'center',
    alignItems: 'center',
  },
  submitBtnDisabled: { opacity: 0.5 },
  submitText: { fontSize: 15, fontWeight: '600', color: '#fff' },
});
