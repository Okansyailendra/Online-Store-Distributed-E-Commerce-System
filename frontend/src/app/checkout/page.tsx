"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, CheckCircle2, ShieldCheck, Zap, Truck, CreditCard, MapPin } from "lucide-react";
import { useCartStore } from "@/store/useCartStore";
import { useAuthStore } from "@/store/useAuthStore";
import { useClusterStore } from "@/store/useClusterStore";
import { formatRupiah } from "@/lib/utils";

export default function CheckoutPage() {
  const router = useRouter();
  const { items, totalAmount, clearCartLocally } = useCartStore();
  const { user, token, isAuthenticated } = useAuthStore();
  const { triggerFailoverAlert } = useClusterStore();

  const [shippingAddress, setShippingAddress] = useState("Jl. Raya Telang No. 1, Bangkalan, Madura, Jawa Timur");
  const [courier, setCourier] = useState("JNE Regular");
  const [shippingCost, setShippingCost] = useState(15000);
  const [paymentMethod, setPaymentMethod] = useState("BANK_TRANSFER");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");

  useEffect(() => {
    if (courier === "JNE Regular") setShippingCost(15000);
    else if (courier === "JNE Express") setShippingCost(20000);
    else if (courier === "SiCepat Reg") setShippingCost(14000);
  }, [courier]);

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

  if (items.length === 0) {
    return (
      <div className="container mx-auto px-4 py-16 text-center">
        <h2 className="text-xl font-bold mb-3">Keranjang Belanja Kosong</h2>
        <Link href="/products" className="px-6 py-2.5 bg-blue-600 text-white rounded-xl font-semibold text-sm">
          Jelajahi Produk
        </Link>
      </div>
    );
  }

  const grandTotal = totalAmount + shippingCost;

  const handleCheckout = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setErrorMsg("");

    // Generate Idempotency Key unik UUIDv4
    const idempotencyKey = "idemp-" + Math.random().toString(36).substring(2, 12) + "-" + Date.now();

    const payload = {
      method: "process_checkout",
      params: {
        idempotency_key: idempotencyKey,
        user_id: user?.id,
        shipping_address: shippingAddress,
        shipping_courier: courier,
        shipping_cost: shippingCost,
        payment_method: paymentMethod,
        items: items.map((it) => ({
          product_id: it.product_id,
          quantity: it.quantity,
          unit_price: it.unit_price,
        })),
      },
    };

    try {
      const res = await fetch("/api/rpc", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const json = await res.json();

      if (!json.success) {
        setErrorMsg(json.message || "Gagal memproses transaksi.");
        setIsSubmitting(false);
        return;
      }

      // Deteksi jika respon dilayani oleh Backup Node
      if (json.is_failover) {
        triggerFailoverAlert(
          "Server 1 (RPC)",
          "Node Koordinator sedang offline. Transaksi pembelian Anda dialihkan secara otomatis ke Node Cadangan (:6101) tanpa kehilangan data!"
        );
      }

      clearCartLocally();
      alert(`Transaksi Sukses!\nNomor Pesanan: ${json.data.order_number}\nStatus: ${json.data.status}`);
      router.push("/orders");
    } catch (err: any) {
      setErrorMsg("Koneksi RPC terputus atau seluruh node checkout tidak merespon: " + err.message);
      setIsSubmitting(false);
    }
  };

  return (
    <div className="container mx-auto px-4 sm:px-6 py-8">
      <Link href="/cart" className="inline-flex items-center gap-2 text-sm text-slate-500 hover:text-slate-800 mb-6">
        <ArrowLeft className="w-4 h-4" /> Kembali ke Keranjang
      </Link>

      <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white mb-2">
        Konfirmasi Checkout & Pembayaran
      </h1>
      <p className="text-sm text-slate-500 mb-8">
        Transaksi dieksekusi melalui Socket JSON-RPC 2.0 atomik dengan proteksi failover otomatis
      </p>

      {errorMsg && (
        <div className="p-4 mb-6 rounded-2xl bg-red-50 border border-red-200 text-red-700 text-sm font-medium">
          {errorMsg}
        </div>
      )}

      <form onSubmit={handleCheckout} className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-6">
          {/* Step 1: Alamat */}
          <div className="p-6 rounded-3xl bg-white border dark:bg-slate-900 dark:border-slate-800 shadow-sm space-y-4">
            <h3 className="font-bold text-base flex items-center gap-2 text-slate-900 dark:text-white">
              <MapPin className="w-5 h-5 text-blue-600" />
              1. Alamat Pengiriman
            </h3>
            <textarea
              rows={3}
              required
              value={shippingAddress}
              onChange={(e) => setShippingAddress(e.target.value)}
              className="w-full text-sm p-3.5 border rounded-2xl bg-slate-50 dark:bg-slate-800 dark:border-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Masukkan alamat lengkap tujuan pengiriman..."
            />
          </div>

          {/* Step 2: Kurir */}
          <div className="p-6 rounded-3xl bg-white border dark:bg-slate-900 dark:border-slate-800 shadow-sm space-y-4">
            <h3 className="font-bold text-base flex items-center gap-2 text-slate-900 dark:text-white">
              <Truck className="w-5 h-5 text-blue-600" />
              2. Opsi Ekspedisi Kurir
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              {[
                { name: "JNE Regular", cost: 15000, eta: "2-3 Hari" },
                { name: "JNE Express", cost: 20000, eta: "1 Hari" },
                { name: "SiCepat Reg", cost: 14000, eta: "2-3 Hari" },
              ].map((c) => (
                <div
                  key={c.name}
                  onClick={() => setCourier(c.name)}
                  className={`p-4 rounded-2xl border cursor-pointer transition ${
                    courier === c.name
                      ? "border-blue-600 bg-blue-50/50 dark:bg-blue-950/40"
                      : "hover:border-slate-300 dark:border-slate-800"
                  }`}
                >
                  <div className="font-bold text-sm text-slate-900 dark:text-white">{c.name}</div>
                  <div className="text-xs text-slate-400 mt-0.5">{c.eta}</div>
                  <div className="font-extrabold text-blue-600 text-sm mt-2">{formatRupiah(c.cost)}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Step 3: Metode Pembayaran */}
          <div className="p-6 rounded-3xl bg-white border dark:bg-slate-900 dark:border-slate-800 shadow-sm space-y-4">
            <h3 className="font-bold text-base flex items-center gap-2 text-slate-900 dark:text-white">
              <CreditCard className="w-5 h-5 text-blue-600" />
              3. Metode Pembayaran
            </h3>
            <div className="space-y-2.5">
              {[
                { id: "BANK_TRANSFER", title: "Transfer Bank (Virtual Account Otomatis)" },
                { id: "E_WALLET", title: "QRIS / Dompet Digital (Gopay/OVO/Dana)" },
                { id: "COD", title: "Cash on Delivery (Bayar di Tempat)" },
              ].map((m) => (
                <label
                  key={m.id}
                  className={`flex items-center gap-3 p-3.5 rounded-2xl border cursor-pointer transition ${
                    paymentMethod === m.id
                      ? "border-blue-600 bg-blue-50/50 dark:bg-blue-950/40"
                      : "dark:border-slate-800"
                  }`}
                >
                  <input
                    type="radio"
                    name="paymentMethod"
                    value={m.id}
                    checked={paymentMethod === m.id}
                    onChange={(e) => setPaymentMethod(e.target.value)}
                    className="w-4 h-4 text-blue-600"
                  />
                  <span className="text-sm font-semibold text-slate-800 dark:text-slate-200">{m.title}</span>
                </label>
              ))}
            </div>
          </div>
        </div>

        {/* Ringkasan & Submit */}
        <div className="lg:col-span-1">
          <div className="p-6 rounded-3xl bg-white border dark:bg-slate-900 dark:border-slate-800 shadow-sm space-y-6 sticky top-24">
            <h3 className="font-bold text-base text-slate-900 dark:text-white">Rincian Pembayaran</h3>

            <div className="space-y-3 text-sm">
              <div className="flex justify-between text-slate-500">
                <span>Subtotal Barang</span>
                <span className="font-semibold text-slate-800 dark:text-slate-200">{formatRupiah(totalAmount)}</span>
              </div>
              <div className="flex justify-between text-slate-500">
                <span>Ongkos Kirim ({courier})</span>
                <span className="font-semibold text-slate-800 dark:text-slate-200">{formatRupiah(shippingCost)}</span>
              </div>
              <div className="border-t pt-3 flex justify-between font-extrabold text-base text-slate-900 dark:text-white">
                <span>Total Tagihan</span>
                <span className="text-blue-600">{formatRupiah(grandTotal)}</span>
              </div>
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full py-3.5 px-6 rounded-xl bg-blue-600 text-white font-bold text-sm hover:bg-blue-700 shadow-lg shadow-blue-500/20 transition flex items-center justify-center gap-2 disabled:bg-slate-400"
            >
              {isSubmitting ? "Memproses Transaksi RPC..." : "Konfirmasi & Bayar Sekarang"}
            </button>

            <div className="text-[11px] text-slate-400 text-center leading-relaxed flex items-center justify-center gap-1.5">
              <ShieldCheck className="w-4 h-4 text-emerald-500 shrink-0" />
              Idempotensi aktif: Transaksi tidak akan terproses ganda saat terjadi failover.
            </div>
          </div>
        </div>
      </form>
    </div>
  );
}
