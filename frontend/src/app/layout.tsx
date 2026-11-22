import type { Metadata } from "next";
import "./globals.css";
import Navbar from "@/components/layout/Navbar";
import Footer from "@/components/layout/Footer";
import FailoverToast from "@/components/cluster/FailoverToast";

export const metadata: Metadata = {
  title: "SisterShop — Distributed & High-Availability E-Commerce",
  description: "Toko Online Terdistribusi Multi-Protokol (RPC, RMI, REST) dengan Toleransi Kesalahan dan Ketersediaan Tinggi.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="id">
      <body className="flex flex-col min-h-screen bg-slate-50/50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 antialiased">
        <Navbar />
        <main className="flex-1">{children}</main>
        <Footer />
        <FailoverToast />
      </body>
    </html>
  );
}
