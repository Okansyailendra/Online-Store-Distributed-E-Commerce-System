# Struktur Proyek, Konfigurasi Lingkungan, & Panduan Deployment Multi-Laptop LAN
## Deployment Guide, Directory Hierarchy, Network Configuration & Chaos Testing Scenarios

- **Dokumen Versi:** 2.0.0
- **Status:** Approved for Implementation
- **Target Topologi:** Single Machine (Localhost Multi-Process) & Multi-Laptop (Local Area Network / Wi-Fi Subnet)
- **Basis Sistem:** Linux, macOS, & Windows (Python 3.11+ & Node.js 18+)

---

## 1. Struktur Direktori Proyek Lengkap (Project File Tree)

Arsitektur repositori mengadopsi struktur monorepo modular yang memisahkan kode frontend, masing-masing layanan backend terdistribusi, utilitas bersama (*common libraries*), dan skrip deployment:

```
/home/kannz/Documents/SISTER/
├── .env.example                               # Template konfigurasi environment global
├── .gitignore                                 # Mengabaikan node_modules, __pycache__, .env, dll.
├── docker-compose.yml                         # Orkestrasi multi-container lokal (opsional)
├── README.md                                  # Ringkasan cepat repositori & quick start
├── docs/                                      # Spesifikasi arsitektural lengkap
│   ├── 01-PRD-PRODUCTION.md                   # Spesifikasi kebutuhan produk
│   ├── 02-DISTRIBUTED-ARCHITECTURE.md         # Topologi, protokol, & failover
│   ├── 03-DATABASE-SCHEMA.md                  # Skema database, DDL, & replikasi
│   ├── 04-API-AND-PROTOCOL-SPEC.md            # Kontrak REST, RPC, dan RMI
│   ├── 05-UI-UX-DESIGN-SYSTEM.md              # Desain antarmuka & penanganan state
│   └── 06-PROJECT-STRUCTURE-AND-DEPLOYMENT.md # Panduan struktur proyek & deployment
├── scripts/                                   # Skrip operasional, data seeding & testing
│   ├── seed_database.py                       # Inisialisasi kategori & 20+ produk awal
│   ├── run_all_local.sh                       # Menjalankan seluruh 8 backend nodes + frontend
│   ├── stop_all_local.sh                      # Menghentikan seluruh proses lokal
│   ├── test_chaos_kill.py                     # Skrip simulasi pematian paksa (crash injection)
│   └── verify_cluster_health.py               # Skrip audit deteksi status kesehatan cluster
├── frontend/                                  # Web Application (Next.js 14+ App Router)
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.ts
│   ├── next.config.mjs
│   ├── public/                                # Media statis, ikon SVG, & placeholder gambar
│   │   ├── images/products/
│   │   └── icons/
│   └── src/
│       ├── app/                               # Next.js App Router Pages
│       │   ├── layout.tsx                     # Global Root Layout + Toaster
│       │   ├── page.tsx                       # Storefront Beranda
│       │   ├── products/
│       │   │   ├── page.tsx                   # Katalog Produk dengan Filter
│       │   │   └── [id]/page.tsx              # Detail Produk Real-time
│       │   ├── cart/page.tsx                  # Keranjang Belanja
│       │   ├── checkout/page.tsx              # Alur Pembayaran & Idempotensi
│       │   ├── orders/
│       │   │   ├── page.tsx                   # Riwayat Pesanan
│       │   │   └── [id]/page.tsx              # Faktur & Status Pengiriman
│       │   ├── auth/
│       │   │   ├── login/page.tsx             # Halaman Masuk
│       │   │   └── register/page.tsx          # Halaman Registrasi
│       │   ├── admin/
│       │   │   ├── page.tsx                   # Dashboard Metrik Penjualan
│       │   │   ├── products/page.tsx          # Manajemen CRUD Produk
│       │   │   ├── inventory/page.tsx         # Manajemen Stok Real-time (RMI)
│       │   │   ├── orders/page.tsx            # Manajemen Status Order
│       │   │   └── cluster/page.tsx           # Panel Monitoring Node & Failover
│       │   └── api/                           # Internal Server Proxy Routes
│       │       ├── proxy/[...path]/route.ts   # Failover HTTP Proxy ke Node API
│       │       └── rpc/route.ts               # Proxy Gateway RPC over TCP Socket
│       ├── components/                        # UI Components (Shadcn + Custom)
│       │   ├── ui/                            # Button, Dialog, Card, Input, Toast, Slider
│       │   ├── layout/Navbar.tsx              # Sticky Header + Search Bar + Cart Counter
│       │   ├── layout/Footer.tsx              # Footer + Cluster Health Status Pill
│       │   ├── product/ProductCard.tsx        # Kartu Katalog Produk Responsif
│       │   ├── product/ProductSkeleton.tsx    # Shimmer Skeleton Loader
│       │   ├── cart/CartItemRow.tsx           # Baris Item Keranjang Interaktif
│       │   └── cluster/NodeStatusCard.tsx     # Kartu Monitoring Detak Jantung Node
│       ├── lib/                               # Utilitas Klien
│       │   ├── failoverRouter.ts              # Logika Retry & Reroute Otomatis
│       │   ├── rpcClient.ts                   # Modul Komunikasi Socket TCP JSON-RPC
│       │   └── utils.ts                       # Format Mata Uang (IDR) & Tanggal
│       └── store/                             # Zustand State Management
│           ├── useCartStore.ts                # State Keranjang Belanja Persisten
│           ├── useAuthStore.ts                # State Sesi Pengguna & JWT Token
│           └── useClusterStore.ts             # State Status Node Health & Failover Alerts
└── backend/                                   # Distributed Backend Services (Python 3)
    ├── requirements.txt                       # Dependensi global backend Python
    ├── common/                                # Modul Bersama Seluruh Node Terdistribusi
    │   ├── __init__.py
    │   ├── config.py                          # Parser variabel lingkungan (.env)
    │   ├── logger.py                          # Logger terstruktur dengan pewarnaan terminal
    │   ├── heartbeat.py                       # Modul HeartbeatEmitter & HeartbeatListener
    │   ├── failover.py                        # Finite State Machine & Promosi Otomatis
    │   ├── rpc_protocol.py                    # Length-Prefixed JSON-RPC Framer & Socket Handler
    │   └── db_client.py                       # HTTP Client pembungkus akses ke server4_data
    ├── server1_rpc/                           # Layanan Transaksi & Checkout (RPC)
    │   ├── server.py                          # Main Entry: Mode COORDINATOR atau FOLLOWER
    │   ├── checkout_handler.py                # Eksekusi atomik checkout, validasi, rollback
    │   └── config.py
    ├── server2_rmi/                           # Layanan Inventaris & Stok (RMI)
    │   ├── server.py                          # Main Entry: Pyro5 Daemon / Object Invocation
    │   ├── inventory_service.py               # Kelas remote InventoryService + OCC logic
    │   └── config.py
    ├── server3_api/                           # Layanan Katalog, Auth, & Cart (REST API)
    │   ├── server.py                          # Main Entry: FastAPI Application + Uvicorn
    │   ├── routes/                            # Route Handlers: auth, products, cart, orders
    │   ├── schemas/                           # Pydantic v2 Input/Output Models
    │   └── config.py
    └── server4_data/                          # Layanan Basis Data Persisten & Replikasi
        ├── server.py                          # HTTP Data Access Server & Replication Master
        ├── database.py                        # Konektor PostgreSQL / SQLite WAL Engine
        ├── replication.py                     # Streaming Replikasi Mutasi Real-time
        └── config.py
```

---

## 2. Konfigurasi Environment (`.env.example`)

File konfigurasi ini memungkinkan pengaturan alamat IP dan port secara dinamis. Nilai default dikonfigurasi untuk pengujian 1 laptop (*localhost*), namun dapat langsung diganti dengan IP LAN saat deployment multi-laptop:

```ini
# ==============================================================================
# SISTER E-COMMERCE: GLOBAL ENVIRONMENT CONFIGURATION
# ==============================================================================
# Mode Lingkungan: "development" | "production" | "demo"
ENVIRONMENT=development
LOG_LEVEL=INFO

# ------------------------------------------------------------------------------
# FRONTEND CONFIGURATION (NEXT.JS)
# ------------------------------------------------------------------------------
NEXT_PUBLIC_APP_URL=http://localhost:3000
PORT=3000

# ------------------------------------------------------------------------------
# SERVER 1: RPC TRANSAKSI & CHECKOUT
# ------------------------------------------------------------------------------
# Koordinator (Primary)
SERVER1_RPC_PRIMARY_HOST=127.0.0.1
SERVER1_RPC_PRIMARY_PORT=6001

# Pengikut (Follower / Backup)
SERVER1_RPC_BACKUP_HOST=127.0.0.1
SERVER1_RPC_BACKUP_PORT=6101

# Heartbeat Listener Port pada Node Backup
SERVER1_RPC_HEARTBEAT_PORT=6201

# ------------------------------------------------------------------------------
# SERVER 2: RMI MANAJEMEN INVENTARIS & STOK
# ------------------------------------------------------------------------------
# Koordinator (Primary)
SERVER2_RMI_PRIMARY_HOST=127.0.0.1
SERVER2_RMI_PRIMARY_PORT=6002

# Pengikut (Follower / Backup)
SERVER2_RMI_BACKUP_HOST=127.0.0.1
SERVER2_RMI_BACKUP_PORT=6102

# Heartbeat Listener Port pada Node Backup
SERVER2_RMI_HEARTBEAT_PORT=6202

# ------------------------------------------------------------------------------
# SERVER 3: REST API KATALOG, AUTH, & ORDER HISTORY
# ------------------------------------------------------------------------------
# Koordinator (Primary)
SERVER3_API_PRIMARY_HOST=127.0.0.1
SERVER3_API_PRIMARY_PORT=6003

# Pengikut (Follower / Backup)
SERVER3_API_BACKUP_HOST=127.0.0.1
SERVER3_API_BACKUP_PORT=6103

# Heartbeat Listener Port pada Node Backup
SERVER3_API_HEARTBEAT_PORT=6203

# ------------------------------------------------------------------------------
# SERVER 4: PENYIMPANAN DATA PERSISTEN & REPLIKASI
# ------------------------------------------------------------------------------
# Koordinator Data (Primary DB Node)
SERVER4_DATA_PRIMARY_HOST=127.0.0.1
SERVER4_DATA_PRIMARY_PORT=6004

# Pengikut Data (Replica DB Node)
SERVER4_DATA_BACKUP_HOST=127.0.0.1
SERVER4_DATA_BACKUP_PORT=6104

# Jalur Replikasi & Heartbeat Listener Data
SERVER4_DATA_REPLICATION_PORT=6204

# Engine Basis Data: "sqlite" (Single-File WAL Mode) atau "postgres"
DATABASE_ENGINE=sqlite
DATABASE_SQLITE_PRIMARY_PATH=./backend/server4_data/primary_ecommerce.db
DATABASE_SQLITE_BACKUP_PATH=./backend/server4_data/backup_ecommerce.db

# Jika menggunakan PostgreSQL:
POSTGRES_USER=sister_user
POSTGRES_PASSWORD=sister_secret_password
POSTGRES_DB=sister_ecommerce
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5432

# ------------------------------------------------------------------------------
# FAULT TOLERANCE & HEARTBEAT PARAMETERS
# ------------------------------------------------------------------------------
# Interval pengiriman detak jantung (detik)
HEARTBEAT_INTERVAL=2.0

# Ambang batas waktu sebelum follower mempromosikan diri (detik)
HEARTBEAT_TIMEOUT=5.0

# Jumlah detak hilang maksimal sebelum deklarasi crash
MAX_MISSED_HEARTBEATS=3

# Socket connection timeout (detik)
SOCKET_TIMEOUT=1.5

# ------------------------------------------------------------------------------
# KEAMANAN & AUTENTIKASI
# ------------------------------------------------------------------------------
JWT_SECRET_KEY=super_secure_jwt_secret_key_sister_trunojoyo_2026
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
```

---

## 3. Panduan Deployment Multi-Laptop dalam Jaringan LAN

Skenario ini dirancang khusus untuk demonstrasi tugas besar di laboratorium / ruang kelas menggunakan **3 hingga 5 laptop** yang terhubung ke satu Wi-Fi router / switch LAN yang sama:

### 3.1 Skema Pembagian Laptop Contoh (5 Laptop Mahasiswa)

| Laptop ID | Nama Mahasiswa / Peran | IP Address Contoh | Node Layanan yang Dijalankan |
| :---: | :--- | :--- | :--- |
| **Laptop 1** | Okan (Project Lead / Client) | `192.168.1.101` | **Frontend Web Next.js (:3000)** |
| **Laptop 2** | Aril (System Architect) | `192.168.1.102` | **Server 1 Primary (:6001)** & **Server 2 Backup (:6102)** |
| **Laptop 3** | Rafi (Fault Tolerance Lead) | `192.168.1.103` | **Server 1 Backup (:6101)** & **Server 2 Primary (:6002)** |
| **Laptop 4** | Arfian (Data & Replikasi Lead)| `192.168.1.104` | **Server 3 Primary (:6003)** & **Server 4 Primary (:6004)** |
| **Laptop 5** | Afriza (QA & Demo Operator) | `192.168.1.105` | **Server 3 Backup (:6103)** & **Server 4 Backup (:6104)** |

*(Catatan: Pengaturan cross-redundancy di atas menjamin jika salah satu laptop mati total, laptop pasangannya tetap menjalankan fungsi cadangan secara mandiri).*

### 3.2 Langkah-Langkah Konfigurasi Multi-Laptop

1. **Samakan Subnet Wi-Fi:** Pastikan seluruh laptop terhubung ke Access Point yang sama dan dapat saling melakukan `ping` antar alamat IP.
2. **Periksa Firewall Port:**
   - Linux: `sudo ufw allow 3000,6001:6004/tcp && sudo ufw allow 6101:6104/tcp && sudo ufw allow 6201:6204/tcp`
   - Windows: Buka *Windows Defender Firewall* -> Izinkan port 3000, 6001–6004, 6101–6104, dan 6201–6204.
3. **Distribusikan File `.env`:** Salin file `.env` dengan alamat IP LAN aktual masing-masing laptop ke seluruh mesin.
4. **Jalankan Node Sesuai Peran:**
   - Di Laptop 2 (Server 1 Primary & Server 2 Backup):
     ```bash
     python3 backend/server1_rpc/server.py --role COORDINATOR
     python3 backend/server2_rmi/server.py --role FOLLOWER
     ```
   - Di Laptop 3 (Server 1 Backup & Server 2 Primary):
     ```bash
     python3 backend/server1_rpc/server.py --role FOLLOWER
     python3 backend/server2_rmi/server.py --role COORDINATOR
     ```
   - Di Laptop 4 (Server 3 Primary & Server 4 Primary):
     ```bash
     python3 backend/server4_data/server.py --role COORDINATOR
     python3 backend/server3_api/server.py --role COORDINATOR
     ```
   - Di Laptop 5 (Server 3 Backup & Server 4 Backup):
     ```bash
     python3 backend/server4_data/server.py --role FOLLOWER
     python3 backend/server3_api/server.py --role FOLLOWER
     ```
   - Di Laptop 1 (Frontend):
     ```bash
     cd frontend && npm install && npm run dev
     ```

---

## 4. Database Seeding (Data Produk Awal)

Skrip `scripts/seed_database.py` secara otomatis mengisi data awal yang siap digunakan untuk demo belanja e-commerce:

```python
# Cuplikan Data Seeding (scripts/seed_database.py)
INITIAL_CATEGORIES = [
    {"name": "Elektronik & Gadget", "slug": "elektronik-gadget", "description": "Laptop, smartphone, dan perangkat pintar"},
    {"name": "Aksesoris Komputer", "slug": "aksesoris-komputer", "description": "Keyboard mekanik, mouse ergonomis, monitor"},
    {"name": "Pakaian & Fashion", "slug": "pakaian-fashion", "description": "Kaos distro, jaket hoodie, celana denim"},
    {"name": "Buku & Alat Tulis", "slug": "buku-alat-tulis", "description": "Buku komputer, sistem terdistribusi, novel"}
]

INITIAL_PRODUCTS = [
    {
        "sku": "SKU-LAP-001",
        "name": "Laptop UltraBook Pro 14 Inch",
        "category_slug": "elektronik-gadget",
        "price": 12500000.00,
        "stock": 10,
        "description": "Prosesor Core i7, RAM 16GB, SSD 512GB NVMe, Layar 2.8K OLED.",
        "image_url": "/images/products/ultrabook-14.webp"
    },
    {
        "sku": "SKU-MOU-002",
        "name": "Wireless Ergonomic Mouse Silent",
        "category_slug": "aksesoris-komputer",
        "price": 350000.00,
        "stock": 25,
        "description": "Koneksi ganda 2.4Ghz & Bluetooth, sensor 4000 DPI, baterai tahan 3 bulan.",
        "image_url": "/images/products/mouse-ergo.webp"
    },
    {
        "sku": "SKU-KEY-003",
        "name": "Mechanical Keyboard 75% RGB",
        "category_slug": "aksesoris-komputer",
        "price": 850000.00,
        "stock": 15,
        "description": "Hot-swappable tactile switch, PBT double-shot keycaps, RGB backlight.",
        "image_url": "/images/products/keyboard-75.webp"
    },
    {
        "sku": "SKU-BOOK-004",
        "name": "Buku Konsep Sistem Terdistribusi Modern",
        "category_slug": "buku-alat-tulis",
        "price": 145000.00,
        "stock": 50,
        "description": "Panduan komprehensif arsitektur mikro, konsensus Raft, Paxos, dan toleransi kesalahan.",
        "image_url": "/images/products/buku-sister.webp"
    },
    {
        "sku": "SKU-HOD-005",
        "name": "Hoodie Developer Binary Edition",
        "category_slug": "pakaian-fashion",
        "price": 280000.00,
        "stock": 30,
        "description": "Bahan katun fleece premium, hangat, nyaman untuk sesi coding marathon.",
        "image_url": "/images/products/hoodie-dev.webp"
    }
]
```

---

## 5. Skenario Pengujian Uji Ketahanan & Demonstrasi Live Failover

Prosedur uji coba ini dirancang agar tim dapat mendemonstrasikan kemampuan toleransi kesalahan di depan dosen penguji secara meyakinkan dan tanpa kegagalan:

### Skenario 1: Transaksi Normal (Baseline Verification)
1. Buka browser di Laptop 1 menuju `http://localhost:3000`.
2. Masuk ke halaman katalog, pilih `Laptop UltraBook Pro 14 Inch` (stok awal = 10).
3. Tambahkan 1 item ke keranjang dan klik **Lanjut ke Checkout**.
4. Isi alamat dan pilih metode pembayaran Transfer Bank, klik **Konfirmasi Pembayaran**.
5. **Observasi:**
   - Transaksi sukses dalam $< 300$ ms. Nomor pesanan `ORD-20261122-XXXXX` terbit.
   - Periksa terminal `server1_rpc` (Primary :6001): tercatat log pemanggilan RPC `process_checkout`.
   - Periksa terminal `server2_rmi` (Primary :6002): tercatat log pemotongan stok dari 10 menjadi 9.
   - Periksa terminal `server4_data`: tercatat log replikasi mutasi data ke Server 4B.

### Skenario 2: Simulasi Crash Server 1 (RPC Transaksi Koordinator Mati)
1. Pada terminal Laptop 2 yang menjalankan `server1_rpc` Primary (:6001), lakukan pemutusan paksa mendadak dengan menekan **`Ctrl + C`** atau perintah `kill -9 <PID>`.
2. Amati terminal Laptop 3 yang menjalankan `server1_rpc_backup` (:6101):
   - Timer countdown timeout berjalan: $1.0\text{s} \rightarrow 3.0\text{s} \rightarrow 5.0\text{s}$.
   - Tepat pada detik ke-5, muncul log tebal merah/kuning:
     ```
     [HEARTBEAT TIMEOUT] 3 detak berturut-turut tidak diterima dari 192.168.1.102:6001!
     [STATE TRANSITION] Mengubah status dari STANDBY_FOLLOWER -> COORDINATOR
     [PROMOTION SUCCESS] Server 1B berhasil dipromosikan menjadi RPC Coordinator aktif!
     [AUDIT LOG] Peristiwa failover dicatat ke basis data terdistribusi.
     ```
3. Kembali ke Web Browser di Laptop 1 tanpa me-refresh halaman:
   - Klik beli produk kedua: `Wireless Ergonomic Mouse`.
   - Lakukan Checkout dan klik **Konfirmasi Pembayaran**.
4. **Hasil Pengujian yang Diharapkan:**
   - Klien mencoba ke port 6001 $\rightarrow$ mendeteksi koneksi terputus dalam 200 ms.
   - Klien secara instan mengalihkan panggilan ke `server1_rpc_backup` (:6101).
   - Muncul toast ungu halus di web browser: *"Toleransi Kesalahan Sistem Aktif: Beralih ke Node Cadangan (:6101)"*.
   - Pesanan berhasil dibuat dengan status sukses tanpa kesalahan visual bagi pembeli.

### Skenario 3: Simulasi Matinya Database Koordinator (`server4_data` Crash)
1. Matikan proses `server4_data` Primary (:6004).
2. `server4_data_backup` (:6104) mendeteksi timeout heartbeat dan mempromosikan dirinya menjadi database utama aktif.
3. Lakukan pembacaan riwayat pesanan (`GET /orders`) dan pembaruan stok via admin.
4. **Hasil Pengujian yang Diharapkan:**
   - Seluruh data yang dibuat pada Skenario 1 dan 2 tetap utuh dan terbaca lengkap.
   - Tidak ada rollback atau kehilangan pesanan (*Zero Data Loss / RPO = 0*).
   - Panel `/admin/cluster` memperbarui visualisasi: Node Server 4 Primary berubah merah (`CRASHED`), sedangkan Server 4 Backup berubah hijau menyala (`PROMOTED / ACTIVE COORDINATOR`).