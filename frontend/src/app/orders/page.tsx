"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Package, Clock, CheckCircle2, ChevronRight, ShoppingBag } from "lucide-react";
import { apiFetch } from "@/lib/failoverRouter";
import { useAuthStore } from "@/store/useAuthStore";
import { formatRupiah, formatDate } from "@/lib/utils";

export default function OrdersPage() {
  const { token, isAuthenticated } = useAuthStore();
  const [orders, setOrders] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadOrders() {
      if (!token) return;
      setLoading(true);
      const res = await apiFetch("/orders", {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.success && res.data) {
        setOrders(res.data);
      }
      setLoading(false);
    }
    loadOrders();
  }, [token]);

  if (!isAuthenticated) {
    return (
      <div className="container mx-auto px-4 py-16 text-center">
        <h2 className="text-xl font-bold mb-3">Silakan Masuk Terlebih Dahulu</h2>
        <Link href="/auth/login" className="px-6 py-2.5 bg-blue-600 text-white rounded-xl font-semibold text-sm">
          Masuk ke Akun
        </Link>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 sm:px-6 py-8">
      <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white mb-2">
        Riwayat Pesanan Saya
      </h1>
      <p className="text-sm text-slate-500 mb-8">
        Lacak status pesanan, faktur transaksi, dan riwayat pembayaran
      </p>

      {loading ? (
        <div className="space-y-4">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-28 rounded-2xl bg-slate-200 dark:bg-slate-800 animate-pulse" />
          ))}
        </div>
      ) : orders.length === 0 ? (
        <div className="p-12 text-center rounded-3xl bg-white border dark:bg-slate-900 dark:border-slate-800">
          <Package className="w-12 h-12 text-slate-300 mx-auto mb-3" />
          <h3 className="font-bold text-base text-slate-800 dark:text-slate-200">Belum Ada Pesanan</h3>
          <p className="text-xs text-slate-400 mt-1 mb-6">Anda belum pernah melakukan transaksi pembelian.</p>
          <Link
            href="/products"
            className="px-6 py-2.5 rounded-xl bg-blue-600 text-white font-semibold text-sm shadow hover:bg-blue-700 transition"
          >
            Mulai Belanja
          </Link>
        </div>
      ) : (
        <div className="space-y-4">
          {orders.map((order) => (
            <div
              key={order.id}
              className="p-5 rounded-2xl bg-white border dark:bg-slate-900 dark:border-slate-800 shadow-sm flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4"
            >
              <div className="space-y-1.5">
                <div className="flex items-center gap-3">
                  <span className="font-extrabold text-sm text-slate-900 dark:text-white">
                    {order.order_number}
                  </span>
                  <span
                    className={`px-2.5 py-0.5 rounded-full text-[11px] font-bold ${
                      order.status === "DELIVERED"
                        ? "bg-emerald-50 text-emerald-700"
                        : order.status === "PROCESSING" || order.status === "PAID"
                        ? "bg-blue-50 text-blue-700"
                        : order.status === "CANCELLED"
                        ? "bg-red-50 text-red-600"
                        : "bg-amber-50 text-amber-700"
                    }`}
                  >
                    {order.status}
                  </span>
                </div>
                <div className="text-xs text-slate-400 flex items-center gap-2">
                  <Clock className="w-3.5 h-3.5" />
                  {formatDate(order.created_at)} • Kurir: {order.shipping_courier}
                </div>
              </div>

              <div className="flex items-center justify-between sm:justify-end gap-6 w-full sm:w-auto pt-3 sm:pt-0 border-t sm:border-t-0">
                <div className="text-left sm:text-right">
                  <div className="text-xs text-slate-400">Total Tagihan</div>
                  <div className="font-extrabold text-base text-blue-600">
                    {formatRupiah(order.total_amount)}
                  </div>
                </div>

                <div className="text-xs px-3 py-1.5 rounded-lg border bg-slate-50 font-semibold text-slate-700 dark:bg-slate-800 dark:text-slate-300">
                  {order.total_items_count || 1} Item
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
