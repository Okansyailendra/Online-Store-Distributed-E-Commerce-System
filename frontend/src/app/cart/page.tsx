"use client";

import { useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Trash2, ArrowRight, ShoppingBag, ShieldCheck } from "lucide-react";
import { useCartStore } from "@/store/useCartStore";
import { useAuthStore } from "@/store/useAuthStore";
import { formatRupiah } from "@/lib/utils";

export default function CartPage() {
  const router = useRouter();
  const { items, totalAmount, totalItems, fetchCart, updateQuantity, removeItem, isLoading } = useCartStore();
  const { token, isAuthenticated } = useAuthStore();

  useEffect(() => {
    if (token) {
      fetchCart(token);
    }
  }, [token, fetchCart]);

  if (!isAuthenticated) {
    return (
      <div className="container mx-auto px-4 py-16 text-center">
        <h2 className="text-xl font-bold mb-3">Silakan Masuk Terlebih Dahulu</h2>
        <p className="text-slate-500 text-sm mb-6">Anda perlu login untuk melihat isi keranjang belanja.</p>
        <Link href="/auth/login" className="px-6 py-2.5 bg-blue-600 text-white rounded-xl font-semibold text-sm">
          Masuk ke Akun
        </Link>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 sm:px-6 py-8">
      <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white mb-2">
        Keranjang Belanja
      </h1>
      <p className="text-sm text-slate-500 mb-8">
        Kelola barang belanjaan sebelum diproses ke checkout RPC atomik
      </p>

      {items.length === 0 ? (
        <div className="p-12 text-center rounded-3xl bg-white border dark:bg-slate-900 dark:border-slate-800">
          <ShoppingBag className="w-12 h-12 text-slate-300 mx-auto mb-3" />
          <h3 className="font-bold text-base text-slate-800 dark:text-slate-200">Keranjang Anda Kosong</h3>
          <p className="text-xs text-slate-400 mt-1 mb-6">Mulai pilih produk unggulan di katalog kami.</p>
          <Link
            href="/products"
            className="px-6 py-2.5 rounded-xl bg-blue-600 text-white font-semibold text-sm shadow hover:bg-blue-700 transition"
          >
            Jelajahi Produk
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Daftar Barang */}
          <div className="lg:col-span-2 space-y-4">
            {items.map((item) => (
              <div
                key={item.cart_item_id}
                className="flex flex-col sm:flex-row items-center justify-between gap-4 p-4 rounded-2xl bg-white border dark:bg-slate-900 dark:border-slate-800 shadow-sm"
              >
                <div className="flex items-center gap-4 w-full sm:w-auto">
                  <div className="h-20 w-20 rounded-xl overflow-hidden bg-slate-100 shrink-0">
                    <img
                      src={item.image_url || "/images/placeholder.webp"}
                      alt={item.name}
                      className="w-full h-full object-cover"
                    />
                  </div>
                  <div>
                    <h4 className="font-bold text-sm text-slate-900 dark:text-white line-clamp-1">{item.name}</h4>
                    <p className="text-xs text-slate-400">SKU: {item.sku}</p>
                    <div className="font-extrabold text-blue-600 text-sm mt-1">
                      {formatRupiah(item.unit_price)}
                    </div>
                  </div>
                </div>

                <div className="flex items-center justify-between sm:justify-end gap-6 w-full sm:w-auto pt-2 sm:pt-0 border-t sm:border-t-0">
                  <div className="flex items-center border rounded-lg bg-slate-50 dark:bg-slate-800 dark:border-slate-700">
                    <button
                      onClick={() => updateQuantity(item.cart_item_id, Math.max(1, item.quantity - 1), token || undefined)}
                      className="px-2.5 py-0.5 text-sm font-bold text-slate-600"
                    >
                      -
                    </button>
                    <span className="px-3 py-0.5 text-xs font-bold">{item.quantity}</span>
                    <button
                      onClick={() => updateQuantity(item.cart_item_id, item.quantity + 1, token || undefined)}
                      className="px-2.5 py-0.5 text-sm font-bold text-slate-600"
                    >
                      +
                    </button>
                  </div>

                  <div className="font-bold text-sm text-slate-800 dark:text-slate-200 min-w-[100px] text-right">
                    {formatRupiah(item.subtotal)}
                  </div>

                  <button
                    onClick={() => removeItem(item.cart_item_id, token || undefined)}
                    className="p-1.5 text-slate-400 hover:text-red-600 transition"
                    title="Hapus"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>

          {/* Ringkasan Belanja */}
          <div className="lg:col-span-1">
            <div className="p-6 rounded-3xl bg-white border dark:bg-slate-900 dark:border-slate-800 shadow-sm space-y-6">
              <h3 className="font-bold text-base text-slate-900 dark:text-white">Ringkasan Belanja</h3>

              <div className="space-y-3 text-sm">
                <div className="flex justify-between text-slate-500">
                  <span>Total Kuantitas</span>
                  <span className="font-semibold text-slate-700 dark:text-slate-300">{totalItems} Barang</span>
                </div>
                <div className="flex justify-between text-slate-500">
                  <span>Subtotal Produk</span>
                  <span className="font-semibold text-slate-700 dark:text-slate-300">{formatRupiah(totalAmount)}</span>
                </div>
                <div className="border-t pt-3 flex justify-between font-extrabold text-base text-slate-900 dark:text-white">
                  <span>Total Tagihan</span>
                  <span className="text-blue-600">{formatRupiah(totalAmount)}</span>
                </div>
              </div>

              <Link
                href="/checkout"
                className="w-full py-3.5 px-6 rounded-xl bg-blue-600 text-white font-bold text-sm hover:bg-blue-700 shadow-lg shadow-blue-500/20 transition flex items-center justify-center gap-2"
              >
                Lanjut ke Checkout
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
