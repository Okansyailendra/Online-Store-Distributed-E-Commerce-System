"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Lock, Mail, ArrowRight, ShieldCheck } from "lucide-react";
import { apiFetch } from "@/lib/failoverRouter";
import { useAuthStore } from "@/store/useAuthStore";

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuthStore();
  const [email, setEmail] = useState("budi@sister.com");
  const [password, setPassword] = useState("BudiPass123!");
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setErrorMsg("");

    const res = await apiFetch("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });

    if (res.success && res.data) {
      login(res.data.access_token, res.data.user);
      if (res.data.user.role === "ADMIN") {
        router.push("/admin/cluster");
      } else {
        router.push("/products");
      }
    } else {
      setErrorMsg(res.message || "Email atau kata sandi tidak cocok.");
    }
    setLoading(false);
  };

  return (
    <div className="container mx-auto px-4 py-16 flex items-center justify-center">
      <div className="max-w-md w-full p-8 rounded-3xl bg-white border dark:bg-slate-900 dark:border-slate-800 shadow-xl space-y-6">
        <div className="text-center space-y-1">
          <div className="h-12 w-12 rounded-2xl bg-blue-600 text-white flex items-center justify-center mx-auto font-black text-2xl shadow-md mb-3">
            S
          </div>
          <h1 className="text-2xl font-extrabold text-slate-900 dark:text-white">Masuk ke SisterShop</h1>
          <p className="text-xs text-slate-500">Gunakan akun demo atau akun yang telah didaftarkan</p>
        </div>

        {errorMsg && (
          <div className="p-3 rounded-xl bg-red-50 border border-red-200 text-red-600 text-xs font-semibold">
            {errorMsg}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">Email</label>
            <div className="relative">
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full text-sm pl-9 pr-3.5 py-2.5 border rounded-xl bg-slate-50 dark:bg-slate-800 dark:border-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="nama@email.com"
              />
              <Mail className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">Kata Sandi</label>
            <div className="relative">
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full text-sm pl-9 pr-3.5 py-2.5 border rounded-xl bg-slate-50 dark:bg-slate-800 dark:border-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="••••••••"
              />
              <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 px-4 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-bold text-sm shadow-md transition flex items-center justify-center gap-2"
          >
            {loading ? "Memverifikasi Sesi..." : "Masuk Sekarang"}
            <ArrowRight className="w-4 h-4" />
          </button>
        </form>

        <div className="pt-4 border-t dark:border-slate-800 space-y-3">
          <div className="text-xs text-slate-500 text-center">
            Pilihan Akun Cepat Demo:
          </div>
          <div className="flex gap-2 text-xs">
            <button
              type="button"
              onClick={() => {
                setEmail("budi@sister.com");
                setPassword("BudiPass123!");
              }}
              className="flex-1 p-2 rounded-lg border bg-slate-50 hover:bg-slate-100 font-semibold text-slate-700 dark:bg-slate-800 dark:text-slate-200"
            >
              Customer (Budi)
            </button>
            <button
              type="button"
              onClick={() => {
                setEmail("admin@sister.com");
                setPassword("AdminPass123!");
              }}
              className="flex-1 p-2 rounded-lg border bg-purple-50 text-purple-700 hover:bg-purple-100 font-semibold"
            >
              Admin Toko
            </button>
          </div>

          <div className="text-xs text-center text-slate-500 pt-2">
            Belum punya akun?{" "}
            <Link href="/auth/register" className="font-bold text-blue-600 hover:underline">
              Daftar di sini
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
