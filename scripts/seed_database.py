import uuid
import sys
from pathlib import Path

# Tambahkan root path ke sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.server4_data.database import Database
from backend.common.config import settings
from backend.server3_api.auth import hash_password
from backend.common.logger import setup_logger

logger = setup_logger("DatabaseSeeder")

def seed():
    # Seed ke primary database
    db = Database(settings.DATABASE_SQLITE_PRIMARY_PATH)
    logger.info(f"Memulai seeding database pada {settings.DATABASE_SQLITE_PRIMARY_PATH}...")

    # 1. Seed Users (Admin & Customer)
    admin_id = str(uuid.uuid4())
    customer_id = str(uuid.uuid4())
    
    users = [
        {
            "id": admin_id,
            "email": "admin@sister.com",
            "password_hash": hash_password("AdminPass123!"),
            "full_name": "Administrator Toko",
            "phone_number": "081234567890",
            "role": "ADMIN"
        },
        {
            "id": customer_id,
            "email": "budi@sister.com",
            "password_hash": hash_password("BudiPass123!"),
            "full_name": "Budi Santoso",
            "phone_number": "089876543210",
            "role": "CUSTOMER"
        }
    ]

    for u in users:
        existing = db.query_one("SELECT id FROM users WHERE email = :email", {"email": u["email"]})
        if not existing:
            db.execute(
                "INSERT INTO users (id, email, password_hash, full_name, phone_number, role) VALUES (:id, :email, :password_hash, :full_name, :phone_number, :role)",
                u
            )
            logger.info(f"User ditambahkan: {u['email']} ({u['role']})")

    # 2. Seed Categories
    categories = [
        {
            "id": "cat-gadget-01",
            "name": "Elektronik & Gadget",
            "slug": "elektronik-gadget",
            "description": "Laptop, smartphone, dan perangkat komputasi pintar.",
            "icon_url": "Laptop"
        },
        {
            "id": "cat-aksesoris-02",
            "name": "Aksesoris Komputer",
            "slug": "aksesoris-komputer",
            "description": "Keyboard mekanik, mouse ergonomis, dan perlengkapan setup kerja.",
            "icon_url": "Mouse"
        },
        {
            "id": "cat-fashion-03",
            "name": "Pakaian & Fashion",
            "slug": "pakaian-fashion",
            "description": "Hoodie programmer, kaos katun premium, dan merchandise developer.",
            "icon_url": "Shirt"
        },
        {
            "id": "cat-buku-04",
            "name": "Buku & Alat Tulis",
            "slug": "buku-alat-tulis",
            "description": "Buku sistem terdistribusi, arsitektur software, dan algoritma.",
            "icon_url": "BookOpen"
        }
    ]

    for c in categories:
        existing = db.query_one("SELECT id FROM categories WHERE slug = :slug", {"slug": c["slug"]})
        if not existing:
            db.execute(
                "INSERT INTO categories (id, name, slug, description, icon_url) VALUES (:id, :name, :slug, :description, :icon_url)",
                c
            )
            logger.info(f"Kategori ditambahkan: {c['name']}")

    # 3. Seed Products
    products = [
        {
            "id": "prod-lap-001",
            "category_id": "cat-gadget-01",
            "sku": "SKU-LAP-001",
            "name": "Laptop UltraBook Pro 14 Inch",
            "slug": "laptop-ultrabook-pro-14-inch",
            "description": "Prosesor Intel Core i7 13th Gen, RAM 16GB LPDDR5, SSD 512GB NVMe, Layar 2.8K OLED 120Hz.",
            "price": 12500000.00,
            "stock": 10,
            "image_url": "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?auto=format&fit=crop&w=800&q=80"
        },
        {
            "id": "prod-lap-002",
            "category_id": "cat-gadget-01",
            "sku": "SKU-LAP-002",
            "name": "Developer Workstation Pro 16",
            "slug": "developer-workstation-pro-16",
            "description": "Chip Apple M3 Pro, 36GB Unified Memory, SSD 1TB, Layar Liquid Retina XDR 16 Inch.",
            "price": 28900000.00,
            "stock": 5,
            "image_url": "https://images.unsplash.com/photo-1541807084-5c52b6b3adef?auto=format&fit=crop&w=800&q=80"
        },
        {
            "id": "prod-mou-001",
            "category_id": "cat-aksesoris-02",
            "sku": "SKU-MOU-001",
            "name": "Wireless Ergonomic Mouse Silent",
            "slug": "wireless-ergonomic-mouse-silent",
            "description": "Sensor optik 4000 DPI, koneksi Bluetooth & Dongle 2.4Ghz, tombol klik hening, daya tahan baterai 3 bulan.",
            "price": 350000.00,
            "stock": 25,
            "image_url": "https://images.unsplash.com/photo-1527864550417-7fd91fc51a46?auto=format&fit=crop&w=800&q=80"
        },
        {
            "id": "prod-key-001",
            "category_id": "cat-aksesoris-02",
            "sku": "SKU-KEY-001",
            "name": "Mechanical Keyboard 75% Tactical RGB",
            "slug": "mechanical-keyboard-75-tactical-rgb",
            "description": "Gateron Brown Switch hot-swappable, PBT double-shot keycaps, gasket mount, RGB 16.8 juta warna.",
            "price": 850000.00,
            "stock": 15,
            "image_url": "https://images.unsplash.com/photo-1587829741301-dc798b83add3?auto=format&fit=crop&w=800&q=80"
        },
        {
            "id": "prod-hod-001",
            "category_id": "cat-fashion-03",
            "sku": "SKU-HOD-001",
            "name": "Hoodie Developer Binary Edition",
            "slug": "hoodie-developer-binary-edition",
            "description": "Bahan katun fleece 330 gsm tebal & lembut, sablon plastisol premium motif binary system terdistribusi.",
            "price": 285000.00,
            "stock": 30,
            "image_url": "https://images.unsplash.com/photo-1556905055-8f358a7a47b2?auto=format&fit=crop&w=800&q=80"
        },
        {
            "id": "prod-tsh-001",
            "category_id": "cat-fashion-03",
            "sku": "SKU-TSH-001",
            "name": "T-Shirt Distro 'There is no cloud, just someone elses computer'",
            "slug": "tshirt-distro-cloud-joke",
            "description": "Kaos combed 24s adem, sablon discharge menyatu dengan kain, warna hitam elegan.",
            "price": 120000.00,
            "stock": 40,
            "image_url": "https://images.unsplash.com/photo-1521572267360-ee0c2909d518?auto=format&fit=crop&w=800&q=80"
        },
        {
            "id": "prod-bok-001",
            "category_id": "cat-buku-04",
            "sku": "SKU-BOK-001",
            "name": "Buku Konsep Sistem Terdistribusi Modern",
            "slug": "buku-konsep-sistem-terdistribusi-modern",
            "description": "Panduan komprehensif toleransi kesalahan, konsensus Raft, replikasi data, RPC, RMI, dan arsitektur terdesentralisasi.",
            "price": 145000.00,
            "stock": 50,
            "image_url": "https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?auto=format&fit=crop&w=800&q=80"
        },
        {
            "id": "prod-bok-002",
            "category_id": "cat-buku-04",
            "sku": "SKU-BOK-002",
            "name": "Designing Data-Intensive Applications",
            "slug": "designing-data-intensive-applications",
            "description": "Edisi Bahasa Indonesia: Kunci keandalan, skalabilitas, dan kemudahan pemeliharaan sistem data terdistribusi.",
            "price": 295000.00,
            "stock": 20,
            "image_url": "https://images.unsplash.com/photo-1532012164546-f432f2e3777f?auto=format&fit=crop&w=800&q=80"
        }
    ]

    for p in products:
        existing = db.query_one("SELECT id FROM products WHERE sku = :sku", {"sku": p["sku"]})
        if not existing:
            db.execute(
                """
                INSERT INTO products (id, category_id, sku, name, slug, description, price, stock, image_url, version, is_active)
                VALUES (:id, :category_id, :sku, :name, :slug, :description, :price, :stock, :image_url, 1, 1)
                """,
                p
            )
            logger.info(f"Produk ditambahkan: {p['name']} (Stok: {p['stock']}, Rp {p['price']:,.0f})")

    # Sinkronkan juga ke backup db jika ada
    import shutil
    try:
        shutil.copyfile(settings.DATABASE_SQLITE_PRIMARY_PATH, settings.DATABASE_SQLITE_BACKUP_PATH)
        logger.info(f"Basis data backup disinkronkan ke {settings.DATABASE_SQLITE_BACKUP_PATH}")
    except Exception as e:
        logger.warning(f"Gagal menyalin ke backup db: {e}")

    logger.info("=== SEEDING DATABASE SELESAI DENGAN SUKSES! ===")

if __name__ == "__main__":
    seed()
