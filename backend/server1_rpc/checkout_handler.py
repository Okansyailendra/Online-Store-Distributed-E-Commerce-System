import time
import uuid
import Pyro5.api
from datetime import datetime
from backend.common.config import settings
from backend.common.db_client import db_client
from backend.common.rpc_protocol import RPCError
from backend.common.logger import setup_logger

logger = setup_logger("CheckoutHandler")

class CheckoutHandler:
    def __init__(self):
        self.rmi_primary_uri = f"PYRO:InventoryService@{settings.SERVER2_RMI_PRIMARY_HOST}:{settings.SERVER2_RMI_PRIMARY_PORT}"
        self.rmi_backup_uri = f"PYRO:InventoryService@{settings.SERVER2_RMI_BACKUP_HOST}:{settings.SERVER2_RMI_BACKUP_PORT}"

    def _get_inventory_proxy(self):
        """
        Menghubungkan ke objek remote InventoryService dengan failover otomatis
        dari Primary ke Backup RMI server.
        """
        try:
            proxy = Pyro5.api.Proxy(self.rmi_primary_uri)
            proxy._pyroTimeout = settings.SOCKET_TIMEOUT
            proxy._pyroBind()
            return proxy
        except Exception:
            # Fallback ke RMI Backup
            proxy = Pyro5.api.Proxy(self.rmi_backup_uri)
            proxy._pyroTimeout = settings.SOCKET_TIMEOUT
            proxy._pyroBind()
            return proxy

    def process_checkout(self, params: dict) -> dict:
        """
        Remote Procedure: Eksekusi transaksi pembelian & checkout atomik.
        Mendukung verifikasi idempotensi, reservasi stok RMI, dan pembuatan order.
        """
        idempotency_key = params.get("idempotency_key")
        user_id = params.get("user_id")
        items = params.get("items", [])
        shipping_address = params.get("shipping_address", "")
        shipping_courier = params.get("shipping_courier", "JNE Regular")
        shipping_cost = float(params.get("shipping_cost", 0.0))
        payment_method = params.get("payment_method", "BANK_TRANSFER")

        if not idempotency_key or not user_id or not items:
            raise RPCError(-32602, "Parameter tidak lengkap: idempotency_key, user_id, dan items wajib diisi")

        # 1. Jaminan Idempotensi: Periksa apakah pesanan sudah pernah dibuat
        existing_order = db_client.query_one(
            "SELECT id, order_number, total_amount, status FROM orders WHERE idempotency_key = :k",
            {"k": idempotency_key}
        )
        if existing_order:
            logger.info(f"[RPC IDEMPOTENCY] Pesanan dengan key {idempotency_key} sudah pernah dibuat sebelumnya.")
            payment = db_client.query_one("SELECT transaction_reference FROM payments WHERE order_id = :oid", {"oid": existing_order["id"]})
            return {
                "success": True,
                "order_id": existing_order["id"],
                "order_number": existing_order["order_number"],
                "total_amount": existing_order["total_amount"],
                "status": existing_order["status"],
                "payment_reference": payment["transaction_reference"] if payment else None,
                "is_idempotent_replay": True
            }

        order_id = str(uuid.uuid4())
        date_str = datetime.now().strftime("%Y%m%d")
        short_id = uuid.uuid4().hex[:5].upper()
        order_number = f"ORD-{date_str}-{short_id}"

        # 2. Panggil Reservasi Stok via RMI
        rmi_items = [{"product_id": it["product_id"], "quantity": it["quantity"]} for it in items]
        try:
            with self._get_inventory_proxy() as inv_proxy:
                reserve_res = inv_proxy.reserve_stock(order_id, rmi_items)
        except Exception as e:
            logger.error(f"[RPC CHECKOUT] Gagal menghubungi layanan RMI Inventaris: {e}")
            raise RPCError(-32004, f"Layanan Inventaris (RMI) tidak dapat dihubungi: {e}")

        if not reserve_res.get("success"):
            err_code = -32001 if reserve_res.get("error_code") == "INSUFFICIENT_STOCK" else -32002
            raise RPCError(err_code, reserve_res.get("message", "Gagal mengalokasikan stok barang"), reserve_res)

        # 3. Hitung Total dan Rekam ke Basis Data dalam 1 Transaksi Atomik
        subtotal_sum = 0.0
        db_statements = []

        for it in items:
            item_id = str(uuid.uuid4())
            pid = it["product_id"]
            qty = int(it["quantity"])
            uprice = float(it["unit_price"])
            sub = qty * uprice
            subtotal_sum += sub

            db_statements.append({
                "sql": """
                INSERT INTO order_items (id, order_id, product_id, quantity, unit_price, subtotal)
                VALUES (:id, :order_id, :product_id, :quantity, :unit_price, :subtotal)
                """,
                "params": {
                    "id": item_id,
                    "order_id": order_id,
                    "product_id": pid,
                    "quantity": qty,
                    "unit_price": uprice,
                    "subtotal": sub
                }
            })

        total_amount = subtotal_sum + shipping_cost

        # Insert Order Induk
        db_statements.insert(0, {
            "sql": """
            INSERT INTO orders (id, order_number, user_id, total_amount, status, shipping_address, shipping_courier, shipping_cost, idempotency_key)
            VALUES (:id, :order_number, :user_id, :total_amount, 'PROCESSING', :shipping_address, :shipping_courier, :shipping_cost, :idempotency_key)
            """,
            "params": {
                "id": order_id,
                "order_number": order_number,
                "user_id": user_id,
                "total_amount": total_amount,
                "shipping_address": shipping_address,
                "shipping_courier": shipping_courier,
                "shipping_cost": shipping_cost,
                "idempotency_key": idempotency_key
            }
        })

        # Insert Payment
        payment_id = str(uuid.uuid4())
        tx_ref = f"VA-{payment_method[:3]}-{uuid.uuid4().hex[:8].upper()}"
        db_statements.append({
            "sql": """
            INSERT INTO payments (id, order_id, payment_method, payment_status, transaction_reference, amount, paid_at)
            VALUES (:id, :order_id, :payment_method, 'PAID', :transaction_reference, :amount, CURRENT_TIMESTAMP)
            """,
            "params": {
                "id": payment_id,
                "order_id": order_id,
                "payment_method": payment_method,
                "transaction_reference": tx_ref,
                "amount": total_amount
            }
        })

        # Hapus item dari Cart
        for it in items:
            db_statements.append({
                "sql": "DELETE FROM cart_items WHERE user_id = :uid AND product_id = :pid",
                "params": {"uid": user_id, "pid": it["product_id"]}
            })

        # Eksekusi Commit ke Lapisan Data
        try:
            db_client.execute_transaction(db_statements)
            logger.info(f"[RPC CHECKOUT SUCCESS] Pesanan #{order_number} berhasil dibuat ({total_amount:,.2f})")
            return {
                "success": True,
                "order_id": order_id,
                "order_number": order_number,
                "total_amount": total_amount,
                "status": "PROCESSING",
                "payment_reference": tx_ref,
                "processed_at": datetime.utcnow().isoformat() + "Z"
            }
        except Exception as ex:
            logger.error(f"[RPC CHECKOUT ROLLBACK] Gagal menyimpan order ke database: {ex}")
            # Rollback stok yang telah di-reserve
            try:
                with self._get_inventory_proxy() as inv_proxy:
                    inv_proxy.release_stock(order_id, rmi_items)
            except Exception as rmi_err:
                logger.critical(f"[COMPENSATION FAILED] Gagal mengembalikan stok RMI: {rmi_err}")
            raise RPCError(-32000, f"Gagal menyelesaikan transaksi di database: {ex}")

    def validate_order(self, params: dict) -> dict:
        order_id = params.get("order_id")
        row = db_client.query_one("SELECT id, order_number, status, total_amount FROM orders WHERE id = :id", {"id": order_id})
        if not row:
            return {"valid": False, "message": "Pesanan tidak ditemukan"}
        return {"valid": True, "order": row}

    def cancel_order(self, params: dict) -> dict:
        order_id = params.get("order_id")
        reason = params.get("reason", "Cancelled by customer")
        order = db_client.query_one("SELECT id, status FROM orders WHERE id = :id", {"id": order_id})
        if not order:
            raise RPCError(-32602, "Pesanan tidak ditemukan")

        if order["status"] == "CANCELLED":
            return {"success": True, "message": "Pesanan sudah berstatus batal sebelumnya"}

        items = db_client.query("SELECT product_id, quantity FROM order_items WHERE order_id = :oid", {"oid": order_id})
        
        # Kembalikan stok via RMI
        rmi_items = [{"product_id": it["product_id"], "quantity": it["quantity"]} for it in items]
        try:
            with self._get_inventory_proxy() as inv_proxy:
                inv_proxy.release_stock(order_id, rmi_items)
        except Exception as e:
            logger.warning(f"[CANCEL ORDER] Release stok RMI warning: {e}")

        db_client.execute("UPDATE orders SET status = 'CANCELLED', updated_at = CURRENT_TIMESTAMP WHERE id = :id", {"id": order_id})
        logger.info(f"[RPC CANCEL] Pesanan {order_id} berhasil dibatalkan. Alasan: {reason}")
        return {"success": True, "order_id": order_id, "status": "CANCELLED"}

    def get_transaction_status(self, params: dict) -> dict:
        key = params.get("idempotency_key")
        oid = params.get("order_id")
        sql = "SELECT id, order_number, status, total_amount FROM orders WHERE "
        p = {}
        if key:
            sql += "idempotency_key = :k"
            p["k"] = key
        elif oid:
            sql += "id = :oid"
            p["oid"] = oid
        else:
            raise RPCError(-32602, "Diperlukan idempotency_key atau order_id")

        row = db_client.query_one(sql, p)
        if not row:
            return {"found": False}
        return {"found": True, "transaction": row}
