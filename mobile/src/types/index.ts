// ── User ──
export interface User {
  id: string;
  email: string;
  created_at: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

// ── Product ──
export interface Product {
  id: string;
  platform: 'jd' | 'taobao' | 'pdd';
  platform_id: string;
  title: string;
  image_url: string | null;
  shop_name: string | null;
  url: string;
  current_price: number | null;
  lowest_price: number | null;
  created_at: string;
  updated_at: string;
}

export interface PricePoint {
  price: number;
  recorded_at: string;
}

export interface ProductHistory {
  product: Product;
  price_history: PricePoint[];
}

// ── Watchlist ──
export interface WatchlistItem {
  id: string;
  product_id: string;
  target_price: number | null;
  notify_on_any_drop: boolean;
  created_at: string;
  product_title: string;
  product_image: string | null;
  product_url: string;
  platform: string;
  current_price: number | null;
  lowest_price: number | null;
}

// ── Alert ──
export interface PriceAlert {
  id: string;
  product_id: string;
  old_price: number;
  new_price: number;
  drop_percent: number | null;
  is_sent: boolean;
  created_at: string;
  product_title: string;
  product_image: string | null;
  platform: string;
}

// ── Platform ──
export const PLATFORM_LABELS: Record<string, string> = {
  jd: '京东',
  taobao: '淘宝',
  pdd: '拼多多',
};

export const PLATFORM_COLORS: Record<string, string> = {
  jd: '#E2231A',
  taobao: '#FF5000',
  pdd: '#E02E24',
};
