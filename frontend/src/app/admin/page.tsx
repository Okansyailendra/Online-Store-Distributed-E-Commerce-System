"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { DollarSign, ShoppingBag, Users, AlertCircle, ArrowRight, ShieldCheck, Activity, Package } from "lucide-react";
import { apiFetch } from "@/lib/failoverRouter";
import { useAuthStore } from "@/store/useAuthStore";
import { formatRupiah } from "@/lib/utils";

export default function AdminDashboardPage() {
  const { token, user } = useAuthStore();
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadStats() {
      if (!token) return;
      setLoading(true);
      const res = await apiFetch("/admin/stats", {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.success && res.data) {
        setStats(res.data);
      }
      setLoading(false);
    }
    loadStats();
  }, [token]);

  return (
    <div className="container mx-auto px-4 sm:px-6 py-8 space-y-8">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white">
            Portal Admin Toko
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Ringkasan metrik penjualan, kontrol inventaris RMI, dan navigasi operasional toko.
          </p>
        </div>

        <Link
          href="/admin/cluster"
          className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold bg-emerald-600 text-white hover:bg-emerald-700 shadow transition"
        >
          <Activity className="w-4 h-4 animate-pulse" />
          Live Cluster Monitor
        </Link>
      </div>

      {/* Grid Statistik */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-5 rounded-2xl bg-white border dark:bg-slate-900 dark:border-slate-800 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-500 uppercase">Total Pendapatan</span>
            <DollarSign className="w-4 h-4 text-emerald-600" />
          </div>
          <div className="text-xl font-black text-slate-900 dark:text-white mt-2">
            {formatRupiah(stats?.total_revenue || 0)}
          </div>
        </div>

        <div className="p-5 rounded-2xl bg-white border dark:bg-slate-900 dark:border-slate-800 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-500 uppercase">Total Pesanan</span>
            <ShoppingBag className="w-4 h-4 text-blue-600" />
          </div>
          <div className="text-2xl font-black text-slate-900 dark:text-white mt-2">
            {stats?.total_orders || 0}
          </div>
        </div>

        <div className="p-5 rounded-2xl bg-white border dark:bg-slate-900 dark:border-slate-800 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-500 uppercase">Pelanggan Terdaftar</span>
            <Users className="w-4 h-4 text-purple-600" />
          </div>
          <div className="text-2xl font-black text-slate-900 dark:text-white mt-2">
            {stats?.total_customers || 0}
          </div>
        </div>

        <div className="p-5 rounded-2xl bg-white border dark:bg-slate-900 dark:border-slate-800 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-500 uppercase">Stok Menipis (&lt;5)</span>
            <AlertCircle className="w-4 h-4 text-amber-500" />
          </div>
          <div className="text-2xl font-black text-amber-600 mt-2">
            {stats?.low_stock_products_count || 0} Produk
          </div>
        </div>
      </div>

      {/* Menu Navigasi Cepat Admin */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Link
          href="/admin/inventory"
          className="p-6 rounded-2xl bg-white border hover:border-blue-500 hover:shadow-md transition dark:bg-slate-900 dark:border-slate-800 group"
        >
          <div className="h-10 w-10 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center mb-4 group-hover:scale-110 transition">
            <Package className="w-5 h-5" />
          </div>
          <h3 className="font-bold text-base text-slate-900 dark:text-white group-hover:text-blue-600 transition">
            Manajemen Stok Real-Time (RMI)
          </h3>
          <p className="text-xs text-slate-500 mt-1">
            Tambah stok barang fisik secara langsung melalui pemanggilan remote method RMI `restock_product`.
          </p>
        </Link>

        <Link
          href="/admin/cluster"
          className="p-6 rounded-2xl bg-white border hover:border-emerald-500 hover:shadow-md transition dark:bg-slate-900 dark:border-slate-800 group"
        >
          <div className="h-10 w-10 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center mb-4 group-hover:scale-110 transition">
            <Activity className="w-5 h-5" />
          </div>
          <h3 className="font-bold text-base text-slate-900 dark:text-white group-hover:text-emerald-600 transition">
            Live Cluster Health & Failover
          </h3>
          <p className="text-xs text-slate-500 mt-1">
            Pantau status detak jantung 8 node aktif-siaga dan log audit perpindahan peran.
          </p>
        </Link>

        <Link
          href="/products"
          className="p-6 rounded-2xl bg-white border hover:border-purple-500 hover:shadow-md transition dark:bg-slate-900 dark:border-slate-800 group"
        >
          <div className="h-10 w-10 rounded-xl bg-purple-50 text-purple-600 flex items-center justify-center mb-4 group-hover:scale-110 transition">
            <ShoppingBag className="w-5 h-5" />
          </div>
          <h3 className="font-bold text-base text-slate-900 dark:text-white group-hover:text-purple-600 transition">
            Katalog Storefront Publik
          </h3>
          <p className="text-xs text-slate-500 mt-1">
            Lihat tampilan etalase barang dari sudut pandang pembeli (customer experience).
          </p>
        </Link>
      </div>
    </div>
  );
}
