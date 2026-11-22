import sqlite3
import threading
from pathlib import Path
from typing import Any, Optional
from backend.common.logger import setup_logger

logger = setup_logger("DatabaseEngine")

SCHEMA_SQL = """
-- 1. Tabel Users
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    full_name TEXT NOT NULL,
    phone_number TEXT,
    role TEXT NOT NULL DEFAULT 'CUSTOMER' CHECK (role IN ('CUSTOMER', 'ADMIN', 'OBSERVER')),
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 2. Tabel Categories
CREATE TABLE IF NOT EXISTS categories (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    slug TEXT NOT NULL UNIQUE,
    description TEXT,
    icon_url TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 3. Tabel Products
CREATE TABLE IF NOT EXISTS products (
    id TEXT PRIMARY KEY,
    category_id TEXT NOT NULL REFERENCES categories(id) ON DELETE RESTRICT,
    sku TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    slug TEXT NOT NULL UNIQUE,
    description TEXT,
    price REAL NOT NULL CHECK (price >= 0),
    stock INTEGER NOT NULL DEFAULT 0 CHECK (stock >= 0),
    image_url TEXT,
    version INTEGER NOT NULL DEFAULT 1,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 4. Tabel Cart Items
CREATE TABLE IF NOT EXISTS cart_items (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    product_id TEXT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    quantity INTEGER NOT NULL DEFAULT 1 CHECK (quantity > 0),
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, product_id)
);

-- 5. Tabel Orders
CREATE TABLE IF NOT EXISTS orders (
    id TEXT PRIMARY KEY,
    order_number TEXT NOT NULL UNIQUE,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    total_amount REAL NOT NULL CHECK (total_amount >= 0),
    status TEXT NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'PAID', 'PROCESSING', 'SHIPPED', 'DELIVERED', 'CANCELLED')),
    shipping_address TEXT NOT NULL,
    shipping_courier TEXT NOT NULL,
    shipping_cost REAL NOT NULL DEFAULT 0.00 CHECK (shipping_cost >= 0),
    idempotency_key TEXT NOT NULL UNIQUE,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 6. Tabel Order Items
CREATE TABLE IF NOT EXISTS order_items (
    id TEXT PRIMARY KEY,
    order_id TEXT NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    product_id TEXT NOT NULL REFERENCES products(id) ON DELETE RESTRICT,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price REAL NOT NULL CHECK (unit_price >= 0),
    subtotal REAL NOT NULL CHECK (subtotal >= 0),
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 7. Tabel Payments
CREATE TABLE IF NOT EXISTS payments (
    id TEXT PRIMARY KEY,
    order_id TEXT NOT NULL UNIQUE REFERENCES orders(id) ON DELETE CASCADE,
    payment_method TEXT NOT NULL CHECK (payment_method IN ('BANK_TRANSFER', 'E_WALLET', 'COD')),
    payment_status TEXT NOT NULL DEFAULT 'UNPAID' CHECK (payment_status IN ('UNPAID', 'PAID', 'FAILED')),
    transaction_reference TEXT UNIQUE,
    amount REAL NOT NULL CHECK (amount >= 0),
    paid_at TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 8. Tabel Cluster Failover Logs
CREATE TABLE IF NOT EXISTS cluster_failover_logs (
    id TEXT PRIMARY KEY,
    service_name TEXT NOT NULL,
    previous_coordinator TEXT NOT NULL,
    promoted_node TEXT NOT NULL,
    reason TEXT NOT NULL,
    event_timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
    details TEXT
);

-- Indeks
CREATE INDEX IF NOT EXISTS idx_products_category ON products (category_id, price);
CREATE INDEX IF NOT EXISTS idx_products_sku ON products (sku);
CREATE INDEX IF NOT EXISTS idx_orders_user ON orders (user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_orders_idempotency ON orders (idempotency_key);
CREATE INDEX IF NOT EXISTS idx_failover_ts ON cluster_failover_logs (event_timestamp DESC);
"""

class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._local = threading.local()
        self._lock = threading.Lock()
        self._ensure_db_dir()
        self._init_schema()

    def _ensure_db_dir(self):
        p = Path(self.db_path)
        p.parent.mkdir(parents=True, exist_ok=True)

    def _get_connection(self) -> sqlite3.Connection:
        if not hasattr(self._local, "conn") or self._local.conn is None:
            conn = sqlite3.connect(self.db_path, check_same_thread=False, timeout=10.0)
            conn.row_factory = sqlite3.Row
            # Aktifkan WAL mode untuk performa baca/tulis konkuren tinggi
            conn.execute("PRAGMA journal_mode = WAL;")
            conn.execute("PRAGMA synchronous = NORMAL;")
            conn.execute("PRAGMA busy_timeout = 5000;")
            conn.execute("PRAGMA foreign_keys = ON;")
            self._local.conn = conn
        return self._local.conn

    def _init_schema(self):
        with self._lock:
            conn = sqlite3.connect(self.db_path, timeout=10.0)
            try:
                conn.executescript(SCHEMA_SQL)
                conn.commit()
                logger.info(f"[DATABASE] Skema 8 tabel berhasil diverifikasi/diinisialisasi pada {self.db_path}")
            finally:
                conn.close()

    def query(self, sql: str, params: Optional[dict] = None) -> list[dict]:
        conn = self._get_connection()
        cur = conn.cursor()
        try:
            if params:
                cur.execute(sql, params)
            else:
                cur.execute(sql)
            rows = cur.fetchall()
            return [dict(row) for row in rows]
        finally:
            cur.close()

    def query_one(self, sql: str, params: Optional[dict] = None) -> Optional[dict]:
        rows = self.query(sql, params)
        return rows[0] if rows else None

    def execute(self, sql: str, params: Optional[dict] = None) -> int:
        with self._lock:
            conn = self._get_connection()
            cur = conn.cursor()
            try:
                if params:
                    cur.execute(sql, params)
                else:
                    cur.execute(sql)
                conn.commit()
                return cur.rowcount
            finally:
                cur.close()

    def execute_transaction(self, statements: list[dict]) -> bool:
        """
        statements: [{"sql": str, "params": dict}, ...]
        """
        with self._lock:
            conn = self._get_connection()
            cur = conn.cursor()
            try:
                conn.execute("BEGIN TRANSACTION;")
                for stmt in statements:
                    sql = stmt["sql"]
                    params = stmt.get("params", {})
                    cur.execute(sql, params)
                conn.commit()
                return True
            except Exception as e:
                conn.rollback()
                logger.error(f"[DATABASE] Transaksi rollback akibat error: {e}")
                raise e
            finally:
                cur.close()
