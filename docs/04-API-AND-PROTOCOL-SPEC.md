# Spesifikasi Kontrak Komunikasi: REST API, RPC, & RMI
## Comprehensive Multi-Protocol Interface & Serialization Specification

- **Dokumen Versi:** 2.0.0
- **Status:** Approved for Implementation
- **Layanan Terlibat:** `server1_rpc`, `server2_rmi`, `server3_api`, `server4_data`

---

## 1. REST API Contracts (`server3_api`)

Layanan `server3_api` berjalan pada port `6003` (Koordinator) dan port `6103` (Pengikut). Seluruh komunikasi publik menggunakan protokol HTTP/1.1 dengan payload format `application/json`.

### 1.1 Modul Autentikasi (`/api/v1/auth`)

#### `POST /api/v1/auth/register`
Mendaftarkan akun pembeli baru.
- **Headers:** `Content-Type: application/json`
- **Request Body:**
  ```json
  {
    "email": "budi.santoso@example.com",
    "password": "PasswordSangatAman123!",
    "full_name": "Budi Santoso",
    "phone_number": "081234567890"
  }
  ```
- **Response `201 Created`:**
  ```json
  {
    "success": true,
    "message": "Registrasi akun berhasil.",
    "data": {
      "user_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "email": "budi.santoso@example.com",
      "full_name": "Budi Santoso",
      "role": "CUSTOMER",
      "created_at": "2026-11-22T15:55:00.000Z"
    }
  }
  ```
- **Response `409 Conflict` (Email sudah terdaftar):**
  ```json
  {
    "success": false,
    "error_code": "EMAIL_ALREADY_EXISTS",
    "message": "Alamat email tersebut sudah terdaftar dalam sistem."
  }
  ```

#### `POST /api/v1/auth/login`
Autentikasi akun dan penerbitan token JWT.
- **Request Body:**
  ```json
  {
    "email": "budi.santoso@example.com",
    "password": "PasswordSangatAman123!"
  }
  ```
- **Response `200 OK`:**
  ```json
  {
    "success": true,
    "message": "Login berhasil.",
    "data": {
      "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "token_type": "Bearer",
      "expires_in_seconds": 86400,
      "user": {
        "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "email": "budi.santoso@example.com",
        "full_name": "Budi Santoso",
        "role": "CUSTOMER"
      }
    }
  }
  ```
- **Response `401 Unauthorized`:**
  ```json
  {
    "success": false,
    "error_code": "INVALID_CREDENTIALS",
    "message": "Kombinasi email atau kata sandi tidak cocok."
  }
  ```

#### `GET /api/v1/auth/me`
Mendapatkan profil pengguna yang sedang login.
- **Headers:** `Authorization: Bearer <access_token>`
- **Response `200 OK`:**
  ```json
  {
    "success": true,
    "data": {
      "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "email": "budi.santoso@example.com",
      "full_name": "Budi Santoso",
      "phone_number": "081234567890",
      "role": "CUSTOMER",
      "created_at": "2026-11-22T15:55:00.000Z"
    }
  }
  ```

---

### 1.2 Modul Kategori & Katalog Produk (`/api/v1/categories`, `/api/v1/products`)

#### `GET /api/v1/categories`
Mengambil seluruh kategori produk aktif.
- **Response `200 OK`:**
  ```json
  {
    "success": true,
    "data": [
      {
        "id": "cat-001-uuid",
        "name": "Elektronik & Gadget",
        "slug": "elektronik-gadget",
        "description": "Perangkat pintar, laptop, dan aksesoris komputer.",
        "icon_url": "/icons/gadget.svg"
      },
      {
        "id": "cat-002-uuid",
        "name": "Peralatan Rumah Tangga",
        "slug": "peralatan-rumah-tangga",
        "description": "Kebutuhan perabot dan peralatan rumah.",
        "icon_url": "/icons/home.svg"
      }
    ]
  }
  ```

#### `GET /api/v1/products`
Mengambil daftar produk katalog dengan filter, pencarian, dan paginasi.
- **Query Parameters:**
  - `q`: String pencarian (contoh: `laptop`)
  - `category`: Slug kategori (contoh: `elektronik-gadget`)
  - `min_price`: Angka minimum (contoh: `1000000`)
  - `max_price`: Angka maksimum (contoh: `15000000`)
  - `sort`: `price_asc` | `price_desc` | `newest` | `name_asc` (default: `newest`)
  - `page`: Nomor halaman integer (default: `1`)
  - `limit`: Jumlah per halaman integer (default: `12`)
- **Response `200 OK`:**
  ```json
  {
    "success": true,
    "meta": {
      "page": 1,
      "limit": 12,
      "total_items": 45,
      "total_pages": 4
    },
    "data": [
      {
        "id": "p-101-uuid",
        "sku": "SKU-LAP-001",
        "name": "Laptop UltraBook Pro 14 Inch",
        "slug": "laptop-ultrabook-pro-14-inch",
        "category": {
          "id": "cat-001-uuid",
          "name": "Elektronik & Gadget",
          "slug": "elektronik-gadget"
        },
        "price": 12500000.00,
        "stock": 18,
        "image_url": "/images/products/ultrabook-14.webp",
        "is_active": true
      }
    ]
  }
  ```

#### `GET /api/v1/products/{id_or_slug}`
Mengambil detail satu produk lengkap.
- **Response `200 OK`:**
  ```json
  {
    "success": true,
    "data": {
      "id": "p-101-uuid",
      "sku": "SKU-LAP-001",
      "name": "Laptop UltraBook Pro 14 Inch",
      "slug": "laptop-ultrabook-pro-14-inch",
      "category_id": "cat-001-uuid",
      "description": "Laptop ultra-tipis dengan prosesor generasi terbaru, RAM 16GB, dan SSD 512GB NVMe.",
      "price": 12500000.00,
      "stock": 18,
      "image_url": "/images/products/ultrabook-14.webp",
      "version": 1,
      "is_active": true,
      "created_at": "2026-11-22T10:00:00.000Z",
      "updated_at": "2026-11-22T15:00:00.000Z"
    }
  }
  ```

---

### 1.3 Modul Keranjang Belanja (`/api/v1/cart`)
Seluruh endpoint di bawah mewajibkan header `Authorization: Bearer <access_token>`.

#### `GET /api/v1/cart`
Mengambil seluruh item keranjang belanja milik user.
- **Response `200 OK`:**
  ```json
  {
    "success": true,
    "data": {
      "items": [
        {
          "cart_item_id": "cart-001-uuid",
          "product_id": "p-101-uuid",
          "name": "Laptop UltraBook Pro 14 Inch",
          "sku": "SKU-LAP-001",
          "unit_price": 12500000.00,
          "quantity": 1,
          "subtotal": 12500000.00,
          "current_stock": 18,
          "image_url": "/images/products/ultrabook-14.webp"
        }
      ],
      "total_items": 1,
      "total_amount": 12500000.00
    }
  }
  ```

#### `POST /api/v1/cart/items`
Menambahkan item ke dalam keranjang.
- **Request Body:**
  ```json
  {
    "product_id": "p-101-uuid",
    "quantity": 1
  }
  ```
- **Response `200 OK`:**
  ```json
  {
    "success": true,
    "message": "Item berhasil ditambahkan ke keranjang.",
    "data": {
      "cart_item_id": "cart-001-uuid",
      "product_id": "p-101-uuid",
      "quantity": 1
    }
  }
  ```

#### `PUT /api/v1/cart/items/{cart_item_id}`
Mengubah kuantitas item dalam keranjang.
- **Request Body:**
  ```json
  {
    "quantity": 2
  }
  ```
- **Response `200 OK`:**
  ```json
  {
    "success": true,
    "message": "Kuantitas keranjang berhasil diperbarui."
  }
  ```

#### `DELETE /api/v1/cart/items/{cart_item_id}`
Menghapus item dari keranjang.
- **Response `200 OK`:**
  ```json
  {
    "success": true,
    "message": "Item berhasil dihapus dari keranjang."
  }
  ```

---

### 1.4 Modul Pesanan (`/api/v1/orders`)

#### `GET /api/v1/orders`
Mengambil riwayat pesanan milik user login.
- **Headers:** `Authorization: Bearer <access_token>`
- **Response `200 OK`:**
  ```json
  {
    "success": true,
    "data": [
      {
        "id": "ord-001-uuid",
        "order_number": "ORD-20261122-8F92A",
        "total_amount": 12520000.00,
        "status": "PROCESSING",
        "shipping_courier": "JNE Express",
        "shipping_cost": 20000.00,
        "created_at": "2026-11-22T15:52:45.000Z",
        "total_items_count": 1
      }
    ]
  }
  ```

#### `GET /api/v1/orders/{order_id}`
Mengambil detail pesanan dan rincian item pesanan.
- **Headers:** `Authorization: Bearer <access_token>`
- **Response `200 OK`:**
  ```json
  {
    "success": true,
    "data": {
      "id": "ord-001-uuid",
      "order_number": "ORD-20261122-8F92A",
      "status": "PROCESSING",
      "shipping_address": "Jl. Raya Telang No. 1, Bangkalan, Madura",
      "shipping_courier": "JNE Express",
      "shipping_cost": 20000.00,
      "total_amount": 12520000.00,
      "items": [
        {
          "id": "item-001-uuid",
          "product_id": "p-101-uuid",
          "product_name": "Laptop UltraBook Pro 14 Inch",
          "unit_price": 12500000.00,
          "quantity": 1,
          "subtotal": 12500000.00
        }
      ],
      "payment": {
        "payment_method": "BANK_TRANSFER",
        "payment_status": "PAID",
        "transaction_reference": "VA-BNI-981240129",
        "paid_at": "2026-11-22T15:53:10.000Z"
      },
      "created_at": "2026-11-22T15:52:45.000Z"
    }
  }
  ```

---

### 1.5 Modul Manajemen Admin (`/api/v1/admin`)
Wajib menyertakan token JWT dengan klaim `role: "ADMIN"`.

#### `POST /api/v1/admin/products`
Membuat produk baru.
- **Request Body:**
  ```json
  {
    "category_id": "cat-001-uuid",
    "sku": "SKU-MOU-002",
    "name": "Wireless Ergonomic Mouse",
    "description": "Mouse nirkabel dengan sensor optik presisi tinggi.",
    "price": 350000.00,
    "initial_stock": 50,
    "image_url": "/images/products/mouse-ergo.webp"
  }
  ```
- **Response `201 Created`:**
  ```json
  {
    "success": true,
    "message": "Produk berhasil ditambahkan.",
    "data": {
      "id": "p-102-uuid",
      "sku": "SKU-MOU-002",
      "name": "Wireless Ergonomic Mouse",
      "stock": 50,
      "version": 1
    }
  }
  ```

#### `PATCH /api/v1/admin/orders/{order_id}/status`
Memperbarui status pesanan customer.
- **Request Body:**
  ```json
  {
    "status": "SHIPPED",
    "tracking_number": "JNE1092830192"
  }
  ```
- **Response `200 OK`:**
  ```json
  {
    "success": true,
    "message": "Status pesanan berhasil diubah menjadi SHIPPED."
  }
  ```

#### `GET /api/v1/admin/stats`
Mengambil ringkasan metrik dashboard admin.
- **Response `200 OK`:**
  ```json
  {
    "success": true,
    "data": {
      "total_revenue": 145000000.00,
      "total_orders": 312,
      "total_customers": 184,
      "low_stock_products_count": 3
    }
  }
  ```

---

### 1.6 Endpoint Kesehatan Cluster (`/api/v1/health`)
Digunakan oleh Klien Web dan monitoring auditor untuk mengecek kesehatan node.
- **Response `200 OK`:**
  ```json
  {
    "status": "HEALTHY",
    "node_id": "server3_api_primary",
    "role": "COORDINATOR",
    "uptime_seconds": 18420,
    "dependencies": {
      "database": "CONNECTED",
      "server1_rpc": "ONLINE",
      "server2_rmi": "ONLINE",
      "server4_data": "ONLINE"
    },
    "timestamp": "2026-11-22T15:55:00.100Z"
  }
  ```

---

## 2. Remote Procedure Call (RPC) Contract (`server1_rpc`)

Layanan `server1_rpc` berjalan pada port `6001` (Koordinator) dan port `6101` (Pengikut).

### 2.1 Spesifikasi Framing Paket Jaringan (TCP Socket Wire Format)
Setiap panggilan RPC dikirimkan melalui koneksi TCP Socket dengan protokol **Length-Prefixed JSON-RPC 2.0**:
- **Prefix Header:** 4-Byte unsigned integer dalam format *Big-Endian (Network Byte Order)* yang menyatakan panjang payload JSON dalam bytes ($N$).
- **Payload Body:** String JSON berukuran tepat $N$ bytes di-encode dalam UTF-8.

```
+-----------------------------+------------------------------------------------------+
| 4-Byte Length Header (uint) | JSON-RPC 2.0 Payload Body (N bytes UTF-8)            |
| (Big-Endian Network Order)  | {"jsonrpc": "2.0", "method": "...", "params": {...}} |
+-----------------------------+------------------------------------------------------+
```

### 2.2 Prosedur Jarak Jauh: `process_checkout`
Menerima kumpulan item keranjang, memotong stok via RMI/Data layer, dan menyimpan data order secara transaksional.

#### RPC Request Frame:
```json
{
  "jsonrpc": "2.0",
  "id": "req-chk-9021",
  "method": "process_checkout",
  "params": {
    "idempotency_key": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
    "user_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "shipping_address": "Jl. Raya Telang No. 1, Bangkalan, Madura",
    "shipping_courier": "JNE Express",
    "shipping_cost": 20000.00,
    "payment_method": "BANK_TRANSFER",
    "items": [
      {
        "product_id": "p-101-uuid",
        "quantity": 1,
        "unit_price": 12500000.00
      }
    ]
  }
}
```

#### RPC Success Response Frame:
```json
{
  "jsonrpc": "2.0",
  "id": "req-chk-9021",
  "result": {
    "success": true,
    "order_id": "ord-001-uuid",
    "order_number": "ORD-20261122-8F92A",
    "total_amount": 12520000.00,
    "status": "PENDING",
    "payment_reference": "VA-BNI-981240129",
    "executed_by_node": "server1_rpc_coordinator",
    "processed_at": "2026-11-22T15:52:45.000Z"
  }
}
```

#### RPC Error Response Frame (Stok Kurang):
```json
{
  "jsonrpc": "2.0",
  "id": "req-chk-9021",
  "error": {
    "code": -32001,
    "message": "INSUFFICIENT_STOCK",
    "data": {
      "product_id": "p-101-uuid",
      "available_stock": 0,
      "requested_quantity": 1
    }
  }
}
```

### 2.3 Prosedur Jarak Jauh: `validate_order`
Memvalidasi kelengkapan data pesanan sebelum eksekusi pembayaran.
- **Method:** `validate_order`
- **Params:** `{"order_id": "ord-001-uuid"}`
- **Result:** `{"valid": true, "order_status": "PENDING", "amount_due": 12520000.00}`

### 2.4 Prosedur Jarak Jauh: `cancel_order`
Membatalkan pesanan dan mengembalikan reservasi stok barang ke inventaris.
- **Method:** `cancel_order`
- **Params:** `{"order_id": "ord-001-uuid", "reason": "Customer cancellation"}`
- **Result:** `{"cancelled": true, "stock_restored": true, "cancelled_at": "2026-11-22T16:00:00.000Z"}`

### 2.5 Daftar Kode Error RPC Standar

| Kode Error | Simbol Error | Penjelasan Penyebab |
| :---: | :--- | :--- |
| `-32700` | `PARSE_ERROR` | Format length prefix atau JSON payload rusak/tidak valid. |
| `-32601` | `METHOD_NOT_FOUND` | Prosedur remote yang dipanggil tidak terdaftar. |
| `-32602` | `INVALID_PARAMS` | Argumen input tidak memenuhi validasi skema skalar. |
| `-32001` | `INSUFFICIENT_STOCK` | Stok barang tidak mencukupi untuk memenuhi kuantitas permintaan. |
| `-32002` | `CONCURRENCY_CONFLICT`| Terjadi tabrakan versi *optimistic locking* setelah batas maksimal retry. |
| `-32003` | `IDEMPOTENCY_DUPLICATE`| Transaksi dengan `idempotency_key` tersebut telah berhasil diproses sebelumnya (mengembalikan data pesanan yang telah tersimpan). |
| `-32004` | `DATA_SERVICE_UNAVAILABLE`| Gagal menghubungi lapisan `server4_data`. |

---

## 3. Remote Method Invocation (RMI) Contract (`server2_rmi`)

Layanan `server2_rmi` berjalan pada port `6002` (Koordinator) dan port `6102` (Pengikut).

### 3.1 Definisi Remote Interface: `InventoryService`
Layanan diimplementasikan dalam Python OOP murni yang diekspos melalui Pyro5 daemon:

```python
import Pyro5.api

@Pyro5.api.expose
class InventoryService:
    def get_stock(self, product_id: str) -> int:
        """
        Mengembalikan jumlah stok fisik terkini untuk produk spesifik.
        """
        pass

    def batch_check_availability(self, items: list[dict]) -> dict:
        """
        Memeriksa ketersediaan stok untuk sekumpulan item dalam 1 panggilan remote.
        Items: [{"product_id": str, "quantity": int}]
        Returns: {"available": bool, "insufficient_items": list[dict]}
        """
        pass

    def reserve_stock(self, order_id: str, items: list[dict]) -> dict:
        """
        Mengunci dan memotong stok untuk pesanan dengan Optimistic Concurrency Control.
        Items: [{"product_id": str, "quantity": int}]
        Returns: {"success": bool, "reserved_items": list[dict]}
        """
        pass

    def release_stock(self, order_id: str, items: list[dict]) -> dict:
        """
        Mengembalikan kuantitas stok produk yang sebelumnya dibatalkan.
        Items: [{"product_id": str, "quantity": int}]
        Returns: {"success": bool, "released_items": list[dict]}
        """
        pass

    def restock_product(self, product_id: str, quantity: int, admin_id: str) -> dict:
        """
        Menambahkan persediaan fisik produk oleh admin toko.
        Returns: {"success": bool, "product_id": str, "previous_stock": int, "new_stock": int}
        """
        pass
```

### 3.2 Contoh Payload Pemanggilan Remote Method & Respon

#### 1. Pemanggilan `reserve_stock`
- **Input Parameters:**
  ```json
  {
    "order_id": "ord-001-uuid",
    "items": [
      { "product_id": "p-101-uuid", "quantity": 1 }
    ]
  }
  ```
- **Return Value:**
  ```json
  {
    "success": true,
    "order_id": "ord-001-uuid",
    "reserved_items": [
      { "product_id": "p-101-uuid", "quantity": 1, "remaining_stock": 17 }
    ],
    "timestamp": "2026-11-22T15:52:45.021Z"
  }
  ```

#### 2. Pemanggilan `restock_product`
- **Input Parameters:**
  ```json
  {
    "product_id": "p-101-uuid",
    "quantity": 10,
    "admin_id": "admin-001-uuid"
  }
  ```
- **Return Value:**
  ```json
  {
    "success": true,
    "product_id": "p-101-uuid",
    "previous_stock": 17,
    "added_quantity": 10,
    "new_stock": 27,
    "version": 2,
    "timestamp": "2026-11-22T16:10:00.000Z"
  }
  ```

### 3.3 Mekanisme Koneksi Klien & Transparansi Failover RMI
Klien RMI pada backend (misal saat dipanggil oleh `server1_rpc` atau Next.js proxy) menggunakan wrapper class `FailoverRMIClient`:

```python
class FailoverRMIClient:
    def __init__(self, primary_uri: str, backup_uri: str):
        self.primary_uri = primary_uri
        self.backup_uri = backup_uri
        self.active_uri = primary_uri

    def invoke(self, method_name: str, *args, **kwargs):
        try:
            with Pyro5.api.Proxy(self.active_uri) as proxy:
                proxy._pyroTimeout = 1.5 # Timeout 1.5 detik
                method = getattr(proxy, method_name)
                return method(*args, **kwargs)
        except (Pyro5.errors.CommunicationError, Pyro5.errors.TimeoutError):
            # Failover otomatis ke backup
            self.active_uri = self.backup_uri if self.active_uri == self.primary_uri else self.primary_uri
            with Pyro5.api.Proxy(self.active_uri) as backup_proxy:
                backup_proxy._pyroTimeout = 2.0
                method = getattr(backup_proxy, method_name)
                return method(*args, **kwargs)
```

Dengan kontrak yang terdefinisi secara presisi di ketiga protokol ini, komunikasi terdistribusi berjalan dengan konsistensi semantik yang tinggi, kebal terhadap kegagalan jaringan acak, dan terhindar dari ketidaksinkronan data.