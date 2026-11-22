"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, ShoppingBag, ShieldCheck, CheckCircle2, Zap } from "lucide-react";
import { apiFetch } from "@/lib/failoverRouter";
import { formatRupiah } from "@/lib/utils";
import { useCartStore } from "@/store/useCartStore";
import { useAuthStore } from "@/store/useAuthStore";

export default function ProductDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;

  const [product, setProduct] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [quantity, setQuantity] = useState(1);
  const [added, setAdded] = useState(false);

  const { addItem } = useCartStore();
  const { token, isAuthenticated } = useAuthStore();

  useEffect(() => {
    async function fetchDetail() {
      setLoading(true);
      const res = await apiFetch(`/products/${id}`);
      if (res.success && res.data) {
        setProduct(res.data);
      }
      setLoading(false);
    }
    if (id) fetchDetail();
  }, [id]);

  const handleAddToCart = async () => {
    if (!isAuthenticated) {
      alert("Silakan login terlebih dahulu untuk berbelanja.");
      router.push("/auth/login");
      return;
    }
    const ok = await addItem(product.id, quantity, token || undefined);
    if (ok) {
      setAdded(true);
      setTimeout(() => setAdded(false), 2500);
    }
  };

  const handleBuyNow = async () => {
    if (!isAuthenticated) {
      alert("Silakan login terlebih dahulu untuk checkout.");
      router.push("/auth/login");
      return;
    }
    const ok = await addItem(product.id, quantity, token || undefined);
    if (ok) {
      router.push("/cart");
    }
  };

  if (loading) {
    return (
      <div className="container mx-auto px-4 sm:px-6 py-12">
        <div className="h-96 rounded-2xl bg-slate-200 dark:bg-slate-800 animate-pulse" />
      </div>
    );
  }

  if (!product) {
    return (
      <div className="container mx-auto px-4 sm:px-6 py-12 text-center">
        <p className="text-slate-500">Produk tidak ditemukan.</p>
        <Link href="/products" className="text-blue-600 hover:underline mt-2 inline-block">
          Kembali ke Katalog
        </Link>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 sm:px-6 py-8">
      <Link
        href="/products"
        className="inline-flex items-center gap-2 text-sm text-slate-500 hover:text-slate-800 mb-6 transition"
      >
        <ArrowLeft className="w-4 h-4" /> Kembali ke Katalog
      </Link>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 bg-white rounded-3xl border p-6 sm:p-10 shadow-sm dark:bg-slate-900 dark:border-slate-800">
        {/* Gambar Produk */}
        <div className="aspect-square rounded-2xl overflow-hidden bg-slate-100 dark:bg-slate-800 relative">
          <img
            src={product.image_url || "/images/placeholder.webp"}
            alt={product.name}
            className="w-full h-full object-cover"
          />
          <div className="absolute top-4 left-4 px-3 py-1 rounded-full bg-black/60 backdrop-blur text-white text-xs font-semibold">
            SKU: {product.sku}
          </div>
        </div>

        {/* Info & Aksi Pembelian */}
        <div className="flex flex-col justify-between space-y-6">
          <div className="space-y-4">
            <span className="text-xs font-bold text-blue-600 uppercase tracking-wider">
              {product.category_name || "Elektronik"}
            </span>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white">
              {product.name}
            </h1>
            <div className="text-3xl font-black text-blue-600 dark:text-blue-400">
              {formatRupiah(product.price)}
            </div>

            <div className="pt-2 flex items-center gap-3">
              <span
                className={`px-3 py-1 rounded-full text-xs font-bold ${
                  product.stock > 0
                    ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                    : "bg-red-50 text-red-600 border border-red-200"
                }`}
              >
                {product.stock > 0 ? `Tersedia: ${product.stock} Unit` : "Stok Habis"}
              </span>
              <span className="text-xs text-slate-400">
                Optimistic Locking v{product.version || 1}
              </span>
            </div>

            <div className="pt-4 border-t dark:border-slate-800">
              <h3 className="font-bold text-sm text-slate-900 dark:text-white mb-2">Deskripsi Produk</h3>
              <p className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed whitespace-pre-line">
                {product.description || "Spesifikasi standar produk berkualitas tinggi siap kirim."}
              </p>
            </div>
          </div>

          <div className="space-y-4 pt-6 border-t dark:border-slate-800">
            {product.stock > 0 && (
              <div className="flex items-center gap-4">
                <span className="text-sm font-medium text-slate-700 dark:text-slate-300">Kuantitas:</span>
                <div className="flex items-center border rounded-xl bg-slate-50 dark:bg-slate-800 dark:border-slate-700">
                  <button
                    onClick={() => setQuantity((q) => Math.max(1, q - 1))}
                    className="px-3 py-1 text-base font-bold text-slate-600 hover:text-black transition"
                  >
                    -
                  </button>
                  <span className="px-4 py-1 text-sm font-bold">{quantity}</span>
                  <button
                    onClick={() => setQuantity((q) => Math.min(product.stock, q + 1))}
                    className="px-3 py-1 text-base font-bold text-slate-600 hover:text-black transition"
                  >
                    +
                  </button>
                </div>
                <span className="text-xs text-slate-400">Maks. {product.stock} unit</span>
              </div>
            )}

            <div className="flex flex-col sm:flex-row gap-3 pt-2">
              <button
                onClick={handleAddToCart}
                disabled={product.stock <= 0}
                className={`flex-1 py-3 px-6 rounded-xl font-bold text-sm border flex items-center justify-center gap-2 transition ${
                  added
                    ? "bg-emerald-600 text-white border-emerald-600"
                    : product.stock > 0
                    ? "border-blue-600 text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-950"
                    : "border-slate-300 text-slate-400 cursor-not-allowed"
                }`}
              >
                {added ? (
                  <>
                    <CheckCircle2 className="w-4 h-4" /> Berhasil Ditambahkan
                  </>
                ) : (
                  <>
                    <ShoppingBag className="w-4 h-4" /> + Keranjang Belanja
                  </>
                )}
              </button>

              <button
                onClick={handleBuyNow}
                disabled={product.stock <= 0}
                className="flex-1 py-3 px-6 rounded-xl font-bold text-sm bg-blue-600 text-white hover:bg-blue-700 shadow-md transition disabled:bg-slate-300 disabled:cursor-not-allowed"
              >
                Beli Sekarang (Langsung Bayar)
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
