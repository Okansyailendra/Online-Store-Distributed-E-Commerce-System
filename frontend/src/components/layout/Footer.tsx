"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Activity, ShieldCheck, Heart, Radio } from "lucide-react";
import { useClusterStore } from "@/store/useClusterStore";

export default function Footer() {
  const { clusterHealthy, fetchClusterStatus } = useClusterStore();

  useEffect(() => {
    fetchClusterStatus();
    const interval = setInterval(fetchClusterStatus, 10000); // Poll setiap 10 detik
    return () => clearInterval(interval);
  }, [fetchClusterStatus]);

  return (
    <footer className="border-t bg-slate-50 dark:bg-slate-900/50 dark:border-slate-800 mt-20">
      <div className="container mx-auto px-4 py-8 sm:px-6">
        <div className="flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex flex-col items-center md:items-start">
            <span className="font-bold text-slate-800 dark:text-white">
              Sister<span className="text-blue-600">Shop</span> — Distributed E-Commerce Platform
            </span>
            <p className="text-xs text-slate-500 mt-1">
              Tugas Mata Kuliah Sistem Terdistribusi (IF2228) • Teknik Informatika, Universitas Trunojoyo Madura
            </p>
          </div>

          {/* Cluster Status Mini-Pill */}
          <div className="flex items-center gap-3">
            <Link
              href="/admin/cluster"
              className="flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium border bg-white shadow-sm hover:shadow transition dark:bg-slate-800 dark:border-slate-700"
            >
              <span className="relative flex h-2.5 w-2.5">
                <span
                  className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${
                    clusterHealthy ? "bg-emerald-400" : "bg-amber-400"
                  }`}
                />
                <span
                  className={`relative inline-flex rounded-full h-2.5 w-2.5 ${
                    clusterHealthy ? "bg-emerald-500" : "bg-amber-500"
                  }`}
                />
              </span>
              <span className="text-slate-600 dark:text-slate-300">
                Cluster:{" "}
                <strong className={clusterHealthy ? "text-emerald-600" : "text-amber-600"}>
                  {clusterHealthy ? "Toleransi Aktif (Normal)" : "Degraded / Partial"}
                </strong>
              </span>
              <Radio className="w-3.5 h-3.5 text-slate-400 ml-1" />
            </Link>
          </div>
        </div>
      </div>
    </footer>
  );
}
