import { create } from "zustand";
import { apiFetch } from "@/lib/failoverRouter";

export interface CartItem {
  cart_item_id: string;
  product_id: string;
  quantity: number;
  name: string;
  sku: string;
  unit_price: number;
  current_stock: number;
  image_url: string;
  subtotal: number;
}

interface CartStore {
  items: CartItem[];
  totalItems: number;
  totalAmount: number;
  isLoading: boolean;
  fetchCart: (token?: string) => Promise<void>;
  addItem: (productId: string, quantity?: number, token?: string) => Promise<boolean>;
  updateQuantity: (cartItemId: string, quantity: number, token?: string) => Promise<boolean>;
  removeItem: (cartItemId: string, token?: string) => Promise<boolean>;
  clearCartLocally: () => void;
}

export const useCartStore = create<CartStore>((set, get) => ({
  items: [],
  totalItems: 0,
  totalAmount: 0,
  isLoading: false,

  fetchCart: async (token) => {
    if (!token) return;
    set({ isLoading: true });
    const res = await apiFetch("/cart", {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (res.success && res.data) {
      set({
        items: res.data.items || [],
        totalItems: res.data.total_items || 0,
        totalAmount: res.data.total_amount || 0,
      });
    }
    set({ isLoading: false });
  },

  addItem: async (productId, quantity = 1, token) => {
    if (!token) return false;
    const res = await apiFetch("/cart/items", {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
      body: JSON.stringify({ product_id: productId, quantity }),
    });
    if (res.success) {
      await get().fetchCart(token);
      return true;
    }
    return false;
  },

  updateQuantity: async (cartItemId, quantity, token) => {
    if (!token) return false;
    const res = await apiFetch(`/cart/items/${cartItemId}`, {
      method: "PUT",
      headers: { Authorization: `Bearer ${token}` },
      body: JSON.stringify({ quantity }),
    });
    if (res.success) {
      await get().fetchCart(token);
      return true;
    }
    return false;
  },

  removeItem: async (cartItemId, token) => {
    if (!token) return false;
    const res = await apiFetch(`/cart/items/${cartItemId}`, {
      method: "DELETE",
      headers: { Authorization: `Bearer ${token}` },
    });
    if (res.success) {
      await get().fetchCart(token);
      return true;
    }
    return false;
  },

  clearCartLocally: () => {
    set({ items: [], totalItems: 0, totalAmount: 0 });
  },
}));
