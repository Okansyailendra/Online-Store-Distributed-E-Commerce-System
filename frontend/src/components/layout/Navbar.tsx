"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { ShoppingCart, ShieldCheck, Activity, User, LogOut, Package, Search } from "lucide-react";
import { useCartStore } from "@/store/useCartStore";
import { useAuthStore } from "@/store/useAuthStore";
import { useRouter } from "next/navigation";

export default function Navbar() {
  const router = useRouter();
  const { totalItems, fetchCart } = useCartStore();
  const { user, token, isAuthenticated, logout, initAuth } = useAuthStore();
  const [searchQuery, setSearchQuery] = useState("");

  useEffect(() => {
    initAuth();
  }, [initAuth]);

  useEffect(() => {
    if (token) {
      fetchCart(token);
    }
  }, [token, fetchCart]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      router.push(`/products?q=${encodeURIComponent(searchQuery.trim())}`);
    }
  };

  return (
    <header className="sticky top-0 z-40 w-full border-b bg-white/95 backdrop-blur shadow-sm dark:bg-slate-900/95 dark:border-slate-800">
      <div className="container mx-auto flex h-16 items-center justify-between px-4 sm:px-6">
        {/* Brand Logo */}
        <div className="flex items-center gap-6">
          <Link href="/" className="flex items-center gap-2 group">
            <div className="h-9 w-9 rounded-lg bg-blue-600 text-white flex items-center justify-center font-bold text-xl shadow-md group-hover:bg-blue-700 transition">
              S
            </div>
            <div className="flex flex-col">
              <span className="font-extrabold text-lg tracking-tight text-slate-900 dark:text-white leading-tight">
                Sister<span className="text-blue-600">Shop</span>
              </span>
              <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-widest">
                Distributed HA
              </span>
            </div>
          </Link>

          <nav className="hidden md:flex items-center gap-5 text-sm font-medium text-slate-600 dark:text-slate-300">
            <Link href="/products" className="hover:text-blue-600 transition">
              Katalog Produk
            </Link>
            <Link href="/orders" className="hover:text-blue-600 transition">
              Pesanan Saya
            </Link>
          </nav>
        </div>

        {/* Global Search Bar */}
        <form onSubmit={handleSearch} className="hidden sm:flex items-center relative max-w-sm w-full mx-4">
          <input
            type="text"
            placeholder="Cari laptop, keyboard, buku..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full text-sm pl-9 pr-4 py-2 border rounded-full bg-slate-50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-slate-800 dark:border-slate-700 dark:text-white"
          />
          <Search className="w-4 h-4 text-slate-400 absolute left-3" />
        </form>

        {/* Action Buttons */}
        <div className="flex items-center gap-3">
          {/* Cluster Monitoring Badge */}
          <Link
            href="/admin/cluster"
            className="hidden lg:flex items-center gap-1.5 px-2.5 py-1 text-xs font-semibold rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 hover:bg-emerald-100 transition"
          >
            <Activity className="w-3.5 h-3.5 animate-pulse text-emerald-600" />
            Cluster Monitor
          </Link>

          {/* Cart Icon */}
          <Link
            href="/cart"
            className="relative p-2 rounded-full text-slate-700 hover:bg-slate-100 transition dark:text-slate-200 dark:hover:bg-slate-800"
            title="Keranjang Belanja"
          >
            <ShoppingCart className="w-5 h-5" />
            {totalItems > 0 && (
              <span className="absolute -top-1 -right-1 flex h-5 w-5 items-center justify-center rounded-full bg-blue-600 text-[11px] font-bold text-white shadow">
                {totalItems > 99 ? "99+" : totalItems}
              </span>
            )}
          </Link>

          {/* Auth State */}
          {isAuthenticated ? (
            <div className="flex items-center gap-2">
              {user?.role === "ADMIN" && (
                <Link
                  href="/admin"
                  className="hidden sm:flex items-center gap-1 px-3 py-1.5 text-xs font-semibold rounded-md bg-purple-600 text-white hover:bg-purple-700 transition"
                >
                  <ShieldCheck className="w-3.5 h-3.5" />
                  Admin
                </Link>
              )}
              <div className="flex items-center gap-2 pl-2 border-l dark:border-slate-800">
                <span className="text-sm font-medium text-slate-700 hidden sm:inline dark:text-slate-300">
                  {user?.full_name?.split(" ")[0]}
                </span>
                <button
                  onClick={() => {
                    logout();
                    router.push("/auth/login");
                  }}
                  className="p-1.5 text-slate-500 hover:text-red-600 rounded hover:bg-slate-100 transition dark:hover:bg-slate-800"
                  title="Keluar"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </div>
            </div>
          ) : (
            <div className="flex items-center gap-2">
              <Link
                href="/auth/login"
                className="px-3.5 py-1.5 text-sm font-medium text-slate-700 hover:text-blue-600 transition dark:text-slate-200"
              >
                Masuk
              </Link>
              <Link
                href="/auth/register"
                className="px-3.5 py-1.5 text-sm font-medium bg-blue-600 text-white rounded-lg hover:bg-blue-700 shadow-sm transition"
              >
                Daftar
              </Link>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
