"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowLeft, Package, Plus, CheckCircle2, AlertCircle } from "lucide-react";
import { apiFetch } from "@/lib/failoverRouter";
import { useAuthStore } from "@/store/useAuthStore";
import { formatRupiah } from "@/lib/utils";

export default function AdminInventoryPage() {
  const { token, user } = useAuthStore();
  const [products, setProducts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedProduct, setSelectedProduct] = useState<string>("");
  const [addQty, setAddQty] = useState<number>(10);
  const [submitting, setSubmitting] = useState(false);
  const [statusMsg, setStatusMsg] = useState("");

  const loadProducts = async () => {
    setLoading(true);
    const res = await apiFetch("/products?limit=50");
    if (res.success && res.data) {
      setProducts(res.data);
      if (res.data.length > 0 && !selectedProduct) {
        setSelectedProduct(res.data[0].id);
      }
    }
    setLoading(false);
  };

  useEffect(() => {
    loadProducts();
  }, []);

  const handleRestock = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token) return;
    setSubmitting(true);
    setStatusMsg("");

    const res = await apiFetch("/admin/inventory/restock", {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
      body: JSON.stringify({
        product_id: selectedProduct,
        quantity: addQty,
      }),
    });

    if (res.success) {
      setStatusMsg(`Stok berhasil ditambahkan via RMI! (Stok Baru: ${res.data?.data?.new_stock || "Terupdate"})`);
      await loadProducts();
    } else {
      setStatusMsg("Gagal menambah stok via RMI: " + (res.message || "Error"));
    }
    setSubmitting(false);
  };

  return (
    <div className="container mx-auto px-4 sm:px-6 py-8 space-y-8">
      <div>
        <Link href="/admin" className="inline-flex items-center gap-2 text-xs text-slate-500 hover:text-slate-800 mb-2">
          <ArrowLeft className="w-3.5 h-3.5" /> Kembali ke Portal Admin
        </Link>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white">
          Manajemen Stok Real-Time (RMI)
        </h1>
        <p className="text-xs sm:text-sm text-slate-500 mt-1">
          Penyesuaian persediaan fisik barang dieksekusi melalui Remote Method Invocation pada Node Server 2
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Form Tambah Stok RMI */}
        <div className="lg:col-span-1">
          <div className="p-6 rounded-3xl bg-white border dark:bg-slate-900 dark:border-slate-800 shadow-sm space-y-4">
            <h3 className="font-bold text-base text-slate-900 dark:text-white flex items-center gap-2">
              <Package className="w-5 h-5 text-blue-600" />
              Restock Barang (RMI Invocation)
            </h3>

            {statusMsg && (
              <div className="p-3 rounded-xl bg-blue-50 border border-blue-200 text-blue-700 text-xs font-semibold">
                {statusMsg}
              </div>
            )}

            <form onSubmit={handleRestock} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                  Pilih Produk
                </label>
                <select
                  value={selectedProduct}
                  onChange={(e) => setSelectedProduct(e.target.value)}
                  className="w-full text-xs sm:text-sm p-2.5 border rounded-xl bg-slate-50 dark:bg-slate-800 dark:border-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {products.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.name} (Sisa: {p.stock})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                  Jumlah Tambahan Kuantitas
                </label>
                <input
                  type="number"
                  min={1}
                  required
                  value={addQty}
                  onChange={(e) => setAddQty(parseInt(e.target.value, 10))}
                  className="w-full text-xs sm:text-sm p-2.5 border rounded-xl bg-slate-50 dark:bg-slate-800 dark:border-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <button
                type="submit"
                disabled={submitting}
                className="w-full py-3 px-4 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-bold text-sm shadow transition flex items-center justify-center gap-2"
              >
                {submitting ? "Memanggil Remote Method RMI..." : "+ Tambah Stok Fisik"}
              </button>
            </form>
          </div>
        </div>

        {/* Tabel Stok Aktual & Version OCC */}
        <div className="lg:col-span-2">
          <div className="rounded-3xl bg-white border dark:bg-slate-900 dark:border-slate-800 shadow-sm overflow-hidden">
            <div className="p-5 border-b dark:border-slate-800 flex items-center justify-between">
              <h3 className="font-bold text-base text-slate-900 dark:text-white">
                Daftar Persediaan & Versi OCC
              </h3>
              <span className="text-xs text-slate-400">Total {products.length} Produk</span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 dark:bg-slate-800/50 border-b dark:border-slate-800 text-slate-500 font-bold">
                  <tr>
                    <th className="p-3.5">Nama Produk</th>
                    <th className="p-3.5">SKU</th>
                    <th className="p-3.5">Harga</th>
                    <th className="p-3.5">Stok Fisik</th>
                    <th className="p-3.5">Versi OCC</th>
                  </tr>
                </thead>
                <tbody className="divide-y dark:divide-slate-800">
                  {products.map((p) => (
                    <tr key={p.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/30">
                      <td className="p-3.5 font-bold text-slate-900 dark:text-white">{p.name}</td>
                      <td className="p-3.5 text-slate-500 font-mono">{p.sku}</td>
                      <td className="p-3.5 font-bold text-blue-600">{formatRupiah(p.price)}</td>
                      <td className="p-3.5">
                        <span
                          className={`font-black ${
                            p.stock < 5 ? "text-amber-600" : "text-emerald-600"
                          }`}
                        >
                          {p.stock} Unit
                        </span>
                      </td>
                      <td className="p-3.5 font-mono text-slate-400">v{p.version || 1}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
