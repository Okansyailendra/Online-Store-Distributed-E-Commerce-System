# Product Requirements Document (PRD)
## Toko Online Terdistribusi dengan Toleransi Kesalahan (Fault Tolerance)
**Mata Kuliah:** Sistem Terdistribusi (IF2228)  
**Semester:** Gasal 2026/2027  
**Universitas:** Universitas Trunojoyo Madura  

---

## 1. Latar Belakang & Urgensi Sistem Terdistribusi (Sister)

### 1.1 Urgensi Implementasi Sister pada Studi Kasus Toko Online
Dalam ekosistem e-commerce dan platform belanja modern, ketergantungan pada server tunggal (*centralized / monolithic system*) menimbulkan risiko fatal terhadap kontinuitas bisnis. Penerapan prinsip **Sistem Terdistribusi (Sister)** pada studi kasus toko online menjadi kebutuhan yang sangat mendesak (urgensi tinggi) karena beberapa faktor utama:

1. **Eliminasi Titik Kegagalan Tunggal (*Single Point of Failure* / SPOF):**
   Pada sistem terpusat, jika satu-satunya server mengalami *crash* (gangguan daya, kegagalan hardware, kernel panic, atau terputusnya jaringan), seluruh operasional toko online berhenti seketika (*total outage*). Implementasi arsitektur terdistribusi mendistribusikan beban ke beberapa node independen dan menyediakan node cadangan (*redundancy*), memastikan kelangsungan sistem tidak bertumpu pada satu perangkat fisik semata.

2. **Jaminan Ketersediaan Tinggi (*High Availability* 24/7):**
   Aktivitas transaksi belanja digital dituntut beroperasi tanpa henti. Terjadinya *downtime*—terlebih pada momen puncak (*flash sale* atau promosi)—mengakibatkan kerugian finansial langsung (*loss of revenue*), transaksi customer yang gagal di tengah jalan, serta rusaknya reputasi platform. Melalui sistem terdistribusi dengan toleransi kesalahan (*fault tolerance*) dan promosi otomatis (*automatic failover*), layanan tetap berjalan secara transparan bagi pengguna.

3. **Pemisahan Beban & Isolasi Kegagalan (*Decoupling & Fault Isolation*):**
   Aktivitas toko online memiliki karakteristik beban komputasi yang berbeda-beda:
   - **Transaksi Pembelian (RPC):** Bersifat kritis, memerlukan eksekusi cepat, atomik, dan konsistensi tinggi.
   - **Manajemen & Pengecekan Stok (RMI):** Membutuhkan pemanggilan method jarak jauh secara efisien dan sinkron antar layanan.
   - **Katalog Produk (REST API):** Bersifat *read-heavy* dengan volume pembacaan tinggi dari pengunjung.
   Dengan mendistribusikan masing-masing modul ke node server terpisah, kegagalan atau lonjakan beban pada satu layanan (misal katalog produk) tidak akan merembet melumpuhkan layanan kritis lainnya (*cascading failure*).

4. **Integritas dan Konsistensi Data Terdistribusi:**
   Toko online rentan terhadap permasalahan *race condition* dan ketidakkonsistenan stok barang ketika banyak customer mengakses dan membeli produk pada detik yang sama. Arsitektur terdistribusi yang dilengkapi sinkronisasi state dan replikasi data (*Primary-Backup replication*) memastikan integritas data persediaan barang tetap valid dan mutakhir meski salah satu node mengalami gangguan tiba-tiba.

### 1.2 Ringkasan Proyek
Project ini merupakan implementasi sistem terdistribusi berbasis studi kasus **Toko Online** yang dirancang dengan kemampuan **Toleransi Kesalahan (Fault Tolerance)** dan **Ketersediaan Tinggi (High Availability)**. Sistem dibangun menggunakan Python 3 dengan komunikasi antar node melalui RPC (Remote Procedure Call), RMI (Remote Method Invocation), dan REST API.

Sistem berjalan di beberapa laptop berbeda dalam satu jaringan lokal (LAN). Untuk memastikan sistem tetap dapat melayani aktivitas customer tanpa kegagalan (downtime), sistem menerapkan pola **Koordinator - Pengikut (Coordinator - Follower / Primary - Backup)**:
- Setiap layanan memiliki **Node Koordinator (Primary)** yang telah ditentukan terlebih dahulu untuk melayani request transaksi secara aktif.
- Setiap layanan didampingi oleh **Node Pengikut (Follower / Backup)** siaga yang memantau kondisi Koordinator.
- Apabila 1 node Koordinator mengalami kegagalan (*crash* atau terputus), Node Pengikut secara otomatis **dipromosikan (promoted)** menjadi Koordinator baru (*Failover Promotion*), sehingga transaksi customer tetap berjalan lancar.

---

## 2. Tujuan

- Mengimplementasikan konsep komunikasi terdistribusi:
  - **RPC (Remote Procedure Call)** via Socket murni + serialization `pickle`.
  - **RMI (Remote Method Invocation)** berbasis object invocation.
  - **REST API** berbasis HTTP/JSON (Flask).
- Mengimplementasikan pola arsitektur **Koordinator - Pengikut (Primary - Backup)**.
- Menerapkan mekanisme **Deteksi Kegagalan (Failure Detection)** melalui sinyal *Heartbeat*.
- Menerapkan mekanisme **Promosi Node Otomatis (Automatic Promotion / Failover)** saat 1 node gagal, sehingga sistem bersifat *self-healing* terhadap gangguan node.
- Menjamin kelangsungan aktivitas customer (belanja, cek produk, update stok) secara transparan (*high availability*).

---

## 3. Arsitektur Sistem & Topologi Redundansi

### 3.1 Diagram Arsitektur

```
┌────────────────────────────────────────────────────────────────────────┐
│                           Jaringan Lokal (LAN)                         │
│                                                                        │
│                      ┌──────────────────────┐                          │
│                      │     Client (Web)     │ :5000                    │
│                      └──────────┬───────────┘                          │
│                                 │                                      │
│        ┌────────────────────────┼────────────────────────┐             │
│        │ RPC Call               │ RMI Call               │ REST API    │
│        ▼                        ▼                        ▼             │
│  ┌───────────┐            ┌───────────┐            ┌───────────┐       │
│  │ Server 1  │            │ Server 2  │            │ Server 3  │       │
│  │(RPC Coord)│            │(RMI Coord)│            │(API Coord)│       │
│  └─────┬─────┘            └─────┬─────┘            └─────┬─────┘       │
│        │ [Heartbeat]            │ [Heartbeat]            │ [Heartbeat] │
│        ▼                        ▼                        ▼             │
│  ┌───────────┐            ┌───────────┐            ┌───────────┐       │
│  │ Server 1B │            │ Server 2B │            │ Server 3B │       │
│  │(RPC Follow)            │(RMI Follow)            │(API Follow)       │
│  └───────────┘            └───────────┘            └───────────┘       │
│        │                        │                        │             │
│        └────────────────────────┼────────────────────────┘             │
│                                 │ Akses Data                           │
│                                 ▼                                      │
│                     ┌───────────────────────┐                          │
│                     │       Server 4        │ :6004                    │
│                     │   (Data Koordinator)  │                          │
│                     └───────────┬───────────┘                          │
│                                 │ [Replikasi / Heartbeat]              │
│                                 ▼                                      │
│                     ┌───────────────────────┐                          │
│                     │       Server 4B       │ :6005                    │
│                     │   (Data Pengikut)     │                          │
│                     └───────────────────────┘                          │
└────────────────────────────────────────────────────────────────────────┘
```

> **Catatan Pengaturan Node:** Node Pengikut dapat dijalankan di laptop terpisah (multi-laptop) atau sebagai proses terpisah di node yang tersedia (*cross-backup redundancy*).

### 3.2 Pembagian Peran Node

| Layanan / Fitur | Node Koordinator (Primary) | Node Pengikut (Follower/Backup) | Protokol Komunikasi |
| :--- | :--- | :--- | :--- |
| **Antarmuka Pengguna** | Client Web (:5000) | - | HTTP / Web Browser |
| **Transaksi Pembelian** | Server 1 (:6001) | Server 1-Backup (:6101) | Socket + Pickle (RPC) |
| **Kelola Stok** | Server 2 (:6002) | Server 2-Backup (:6102) | Socket + Pickle (RMI) |
| **Katalog Produk** | Server 3 (:6003) | Server 3-Backup (:6103) | HTTP / REST API |
| **Penyimpanan Data** | Server 4 (:6004) | Server 4-Backup (:6104) | HTTP / REST Internal |

---

## 4. Mekanisme Koordinator, Pengikut, dan Promosi (Fault Tolerance)

### 4.1 Definisi Peran
1. **Koordinator (Primary / Active):**
   - Ditentukan sejak awal konfigurasi (*pre-determined*).
   - Menjadi titik tunggal penerima request transaksi aktif dari Client atau server lain.
   - Mengirimkan sinyal *Heartbeat* secara periodik ke Node Pengikut sebagai tanda bahwa node masih hidup (*alive*).
   - Menyinkronkan perubahan status data/state ke Node Pengikut.

2. **Pengikut (Follower / Standby):**
   - Node cadangan dalam posisi siaga (*hot-standby*).
   - Mendengarkan detak jantung (*Heartbeat listener*) dari Koordinator secara berkala.
   - Menerima salinan pembaruan data/status untuk menjaga konsistensi state.
   - Tidak melayani request transaksi umum selama Koordinator masih aktif.

### 4.2 Penentuan Awal (Pre-determined Assignment)
- Setiap fitur memiliki daftar prioritas node:
  - **Priority 1 (Koordinator Utama):** Default aktif saat sistem pertama kali dinyalakan.
  - **Priority 2 (Pengikut / Backup Siaga):** Siaga menggantikan Priority 1.
- Penentuan ini dikonfigurasi melalui berkas konfigurasi (misal file konfigurasi IP & Port), sehingga setiap node mengetahui perannya masing-masing saat inisialisasi.

### 4.3 Deteksi Kegagalan (Heartbeat Mechanism)
- **Interval Heartbeat:** Koordinator mengirimkan sinyal ping/heartbeat ke Pengikut setiap **$T_{hb}$** detik (default: 2 detik).
- **Timeout Threshold:** Jika Pengikut tidak menerima sinyal heartbeat selama **$T_{timeout}$** detik berturut-turut (default: 5 - 6 detik) atau koneksi ditolak (*connection refused/timeout*), Koordinator dinyatakan **Gagal / Mati (DOWN)**.

### 4.4 Mekanisme Promosi (Automatic Failover / Promotion)
Ketika kegagalan terdeteksi pada Koordinator:
1. **Deteksi:** Node Pengikut mendeteksi batas timeout telah terlampaui.
2. **Promosi Mandiri:** Node Pengikut mengubah status internalnya dari `FOLLOWER` menjadi `COORDINATOR` (dipromosikan).
3. **Aktivasi Layanan:** Node yang baru dipromosikan mulai membuka socket / endpoint untuk melayani request transaksi penuh.
4. **Log Peristiwa:** Node mencatat kejadian failover pada log sistem untuk keperluan audit sistem terdistribusi.

### 4.5 Transparansi Sisi Client (Client-Side Failover Routing)
Agar aktivitas customer tidak gagal saat 1 node mati:
- Client menyimpan daftar alamat server: `[Primary_URL, Backup_URL]`.
- Client memprioritaskan pengiriman request ke Koordinator Utama.
- Apabila terjadi *timeout* atau *connection refused*, Client secara transparan mengalihkan (*retry & reroute*) request ke Pengikut yang telah dipromosikan tanpa menampilkan error fatal kepada customer.

---

## 5. Fitur Sistem

### 5.1 Client (Web)
- Menampilkan antarmuka katalog produk (nama, harga, stok).
- Membeli produk (fitur transaksi via RPC).
- Melihat detail stok produk (fitur cek via RMI).
- Menambah stok produk (fitur update via RMI).
- **Fitur Ketahanan (Resilience):** Otomatis mendeteksi node gagal dan memindahkan jalur komunikasi ke node cadangan yang telah dipromosikan tanpa membuat user mengulang proses.

### 5.2 Server 1 — RPC Server (Transaksi Pembelian)
- **Koordinator:** Menerima panggilan RPC `buy(product_id, qty)`, validasi ke Data Server, memotong stok, dan mengembalikan status transaksi.
- **Pengikut:** Siaga memantau Koordinator Server 1. Jika Server 1 mati, Pengikut dipromosikan menjadi RPC Server baru dan melayani panggilan RPC pembelian.

### 5.3 Server 2 — RMI Server (Manajemen Stok)
- **Koordinator:** Menyediakan objek `StockService` dengan method:
  - `get_stock(product_id)`
  - `update_stock(product_id, qty)`
- **Pengikut:** Memantau ketersediaan Koordinator Server 2. Jika Server 2 mati, Pengikut mempromosikan dirinya untuk mengaktifkan objek remote `StockService`.

### 5.4 Server 3 — API Server (Katalog Produk)
- **Koordinator:** Menyediakan REST API:
  - `GET /products` — mengambil seluruh produk.
  - `GET /products/<id>` — mengambil detail satu produk.
- **Pengikut:** Standby REST API. Mengambil alih endpoint jika API Server utama gagal.

### 5.5 Server 4 — Data Server (Penyimpanan Data)
- **Koordinator:** Menyimpan data produk dan stok di memori (*in-memory dict*), mengekspos REST API internal (`/internal/*`).
- **Pengikut:** Mereplikasi data dari Koordinator setiap ada perubahan (*state replication*). Jika Data Server utama mati, Pengikut dipromosikan menjadi Data Server aktif dengan data terakhir yang konsisten.

---

## 6. Tech Stack

| Komponen | Teknologi | Keterangan |
| :--- | :--- | :--- |
| **Bahasa Pemrograman** | Python 3 | Digunakan di seluruh node |
| **Web Client** | Flask + HTML / Jinja2 | Antarmuka web pengguna |
| **RPC** | Python `socket` + `pickle` | Remote Procedure Call manual |
| **RMI** | Python `socket` + Object Serialization | Remote Method Invocation manual |
| **REST API** | Flask | Endpoint publik dan internal |
| **Fault Tolerance & HA** | Python `threading` + Socket Heartbeat | Mekanisme deteksi gagal & promosi |
| **Data Storage** | In-memory Dict / JSON Persistence | Penyimpanan data produk |
| **Jaringan** | Local Area Network (LAN / Wi-Fi) | Komunikasi multi-laptop berbasis IP |

---

## 7. Struktur Folder

```
project-sisterdis/
├── client/
│   ├── app.py                  # Client web Flask + failover router
│   ├── config.py               # Konfigurasi IP/Port primary & backup
│   └── templates/
│       └── index.html          # UI interaktif untuk belanja & monitoring
├── server1_rpc/
│   ├── server.py               # RPC Server (mendukung mode Koordinator/Pengikut)
│   └── config.py
├── server2_rmi/
│   ├── server.py               # RMI Server (mendukung mode Koordinator/Pengikut)
│   └── config.py
├── server3_api/
│   ├── server.py               # REST API Server katalog + failover
│   └── config.py
├── server4_data/
│   ├── server.py               # Data Server + sinkronisasi replika
│   └── config.py
├── common/                     # Utility bersama (opsional)
│   ├── heartbeat.py            # Modul pemantau detak jantung & promosi
│   └── network.py
├── PRD.md
├── ARCHITECTURE.md
└── README.md
```

---

## 8. Alur Komunikasi

### 8.1 Skenario Normal (Seluruh Koordinator Aktif)
1. **Lihat Produk:** Client memanggil `GET /products` ke Server 3 (Koordinator API) $\rightarrow$ Server 3 memanggil Server 4 $\rightarrow$ data ditampilkan ke customer.
2. **Transaksi Pembelian:** Customer menekan tombol "Beli" $\rightarrow$ Client memanggil RPC `buy()` ke Server 1 (Koordinator RPC) $\rightarrow$ Server 1 memvalidasi & mengurangi stok ke Server 4 $\rightarrow$ respon sukses dikirim ke Client.
3. **Cek / Tambah Stok:** Client memanggil remote method pada Server 2 (Koordinator RMI) $\rightarrow$ Server 2 memproses data ke Server 4 $\rightarrow$ hasil dikembalikan.

### 8.2 Skenario Toleransi Kesalahan (1 Node Koordinator Gagal & Pengikut Dipromosikan)
Contoh kasus pada **Server 1 (RPC Transaksi Pembelian)**:
1. Koordinator Server 1 mendadak mati (*crash* / laptop mati / koneksi terputus).
2. Pengikut Server 1 (Server 1B) mendeteksi ketiadaan *Heartbeat* setelah melewati batas timeout (misal 5 detik).
3. Server 1B **mempromosikan dirinya sendiri** menjadi Koordinator aktif baru (*Promoted to Coordinator*).
4. Customer melakukan transaksi pembelian di web client.
5. Client mencoba menghubungi Server 1 (gagal / timeout) $\rightarrow$ sistem failover Client langsung mengalihkan request ke Server 1B yang telah dipromosikan.
6. Transaksi pembelian diproses oleh Server 1B tanpa error, customer menerima notifikasi berhasil.

---

## 9. Batasan & Asumsi

- **Lingkup Toleransi Kesalahan:** Sistem dirancang untuk mentolerir kegagalan **1 node per peran/fitur** (*Single Point of Failure mitigation*). Jika seluruh koordinator dan pengikut untuk suatu peran mati secara bersamaan, layanan fitur tersebut baru terhenti.
- **Penyimpanan Data:** Data utama tersimpan di memori (in-memory dict) dengan sinkronisasi ke node pengikut data untuk mencegah hilangnya data saat failover.
- **Autentikasi:** Tidak menggunakan sistem login/otentikasi bertingkat (fokus pada materi komunikasi terdistribusi dan ketahanan sistem).
- **Jaringan:** Seluruh node berada dalam satu subnet jaringan lokal (LAN) yang sama tanpa penghalang firewall antar port.

---

## 10. Anggota Kelompok & Pembagian Tugas

| Nama | Node / Tanggung Jawab Utama | Peran Toleransi Kesalahan |
| :--- | :--- | :--- |
| TBD | Client Web (:5000) | Implementasi failover rerouting sisi client |
| TBD | Server 1 (RPC Server) | Koordinator & Pengikut RPC Transaksi |
| TBD | Server 2 (RMI Server) | Koordinator & Pengikut RMI Manajemen Stok |
| TBD | Server 3 (API Server) | Koordinator & Pengikut REST API Katalog |
| TBD | Server 4 (Data Server) | Koordinator & Replikasi Data Pengikut |
