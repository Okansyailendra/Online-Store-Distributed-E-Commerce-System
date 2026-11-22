"use client";

import { useEffect } from "react";
import { Zap, X, ShieldAlert } from "lucide-react";
import { useClusterStore } from "@/store/useClusterStore";

export default function FailoverToast() {
  const { failoverAlert, dismissFailoverAlert } = useClusterStore();

  useEffect(() => {
    if (failoverAlert?.show) {
      const timer = setTimeout(() => {
        dismissFailoverAlert();
      }, 7000);
      return () => clearTimeout(timer);
    }
  }, [failoverAlert, dismissFailoverAlert]);

  if (!failoverAlert?.show) return null;

  return (
    <div className="fixed bottom-6 right-6 z-50 max-w-md w-full animate-in slide-in-from-bottom-5 duration-300">
      <div className="bg-slate-900 text-white rounded-xl shadow-2xl border border-purple-500/30 p-4 flex items-start gap-3.5 backdrop-blur-md">
        <div className="h-9 w-9 rounded-lg bg-purple-600/20 text-purple-400 flex items-center justify-center shrink-0 border border-purple-500/30">
          <Zap className="w-5 h-5 text-purple-400 animate-bounce" />
        </div>
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <span className="font-bold text-sm text-purple-300">
              Toleransi Kesalahan Sistem Aktif
            </span>
            <span className="text-[10px] px-1.5 py-0.5 rounded bg-purple-900/60 text-purple-200 border border-purple-700/50">
              Failover Transparan
            </span>
          </div>
          <p className="text-xs text-slate-300 mt-1 leading-relaxed">
            {failoverAlert.message ||
              "Koneksi utama mengalami gangguan. Sistem secara transparan mengalihkan rute transaksi ke Node Cadangan tanpa memutus proses belanja Anda."}
          </p>
        </div>
        <button
          onClick={dismissFailoverAlert}
          className="text-slate-400 hover:text-white transition p-1"
        >
          <X className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
