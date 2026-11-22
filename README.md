# Online Store – Distributed E-Commerce System
> **High-Availability & Fault-Tolerant Distributed Architecture**  
> Tugas Besar Mata Kuliah Sistem Terdistribusi (IF2228) — Teknik Informatika, Universitas Trunojoyo Madura.

[![Architecture: Distributed](https://img.shields.io/badge/Architecture-Distributed%20Microservices-blue.svg)](#arsitektur-sistem)
[![Protocols: RPC | RMI | REST](https://img.shields.io/badge/Protocols-RPC%20%7C%20RMI%20%7C%20REST-orange.svg)](#spesifikasi-protokol)
[![Fault Tolerance: Heartbeat + Failover](https://img.shields.io/badge/Fault%20Tolerance-Heartbeat%20%2B%20Failover-emerald.svg)](#mekanisme-fault-tolerance)
[![Frontend: Next.js 14 App Router](https://img.shields.io/badge/Frontend-Next.js%2014%20App%20Router-black.svg)](#frontend-web-app)

---

## 📌 Ringkasan Proyek

Platform E-Commerce Terdistribusi modern yang mengeliminasi **Single Point of Failure (SPOF)** melalui arsitektur **Koordinator–Pengikut (Primary–Backup / Hot-Standby)** di setiap tingkatan fungsional:
- **Server 1 (RPC):** Transaksi checkout atomik berkecepatan tinggi dengan proteksi idempotensi (`idempotency_key`).
- **Server 2 (RMI):** Manajemen inventaris persediaan dengan **Optimistic Concurrency Control (OCC)** untuk jaminan anti-overselling.
- **Server 3 (REST API):** Katalog produk, keranjang belanja, autentikasi sesi JWT, dan monitoring cluster.
- **Server 4 (Data Layer):** Penyimpanan persisten SQLite WAL / PostgreSQL dengan streaming replikasi mutasi real-time (**Recovery Point Objective = 0**).
- **Frontend Web App:** Next.js 14 (App Router), TypeScript, Tailwind CSS, Zustand, dilengkapi **Client-Side Transparent Failover Router**.

---

## 🏗️ Topologi & Arsitektur Terdistribusi

```mermaid
flowchart TD
    subgraph ClientTier["Frontend & Gateway (:3000)"]
        Browser["Next.js 14 App Router Storefront"]
        SmartProxy["Client-Side Failover Router & API Gateway"]
        Browser <--> SmartProxy
    end

    subgraph ServiceTier["Backend Distributed Nodes (Python 3)"]
        subgraph ClusterRPC["Layanan Transaksi (RPC)"]
            RPC_Coord["Server 1: RPC Koordinator<br/>Primary :6001"]
            RPC_Follow["Server 1B: RPC Pengikut<br/>Backup :6101"]
            RPC_Coord -.->|Heartbeat Thb=2s<br/>Port :6201| RPC_Follow
        end

        subgraph ClusterRMI["Layanan Stok (RMI Pyro5)"]
            RMI_Coord["Server 2: RMI Koordinator<br/>Primary :6002"]
            RMI_Follow["Server 2B: RMI Pengikut<br/>Backup :6102"]
            RMI_Coord -.->|Heartbeat Thb=2s<br/>Port :6202| RMI_Follow
        end

        subgraph ClusterAPI["Layanan Katalog & Auth (REST)"]
            API_Coord["Server 3: REST API Koordinator<br/>Primary :6003"]
            API_Follow["Server 3B: REST API Pengikut<br/>Backup :6103"]
            API_Coord -.->|Heartbeat Thb=2s<br/>Port :6203| API_Follow
        end
    end

    subgraph DataTier["Data Persistence & Replikasi"]
        DATA_Coord["Server 4: Data Koordinator<br/>Primary :6004"]
        DATA_Follow["Server 4B: Data Pengikut<br/>Backup :6104"]
        DATA_Coord -.->|Heartbeat Thb=2s<br/>Port :6204| DATA_Follow
        DATA_Coord ==>|Semi-Sync State Replication| DATA_Follow
    end

    SmartProxy ==>|1. JSON-RPC (Checkout)| RPC_Coord
    SmartProxy -.->|Failover Reroute if Down| RPC_Follow

    SmartProxy ==>|2. Remote Method Invocation| RMI_Coord
    SmartProxy -.->|Failover Reroute if Down| RMI_Follow

    SmartProxy ==>|3. REST API Requests| API_Coord
    SmartProxy -.->|Failover Reroute if Down| API_Follow

    RPC_Coord --> DATA_Coord
    RMI_Coord --> DATA_Coord
    API_Coord --> DATA_Coord
```

---

## ⚡ Matriks Port & Protokol Komunikasi

| Layanan | Node Koordinator (Primary) | Node Pengikut (Follower) | Port Heartbeat | Protokol Jaringan |
| :--- | :---: | :---: | :---: | :--- |
| **Frontend Web** | `Port 3000` | - | - | HTTP / React Server Components |
| **Server 1: RPC Checkout** | `Port 6001` | `Port 6101` | `Port 6201` | TCP Socket (Length-Prefixed JSON-RPC 2.0) |
| **Server 2: RMI Inventaris** | `Port 6002` | `Port 6102` | `Port 6202` | Pyro5 Remote Object Invocation |
| **Server 3: REST API Katalog**| `Port 6003` | `Port 6103` | `Port 6203` | HTTP/1.1 REST (FastAPI + ASGI) |
| **Server 4: Data & Replikasi**| `Port 6004` | `Port 6104` | `Port 6204` | HTTP Data Service + Semi-Sync WAL |

---

## 🛡️ Mekanisme Toleransi Kesalahan (Fault Tolerance)

1. **Heartbeat Emission & Detection:** Node Koordinator mengirimkan paket sinyal ping detak jantung setiap $T_{hb} = 2.0$ detik ke Node Pengikut.
2. **Ambang Batas Waktu ($T_{timeout}$):** Apabila Pengikut tidak menerima detak jantung selama $T_{timeout} = 5.0$ detik (3 detak hilang berturut-turut), Pengikut mendeklarasikan Koordinator mati (*CRASHED*).
3. **Promosi Mandiri Otomatis (*Self-Promotion*):** Pengikut secara otonom mempromosikan statusnya menjadi `COORDINATOR`, mengikat socket layanan aktif, dan mencatat peristiwa ke tabel audit `cluster_failover_logs`.
4. **Client-Side Transparent Failover Routing:** Klien web frontend mendeteksi putusnya koneksi TCP (`ECONNREFUSED` / timeout $> 1.5$ detik) dan mengalihkan request secara transparan ke port cadangan tanpa menampilkan pesan error atau form ter-reset kepada pengguna.
5. **Anti-Overselling Concurrency Protection:** Pemotongan stok memverifikasi kolom `version` (Optimistic Concurrency Control) untuk mencegah *race condition* saat lonjakan pembelian bersamaan.

---

## 🚀 Panduan Menjalankan Sistem

### Mode 1: Menjalankan di 1 Laptop (Localhost)

1. **Clone Repositori & Buat Virtual Environment:**
   ```bash
   git clone https://github.com/Okansyailendra/Online-Store-Distributed-E-Commerce-System.git
   cd Online-Store-Distributed-E-Commerce-System
   python3 -m venv venv
   source venv/bin/activate  # Untuk Fish shell: source venv/bin/activate.fish
   pip install -r backend/requirements.txt
   ```

2. **Inisialisasi Database & Seeding Awal:**
   ```bash
   python3 scripts/seed_database.py
   ```

3. **Jalankan Seluruh 8 Node Backend (One-Click Script):**
   ```bash
   ./scripts/run_all_local.sh
   ```
   *(Seluruh log tercatat rapi di direktori `logs/`)*

4. **Jalankan Frontend Web App:**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
   Buka peramban di: [**http://localhost:3000**](http://localhost:3000)

   *(Atau alternatif cepat tanpa `npm install`: jalankan `python3 client/app.py`)*

---

### Mode 2: Menjalankan di Multi-Laptop (1 Jaringan Wi-Fi / Hotspot yang Sama)

Skenario ini dirancang khusus untuk demonstrasi tugas besar di kelas/laboratorium kampus menggunakan **3 hingga 5 laptop mahasiswa**:

#### 1. Persiapan Jaringan Wi-Fi & Firewall
- Pastikan seluruh laptop terhubung ke satu **Access Point Wi-Fi atau Hotspot HP yang sama**.
- Cek alamat IP LAN masing-masing laptop:
  - Linux: `ip a` (cari interface `wlan0` atau `wlp2s0`)
  - Windows: Buka CMD lalu ketik `ipconfig` (cari `IPv4 Address`)
- Buka port firewall pada setiap laptop:
  - Linux: `sudo ufw allow 3000,6001:6004/tcp && sudo ufw allow 6101:6104/tcp && sudo ufw allow 6201:6204/tcp`
  - Windows: Buka *Windows Defender Firewall* -> Izinkan port 3000, 6001–6004, 6101–6104, dan 6201–6204.

#### 2. Contoh Pembagian Peran Node (5 Laptop Mahasiswa)

| Laptop ID | Nama Anggota & IP Contoh | Node Backend / Frontend yang Dijalankan |
| :---: | :--- | :--- |
| **Laptop 1** | Okan (`192.168.1.101`) | **Frontend Web Next.js (:3000)** |
| **Laptop 2** | Aril (`192.168.1.102`) | **Server 1 Primary (:6001)** & **Server 2 Backup (:6102)** |
| **Laptop 3** | Rafi (`192.168.1.103`) | **Server 1 Backup (:6101)** & **Server 2 Primary (:6002)** |
| **Laptop 4** | Arfian (`192.168.1.104`) | **Server 3 Primary (:6003)** & **Server 4 Primary (:6004)** |
| **Laptop 5** | Afriza (`192.168.1.105`) | **Server 3 Backup (:6103)** & **Server 4 Backup (:6104)** |

#### 3. Sesuaikan Konfigurasi File `.env` di Semua Laptop
Salin file `.env.example` menjadi `.env` di semua laptop, lalu masukkan alamat IP laptop teman Anda yang menjalankan layanan tersebut:
```ini
# Ganti dengan IP laptop masing-masing:
SERVER1_RPC_PRIMARY_HOST=192.168.1.102
SERVER1_RPC_BACKUP_HOST=192.168.1.103

SERVER2_RMI_PRIMARY_HOST=192.168.1.103
SERVER2_RMI_BACKUP_HOST=192.168.1.102

SERVER3_API_PRIMARY_HOST=192.168.1.104
SERVER3_API_BACKUP_HOST=192.168.1.105

SERVER4_DATA_PRIMARY_HOST=192.168.1.104
SERVER4_DATA_BACKUP_HOST=192.168.1.105
```

#### 4. Menjalankan Node di Laptop Masing-Masing
- **Di Laptop 2 (Server 1 Primary & Server 2 Backup):**
  ```bash
  python3 backend/server1_rpc/server.py --role COORDINATOR
  python3 backend/server2_rmi/server.py --role FOLLOWER
  ```
- **Di Laptop 3 (Server 1 Backup & Server 2 Primary):**
  ```bash
  python3 backend/server1_rpc/server.py --role FOLLOWER
  python3 backend/server2_rmi/server.py --role COORDINATOR
  ```
- **Di Laptop 4 (Server 3 Primary & Server 4 Primary):**
  ```bash
  python3 backend/server4_data/server.py --role COORDINATOR
  python3 backend/server3_api/server.py --role COORDINATOR
  ```
- **Di Laptop 5 (Server 3 Backup & Server 4 Backup):**
  ```bash
  python3 backend/server4_data/server.py --role FOLLOWER
  python3 backend/server3_api/server.py --role FOLLOWER
  ```
- **Di Laptop 1 (Frontend):**
  ```bash
  cd frontend && npm run dev
  ```
  Buka browser di Laptop 1: `http://localhost:3000` (atau anggota lain bisa buka dari browser laptop mereka di `http://192.168.1.101:3000`).

---

### Demonstrasi Failover Lintas Laptop (Live Demo Dosen)
1. Mahasiswa di Laptop 1 membuka toko online di browser.
2. Saat proses demo berlangsung, **matikan Wi-Fi atau tekan `Ctrl + C` di Laptop 2 (Server 1 Primary)**.
3. Amati layar **Laptop 3 (Server 1 Backup)**: dalam 5 detik muncul log promosi `[PROMOTED TO COORDINATOR]`.
4. Di **Laptop 1**, pembeli menekan tombol beli lagi. Transaksi tetap sukses 100% karena diarahkan ke Laptop 3!

---

---

### Akun Demo Bawaan (Sudah Terisi di Database)

| Peran Pengguna | Email | Kata Sandi | Akses Halaman |
| :--- | :--- | :--- | :--- |
| **Admin / Seller** | `admin@sister.com` | `AdminPass123!` | `/admin` & `/admin/cluster` |
| **Customer (Pembeli)** | `budi@sister.com` | `BudiPass123!` | `/products`, `/cart`, `/checkout` |

---

## 🧪 Skenario Pengujian Failover (Demonstrasi Demo)

1. Buka halaman katalog dan lakukan pembelian barang di [http://localhost:3000/products](http://localhost:3000/products).
2. Di terminal, matikan paksa Node Koordinator RPC (Port 6001):
   ```bash
   fuser -k 6001/tcp
   ```
3. Dalam rentang 5 detik, periksa terminal atau log Node Pengikut di port 6101:
   ```text
   [FAILOVER DETECTED] Detak jantung hilang selama 5.02s!
   [PROMOTION SUCCESS] Node RPC Backup dipromosikan menjadi COORDINATOR aktif!
   ```
4. Lakukan transaksi checkout lagi di browser web. Browser akan menampilkan toast pemberitahuan halus *"Toleransi Kesalahan Sistem Aktif: Dialihkan ke Node Cadangan (:6101)"*, dan transaksi berhasil tanpa gangguan.

Untuk mematikan seluruh node setelah selesai pengujian:
```bash
./scripts/stop_all_local.sh
```

---

## 📚 Dokumentasi Spesifikasi Arsitektural Lengkap

Spesifikasi detail perancangan dapat dipelajari pada direktori [`/docs`](/docs):
- [`01-PRD-PRODUCTION.md`](/docs/01-PRD-PRODUCTION.md): Matriks kebutuhan produk & toleransi kesalahan.
- [`02-DISTRIBUTED-ARCHITECTURE.md`](/docs/02-DISTRIBUTED-ARCHITECTURE.md): Diagram alur topologi, sequence diagram, dan state machine.
- [`03-DATABASE-SCHEMA.md`](/docs/03-DATABASE-SCHEMA.md): Skema relasional, DDL SQL, dan replikasi WAL.
- [`04-API-AND-PROTOCOL-SPEC.md`](/docs/04-API-AND-PROTOCOL-SPEC.md): Kontrak endpoint REST, wire frame JSON-RPC 2.0 TCP, dan RMI Pyro5.
- [`05-UI-UX-DESIGN-SYSTEM.md`](/docs/05-UI-UX-DESIGN-SYSTEM.md): Sistem desain antarmuka, wireframe layout, dan state loading.
- [`06-PROJECT-STRUCTURE-AND-DEPLOYMENT.md`](/docs/06-PROJECT-STRUCTURE-AND-DEPLOYMENT.md): Panduan multi-laptop LAN subnet dan chaos testing.

---

## 👥 Tim Pengembang
- **Mata Kuliah:** Sistem Terdistribusi (IF2228)
- **Program Studi:** Teknik Informatika, Universitas Trunojoyo Madura
