"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Server, Activity, ShieldAlert, RefreshCw, Radio, CheckCircle2, AlertTriangle, ArrowLeft } from "lucide-react";
import { apiFetch } from "@/lib/failoverRouter";
import { formatDate } from "@/lib/utils";

export default function ClusterMonitorPage() {
  const [clusterData, setClusterData] = useState<any>(null);
  const [failoverLogs, setFailoverLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const loadData = async () => {
    setRefreshing(true);
    const [statusRes, logsRes] = await Promise.all([
      apiFetch("/cluster/status"),
      apiFetch("/cluster/logs"),
    ]);

    if (statusRes.success) setClusterData(statusRes);
    if (logsRes.success && logsRes.data) setFailoverLogs(logsRes.data);
    setLoading(false);
    setRefreshing(false);
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 3000); // Poll setiap 3 detik untuk deteksi real-time
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="container mx-auto px-4 sm:px-6 py-8 space-y-8">
      {/* Header Panel */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <Link href="/" className="inline-flex items-center gap-2 text-xs text-slate-500 hover:text-slate-800 mb-2">
            <ArrowLeft className="w-3.5 h-3.5" /> Kembali ke Storefront
          </Link>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white">
              Cluster & Failover Monitoring
            </h1>
            <span className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-blue-50 text-blue-700 border border-blue-200">
              <Radio className="w-3.5 h-3.5 text-blue-600 animate-pulse" />
              Live Heartbeat (2.0s)
            </span>
          </div>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Visualisasi topologi 8 node terdistribusi, detak jantung koordinator, dan audit promosi otomatis.
          </p>
        </div>

        <button
          onClick={loadData}
          disabled={refreshing}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold bg-white border hover:bg-slate-50 shadow-sm transition self-start md:self-auto"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? "animate-spin" : ""}`} />
          Perbarui Status
        </button>
      </div>

      {/* Ringkasan Status Cluster */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="p-5 rounded-2xl bg-white border dark:bg-slate-900 dark:border-slate-800 shadow-sm">
          <div className="text-xs text-slate-400 font-semibold uppercase">Status Ketersediaan</div>
          <div className="text-lg font-black mt-1 flex items-center gap-2">
            {clusterData?.cluster_healthy ? (
              <>
                <CheckCircle2 className="w-5 h-5 text-emerald-500" />
                <span className="text-emerald-600">CLUSTER SEHAT (HA OK)</span>
              </>
            ) : (
              <>
                <AlertTriangle className="w-5 h-5 text-amber-500" />
                <span className="text-amber-600">DEGRADED / CRASH TEST</span>
              </>
            )}
          </div>
        </div>

        <div className="p-5 rounded-2xl bg-white border dark:bg-slate-900 dark:border-slate-800 shadow-sm">
          <div className="text-xs text-slate-400 font-semibold uppercase">Parameter Detak Jantung</div>
          <div className="text-lg font-black text-slate-800 dark:text-slate-200 mt-1">
            Thb = 2.0s • Timeout = 5.0s (3 Misses)
          </div>
        </div>

        <div className="p-5 rounded-2xl bg-white border dark:bg-slate-900 dark:border-slate-800 shadow-sm">
          <div className="text-xs text-slate-400 font-semibold uppercase">Insiden Failover</div>
          <div className="text-lg font-black text-purple-600 mt-1">
            {failoverLogs.length} Peristiwa Tercatat
          </div>
        </div>
      </div>

      {/* Matriks 8 Node Terdistribusi */}
      <div className="space-y-4">
        <h2 className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
          <Server className="w-5 h-5 text-blue-600" />
          Matriks Status Node (Coordinator vs Follower)
        </h2>

        {loading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {[...Array(8)].map((_, i) => (
              <div key={i} className="h-32 rounded-2xl bg-slate-200 dark:bg-slate-800 animate-pulse" />
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {clusterData?.nodes?.map((node: any) => (
              <div
                key={node.id}
                className={`p-4 rounded-2xl border transition ${
                  node.online
                    ? "bg-white border-slate-200 dark:bg-slate-900 dark:border-slate-800"
                    : "bg-red-50/50 border-red-200 dark:bg-red-950/20 dark:border-red-900/50"
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <span
                    className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                      node.role === "COORDINATOR"
                        ? "bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300"
                        : "bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300"
                    }`}
                  >
                    {node.role}
                  </span>
                  <div className="flex items-center gap-1.5">
                    <span
                      className={`h-2.5 w-2.5 rounded-full ${
                        node.online ? "bg-emerald-500 animate-pulse" : "bg-red-500"
                      }`}
                    />
                    <span
                      className={`text-xs font-bold ${
                        node.online ? "text-emerald-600" : "text-red-500"
                      }`}
                    >
                      {node.online ? "ONLINE" : "CRASH / DOWN"}
                    </span>
                  </div>
                </div>

                <div className="font-extrabold text-sm text-slate-900 dark:text-white line-clamp-1">
                  {node.name}
                </div>
                <div className="text-xs text-slate-400 mt-1">
                  Port: <strong className="text-slate-700 dark:text-slate-300">:{node.port}</strong> • {node.protocol}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Tabel Riwayat Failover Audit Log */}
      <div className="space-y-4">
        <h2 className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
          <ShieldAlert className="w-5 h-5 text-purple-600" />
          Audit Log Peristiwa Failover Terdistribusi (`cluster_failover_logs`)
        </h2>

        <div className="rounded-2xl bg-white border dark:bg-slate-900 dark:border-slate-800 overflow-hidden shadow-sm">
          {failoverLogs.length === 0 ? (
            <div className="p-8 text-center text-slate-400 text-xs">
              Belum ada peristiwa failover yang terjadi. Sistem beroperasi stabil pada Node Koordinator Utama.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 dark:bg-slate-800/50 border-b dark:border-slate-800 font-bold text-slate-500">
                  <tr>
                    <th className="p-3.5">Waktu Kejadian</th>
                    <th className="p-3.5">Layanan</th>
                    <th className="p-3.5">Koordinator Lama (Down)</th>
                    <th className="p-3.5">Node Promosi (Active)</th>
                    <th className="p-3.5">Penyebab / Alasan</th>
                  </tr>
                </thead>
                <tbody className="divide-y dark:divide-slate-800">
                  {failoverLogs.map((log) => (
                    <tr key={log.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/30">
                      <td className="p-3.5 text-slate-500">{formatDate(log.event_timestamp)}</td>
                      <td className="p-3.5 font-bold text-blue-600">{log.service_name}</td>
                      <td className="p-3.5 font-mono text-red-500">{log.previous_coordinator}</td>
                      <td className="p-3.5 font-mono text-emerald-600 font-bold">{log.promoted_node}</td>
                      <td className="p-3.5 text-slate-600 dark:text-slate-300">{log.reason}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
