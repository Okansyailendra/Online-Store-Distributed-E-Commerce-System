"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowRight, ShoppingBag, ShieldCheck, Zap, Server, CheckCircle2 } from "lucide-react";
import { apiFetch } from "@/lib/failoverRouter";
import { formatRupiah } from "@/lib/utils";
import { useCartStore } from "@/store/useCartStore";
import { useAuthStore } from "@/store/useAuthStore";

export default function HomePage() {
  const [categories, setCategories] = useState<any[]>([]);
  const [products, setProducts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const { addItem } = useCartStore();
  const { token, isAuthenticated } = useAuthStore();
  const [addedId, setAddedId] = useState<string | null>(null);

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      const [catRes, prodRes] = await Promise.all([
        apiFetch("/categories"),
        apiFetch("/products?limit=8"),
      ]);

      if (catRes.success && catRes.data) setCategories(catRes.data);
      if (prodRes.success && prodRes.data) setProducts(prodRes.data);
      setLoading(false);
    }
    loadData();
  }, []);

  const handleAddToCart = async (productId: string) => {
    if (!isAuthenticated) {
      alert("Silakan masuk/login terlebih dahulu untuk berbelanja.");
      return;
    }
    const ok = await addItem(productId, 1, token || undefined);
    if (ok) {
      setAddedId(productId);
      setTimeout(() => setAddedId(null), 2000);
    }
  };

  return (
    <div className="space-y-16 py-8">
      {/* Hero Banner */}
      <section className="container mx-auto px-4 sm:px-6">
        <div className="relative rounded-3xl overflow-hidden bg-gradient-to-br from-slate-900 via-blue-950 to-indigo-950 text-white p-8 sm:p-14 shadow-2xl border border-slate-800">
          <div className="max-w-2xl space-y-6 relative z-10">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/20 border border-blue-400/30 text-blue-300 text-xs font-semibold">
              <Zap className="w-3.5 h-3.5 text-blue-400" />
              Sistem Terdistribusi Ketersediaan Tinggi (High Availability)
            </div>
            <h1 className="text-3xl sm:text-5xl font-extrabold tracking-tight leading-tight">
              Platform Belanja Digital dengan Ketahanan Mandiri.
            </h1>
            <p className="text-slate-300 text-sm sm:text-base leading-relaxed">
              Didukung arsitektur multi-protokol (RPC, RMI, REST) dan redundansi Koordinator-Pengikut. Transaksi Anda dijamin aman tanpa risiko server crash atau kehilangan data.
            </p>
            <div className="flex flex-wrap items-center gap-4 pt-2">
              <Link
                href="/products"
                className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-blue-600 text-white font-semibold hover:bg-blue-700 shadow-lg shadow-blue-500/30 transition"
              >
                Mulai Belanja
                <ArrowRight className="w-4 h-4" />
              </Link>
              <Link
                href="/admin/cluster"
                className="inline-flex items-center gap-2 px-5 py-3 rounded-xl bg-slate-800/80 text-slate-200 font-semibold border border-slate-700 hover:bg-slate-800 transition"
              >
                <Server className="w-4 h-4 text-emerald-400" />
                Live Cluster Monitor
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Keunggulan Sistem Terdistribusi */}
      <section className="container mx-auto px-4 sm:px-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="p-6 rounded-2xl bg-white border shadow-sm dark:bg-slate-900 dark:border-slate-800 flex items-start gap-4">
            <div className="h-12 w-12 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center shrink-0 dark:bg-blue-900/30 dark:text-blue-400">
              <Zap className="w-6 h-6" />
            </div>
            <div>
              <h3 className="font-bold text-slate-900 dark:text-white">Zero Single Point of Failure</h3>
              <p className="text-xs text-slate-500 mt-1 leading-relaxed">
                Setiap layanan didampingi oleh node cadangan siaga (hot-standby). Jika node utama mati, sistem otomatis failover dalam 5 detik.
              </p>
            </div>
          </div>

          <div className="p-6 rounded-2xl bg-white border shadow-sm dark:bg-slate-900 dark:border-slate-800 flex items-start gap-4">
            <div className="h-12 w-12 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center shrink-0 dark:bg-emerald-900/30 dark:text-emerald-400">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <div>
              <h3 className="font-bold text-slate-900 dark:text-white">Anti-Overselling Guarantee</h3>
              <p className="text-xs text-slate-500 mt-1 leading-relaxed">
                Manajemen stok via RMI dengan Optimistic Concurrency Control (OCC) mencegah perebutan stok saat banyak pembeli checkout bersamaan.
              </p>
            </div>
          </div>

          <div className="p-6 rounded-2xl bg-white border shadow-sm dark:bg-slate-900 dark:border-slate-800 flex items-start gap-4">
            <div className="h-12 w-12 rounded-xl bg-purple-50 text-purple-600 flex items-center justify-center shrink-0 dark:bg-purple-900/30 dark:text-purple-400">
              <Server className="w-6 h-6" />
            </div>
            <div>
              <h3 className="font-bold text-slate-900 dark:text-white">Replikasi Data Real-Time</h3>
              <p className="text-xs text-slate-500 mt-1 leading-relaxed">
                Setiap mutasi transaksi direplikasi secara semi-synchronous ke database pengikut untuk jaminan Recovery Point Objective (RPO) = 0.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Kategori Pilihan */}
      {categories.length > 0 && (
        <section className="container mx-auto px-4 sm:px-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-xl sm:text-2xl font-bold text-slate-900 dark:text-white">Kategori Pilihan</h2>
              <p className="text-xs text-slate-500 mt-0.5">Jelajahi produk berdasarkan klasifikasi</p>
            </div>
            <Link href="/products" className="text-sm font-semibold text-blue-600 hover:underline flex items-center gap-1">
              Lihat Semua <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            {categories.map((cat) => (
              <Link
                key={cat.id}
                href={`/products?category=${cat.slug}`}
                className="group p-5 rounded-2xl bg-white border hover:border-blue-500/50 hover:shadow-md transition text-center dark:bg-slate-900 dark:border-slate-800"
              >
                <div className="font-bold text-sm text-slate-800 group-hover:text-blue-600 transition dark:text-slate-200">
                  {cat.name}
                </div>
                <p className="text-[11px] text-slate-400 mt-1 line-clamp-1">{cat.description}</p>
              </Link>
            ))}
          </div>
        </section>
      )}

      {/* Produk Unggulan */}
      <section className="container mx-auto px-4 sm:px-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-xl sm:text-2xl font-bold text-slate-900 dark:text-white">Produk Unggulan</h2>
            <p className="text-xs text-slate-500 mt-0.5">Produk berkualitas siap checkout instan via RPC</p>
          </div>
          <Link href="/products" className="text-sm font-semibold text-blue-600 hover:underline flex items-center gap-1">
            Lihat Semua Produk <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        {loading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-80 rounded-2xl bg-slate-200 dark:bg-slate-800 animate-pulse" />
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {products.map((prod) => (
              <div
                key={prod.id}
                className="group flex flex-col justify-between rounded-2xl bg-white border p-4 shadow-sm hover:shadow-md transition dark:bg-slate-900 dark:border-slate-800"
              >
                <div className="space-y-3">
                  <div className="relative aspect-square w-full rounded-xl overflow-hidden bg-slate-100 dark:bg-slate-800">
                    <img
                      src={prod.image_url || "/images/placeholder.webp"}
                      alt={prod.name}
                      className="h-full w-full object-cover group-hover:scale-105 transition duration-300"
                    />
                    <div className="absolute top-2 left-2 px-2 py-0.5 rounded-md bg-black/60 backdrop-blur text-white text-[10px] font-semibold">
                      {prod.category_name || "Produk"}
                    </div>
                  </div>

                  <div>
                    <Link href={`/products/${prod.id}`}>
                      <h3 className="font-bold text-sm text-slate-900 hover:text-blue-600 transition dark:text-white line-clamp-2">
                        {prod.name}
                      </h3>
                    </Link>
                    <div className="mt-1 font-extrabold text-blue-600 dark:text-blue-400">
                      {formatRupiah(prod.price)}
                    </div>
                  </div>
                </div>

                <div className="pt-4 mt-3 border-t flex items-center justify-between dark:border-slate-800">
                  <span
                    className={`text-xs font-semibold ${
                      prod.stock > 0 ? "text-emerald-600 dark:text-emerald-400" : "text-red-500"
                    }`}
                  >
                    {prod.stock > 0 ? `Stok: ${prod.stock} unit` : "Stok Habis"}
                  </span>

                  <button
                    onClick={() => handleAddToCart(prod.id)}
                    disabled={prod.stock <= 0}
                    className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition flex items-center gap-1.5 ${
                      addedId === prod.id
                        ? "bg-emerald-600 text-white"
                        : prod.stock > 0
                        ? "bg-blue-600 hover:bg-blue-700 text-white shadow"
                        : "bg-slate-200 text-slate-400 cursor-not-allowed dark:bg-slate-800"
                    }`}
                  >
                    {addedId === prod.id ? (
                      <>
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        Ditambahkan
                      </>
                    ) : (
                      <>
                        <ShoppingBag className="w-3.5 h-3.5" />
                        + Keranjang
                      </>
                    )}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
