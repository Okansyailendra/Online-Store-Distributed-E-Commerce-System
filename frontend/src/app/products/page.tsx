"use client";

import { useEffect, useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { Search, Filter, ShoppingBag, CheckCircle2 } from "lucide-react";
import { apiFetch } from "@/lib/failoverRouter";
import { formatRupiah } from "@/lib/utils";
import { useCartStore } from "@/store/useCartStore";
import { useAuthStore } from "@/store/useAuthStore";

function ProductsContent() {
  const searchParams = useSearchParams();
  const initialCategory = searchParams.get("category") || "";
  const initialQuery = searchParams.get("q") || "";

  const [products, setProducts] = useState<any[]>([]);
  const [categories, setCategories] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const [selectedCategory, setSelectedCategory] = useState(initialCategory);
  const [searchQuery, setSearchQuery] = useState(initialQuery);
  const [sort, setSort] = useState("newest");

  const { addItem } = useCartStore();
  const { token, isAuthenticated } = useAuthStore();
  const [addedId, setAddedId] = useState<string | null>(null);

  useEffect(() => {
    async function fetchCategories() {
      const res = await apiFetch("/categories");
      if (res.success && res.data) setCategories(res.data);
    }
    fetchCategories();
  }, []);

  useEffect(() => {
    async function fetchProducts() {
      setLoading(true);
      const params = new URLSearchParams();
      if (selectedCategory) params.set("category", selectedCategory);
      if (searchQuery) params.set("q", searchQuery);
      if (sort) params.set("sort", sort);
      params.set("limit", "24");

      const res = await apiFetch(`/products?${params.toString()}`);
      if (res.success && res.data) {
        setProducts(res.data);
      }
      setLoading(false);
    }
    fetchProducts();
  }, [selectedCategory, searchQuery, sort]);

  const handleAddToCart = async (productId: string) => {
    if (!isAuthenticated) {
      alert("Silakan masuk/login terlebih dahulu untuk menambahkan barang ke keranjang.");
      return;
    }
    const ok = await addItem(productId, 1, token || undefined);
    if (ok) {
      setAddedId(productId);
      setTimeout(() => setAddedId(null), 2000);
    }
  };

  return (
    <div className="container mx-auto px-4 sm:px-6 py-8">
      <div className="flex flex-col md:flex-row items-start justify-between gap-4 mb-8">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white">
            Katalog Produk
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Menampilkan seluruh produk yang tersedia di ekosistem SisterShop
          </p>
        </div>

        {/* Search & Sort Controls */}
        <div className="flex flex-wrap items-center gap-3 w-full md:w-auto">
          <div className="relative flex-1 md:w-64">
            <input
              type="text"
              placeholder="Cari produk..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full text-xs sm:text-sm pl-8 pr-3 py-2 border rounded-xl bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-slate-900 dark:border-slate-800"
            />
            <Search className="w-4 h-4 text-slate-400 absolute left-2.5 top-2.5" />
          </div>

          <select
            value={sort}
            onChange={(e) => setSort(e.target.value)}
            className="text-xs sm:text-sm px-3 py-2 border rounded-xl bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-slate-900 dark:border-slate-800"
          >
            <option value="newest">Terbaru</option>
            <option value="price_asc">Harga Terendah</option>
            <option value="price_desc">Harga Tertinggi</option>
            <option value="name_asc">Nama (A-Z)</option>
          </select>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
        {/* Sidebar Kategori */}
        <div className="lg:col-span-1 space-y-4">
          <div className="p-5 rounded-2xl bg-white border dark:bg-slate-900 dark:border-slate-800 shadow-sm">
            <h3 className="font-bold text-sm text-slate-900 dark:text-white mb-3 flex items-center gap-2">
              <Filter className="w-4 h-4 text-blue-600" />
              Filter Kategori
            </h3>
            <div className="space-y-1.5">
              <button
                onClick={() => setSelectedCategory("")}
                className={`w-full text-left px-3 py-2 rounded-xl text-xs font-semibold transition ${
                  selectedCategory === ""
                    ? "bg-blue-600 text-white"
                    : "text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
                }`}
              >
                Semua Kategori
              </button>
              {categories.map((c) => (
                <button
                  key={c.id}
                  onClick={() => setSelectedCategory(c.slug)}
                  className={`w-full text-left px-3 py-2 rounded-xl text-xs font-semibold transition ${
                    selectedCategory === c.slug
                      ? "bg-blue-600 text-white"
                      : "text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
                  }`}
                >
                  {c.name}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Product Grid */}
        <div className="lg:col-span-3">
          {loading ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-6">
              {[...Array(6)].map((_, i) => (
                <div key={i} className="h-80 rounded-2xl bg-slate-200 dark:bg-slate-800 animate-pulse" />
              ))}
            </div>
          ) : products.length === 0 ? (
            <div className="p-12 text-center rounded-2xl bg-white border dark:bg-slate-900 dark:border-slate-800">
              <p className="text-slate-500 text-sm">Tidak ada produk yang cocok dengan pencarian Anda.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-6">
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
        </div>
      </div>
    </div>
  );
}

export default function ProductsPage() {
  return (
    <Suspense fallback={<div className="container mx-auto p-12 text-center text-slate-400">Memuat katalog...</div>}>
      <ProductsContent />
    </Suspense>
  );
}
