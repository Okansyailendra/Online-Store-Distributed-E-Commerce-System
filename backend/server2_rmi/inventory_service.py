import time
import Pyro5.api
from typing import Optional
from backend.common.db_client import db_client
from backend.common.logger import setup_logger

logger = setup_logger("InventoryService")

@Pyro5.api.expose
class InventoryService:
    """
    Remote Object untuk manajemen inventaris dan reservasi stok atomik
    dengan perlindungan Optimistic Concurrency Control (OCC).
    """

    def get_stock(self, product_id: str) -> int:
        row = db_client.query_one(
            "SELECT stock FROM products WHERE id = :id AND is_active = 1",
            {"id": product_id}
        )
        if not row:
            return 0
        return int(row.get("stock", 0))

    def batch_check_availability(self, items: list[dict]) -> dict:
        """
        Memeriksa ketersediaan stok untuk sekumpulan item secara serentak.
        items: [{"product_id": str, "quantity": int}]
        """
        insufficient_items = []
        for item in items:
            pid = item["product_id"]
            qty = item["quantity"]
            current_stock = self.get_stock(pid)
            if current_stock < qty:
                insufficient_items.append({
                    "product_id": pid,
                    "available_stock": current_stock,
                    "requested_quantity": qty
                })

        return {
            "available": len(insufficient_items) == 0,
            "insufficient_items": insufficient_items
        }

    def reserve_stock(self, order_id: str, items: list[dict]) -> dict:
        """
        Mengunci dan memotong stok untuk pesanan dengan Optimistic Concurrency Control.
        Jika terjadi modifikasi paralel, mencoba ulang (retry) hingga 3 kali.
        """
        max_retries = 3
        for attempt in range(max_retries):
            # 1. Pengecekan awal ketersediaan stok
            check = self.batch_check_availability(items)
            if not check["available"]:
                return {
                    "success": False,
                    "error_code": "INSUFFICIENT_STOCK",
                    "insufficient_items": check["insufficient_items"],
                    "message": "Stok tidak mencukupi untuk satu atau lebih produk."
                }

            # 2. Eksekusi pemotongan stok berbasis versioning
            reserved_items = []
            conflict = False

            for item in items:
                pid = item["product_id"]
                qty = item["quantity"]

                row = db_client.query_one(
                    "SELECT stock, version FROM products WHERE id = :id AND is_active = 1",
                    {"id": pid}
                )
                if not row or row["stock"] < qty:
                    conflict = True
                    break

                curr_ver = row["version"]
                sql = """
                UPDATE products 
                SET stock = stock - :qty, version = version + 1, updated_at = CURRENT_TIMESTAMP
                WHERE id = :id AND version = :version AND stock >= :qty
                """
                affected = db_client.execute(sql, {"qty": qty, "id": pid, "version": curr_ver})
                if affected == 0:
                    conflict = True
                    break
                else:
                    reserved_items.append({"product_id": pid, "quantity": qty, "previous_version": curr_ver})

            if conflict:
                # Rollback item yang sempat terpotong pada percobaan ini
                for res in reserved_items:
                    db_client.execute(
                        "UPDATE products SET stock = stock + :qty, version = version + 1 WHERE id = :id",
                        {"qty": res["quantity"], "id": res["product_id"]}
                    )
                time.sleep(0.05 * (attempt + 1)) # Backoff jitter 50ms, 100ms
                continue

            # Berhasil memotong seluruh stok dengan konsisten
            logger.info(f"[RMI] Stok berhasil dialokasikan untuk order {order_id}: {items}")
            return {
                "success": True,
                "order_id": order_id,
                "reserved_items": reserved_items,
                "timestamp": time.time()
            }

        return {
            "success": False,
            "error_code": "CONCURRENCY_CONFLICT",
            "message": "Gagal mengalokasikan stok akibat tingginya transaksi konkuren. Silakan coba kembali."
        }

    def release_stock(self, order_id: str, items: list[dict]) -> dict:
        """
        Mengembalikan kuantitas stok produk yang dibatalkan.
        """
        released = []
        for item in items:
            pid = item["product_id"]
            qty = item["quantity"]
            db_client.execute(
                "UPDATE products SET stock = stock + :qty, version = version + 1, updated_at = CURRENT_TIMESTAMP WHERE id = :id",
                {"qty": qty, "id": pid}
            )
            released.append({"product_id": pid, "quantity": qty})

        logger.info(f"[RMI] Stok berhasil dikembalikan untuk order {order_id}: {items}")
        return {"success": True, "order_id": order_id, "released_items": released}

    def restock_product(self, product_id: str, quantity: int, admin_id: str) -> dict:
        """
        Menambahkan persediaan fisik produk oleh admin toko.
        """
        row = db_client.query_one("SELECT stock, version FROM products WHERE id = :id", {"id": product_id})
        if not row:
            return {"success": False, "message": "Produk tidak ditemukan"}

        prev_stock = row["stock"]
        db_client.execute(
            "UPDATE products SET stock = stock + :qty, version = version + 1, updated_at = CURRENT_TIMESTAMP WHERE id = :id",
            {"qty": quantity, "id": product_id}
        )
        new_stock = prev_stock + quantity
        logger.info(f"[RMI] Admin {admin_id} menambah stok produk {product_id}: +{quantity} (Total: {new_stock})")
        return {
            "success": True,
            "product_id": product_id,
            "previous_stock": prev_stock,
            "added_quantity": quantity,
            "new_stock": new_stock
        }
