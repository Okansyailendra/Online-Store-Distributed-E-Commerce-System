import uuid
import Pyro5.api
from fastapi import APIRouter, HTTPException, Depends
from backend.common.config import settings
from backend.common.db_client import db_client
from backend.server3_api.auth import get_admin_user
from backend.server3_api.schemas import ProductCreateRequest, ProductUpdateRequest, OrderStatusUpdateRequest, RestockRequest

router = APIRouter(prefix="/api/v1/admin", tags=["Admin Portal"])

def get_inventory_proxy():
    primary_uri = f"PYRO:InventoryService@{settings.SERVER2_RMI_PRIMARY_HOST}:{settings.SERVER2_RMI_PRIMARY_PORT}"
    backup_uri = f"PYRO:InventoryService@{settings.SERVER2_RMI_BACKUP_HOST}:{settings.SERVER2_RMI_BACKUP_PORT}"
    try:
        p = Pyro5.api.Proxy(primary_uri)
        p._pyroTimeout = 1.5
        p._pyroBind()
        return p
    except Exception:
        p = Pyro5.api.Proxy(backup_uri)
        p._pyroTimeout = 1.5
        p._pyroBind()
        return p

@router.get("/stats")
def get_admin_stats(admin: dict = Depends(get_admin_user)):
    rev_row = db_client.query_one("SELECT COALESCE(SUM(total_amount), 0) as total_rev FROM orders WHERE status != 'CANCELLED'")
    orders_row = db_client.query_one("SELECT COUNT(*) as total_orders FROM orders")
    cust_row = db_client.query_one("SELECT COUNT(*) as total_cust FROM users WHERE role = 'CUSTOMER'")
    low_stock_row = db_client.query_one("SELECT COUNT(*) as low_stock FROM products WHERE stock < 5 AND is_active = 1")

    return {
        "success": True,
        "data": {
            "total_revenue": rev_row["total_rev"] if rev_row else 0.0,
            "total_orders": orders_row["total_orders"] if orders_row else 0,
            "total_customers": cust_row["total_cust"] if cust_row else 0,
            "low_stock_products_count": low_stock_row["low_stock"] if low_stock_row else 0
        }
    }

@router.get("/orders")
def get_all_orders(admin: dict = Depends(get_admin_user)):
    sql = """
    SELECT o.id, o.order_number, o.user_id, u.full_name as customer_name, u.email as customer_email,
           o.total_amount, o.status, o.shipping_courier, o.created_at
    FROM orders o
    JOIN users u ON o.user_id = u.id
    ORDER BY o.created_at DESC
    """
    orders = db_client.query(sql)
    return {"success": True, "data": orders}

@router.patch("/orders/{order_id}/status")
def update_order_status(order_id: str, req: OrderStatusUpdateRequest, admin: dict = Depends(get_admin_user)):
    order = db_client.query_one("SELECT id, status FROM orders WHERE id = :id", {"id": order_id})
    if not order:
        raise HTTPException(status_code=404, detail="Pesanan tidak ditemukan")

    db_client.execute(
        "UPDATE orders SET status = :st, updated_at = CURRENT_TIMESTAMP WHERE id = :id",
        {"st": req.status, "id": order_id}
    )
    return {"success": True, "message": f"Status pesanan berhasil diubah menjadi {req.status}"}

@router.post("/products")
def create_product(req: ProductCreateRequest, admin: dict = Depends(get_admin_user)):
    prod_id = str(uuid.uuid4())
    slug = req.name.lower().replace(" ", "-") + "-" + uuid.uuid4().hex[:4]

    sql = """
    INSERT INTO products (id, category_id, sku, name, slug, description, price, stock, image_url, version, is_active)
    VALUES (:id, :cid, :sku, :name, :slug, :desc, :price, :stock, :img, 1, 1)
    """
    db_client.execute(sql, {
        "id": prod_id,
        "cid": req.category_id,
        "sku": req.sku,
        "name": req.name,
        "slug": slug,
        "desc": req.description,
        "price": req.price,
        "stock": req.initial_stock,
        "img": req.image_url
    })

    return {"success": True, "message": "Produk berhasil ditambahkan", "data": {"id": prod_id, "slug": slug}}

@router.put("/products/{product_id}")
def update_product(product_id: str, req: ProductUpdateRequest, admin: dict = Depends(get_admin_user)):
    fields = []
    params = {"id": product_id}

    if req.name is not None:
        fields.append("name = :name")
        params["name"] = req.name
    if req.description is not None:
        fields.append("description = :desc")
        params["desc"] = req.description
    if req.price is not None:
        fields.append("price = :price")
        params["price"] = req.price
    if req.is_active is not None:
        fields.append("is_active = :active")
        params["active"] = 1 if req.is_active else 0
    if req.image_url is not None:
        fields.append("image_url = :img")
        params["img"] = req.image_url

    if not fields:
        return {"success": True, "message": "Tidak ada perubahan"}

    fields.append("updated_at = CURRENT_TIMESTAMP")
    sql = f"UPDATE products SET {', '.join(fields)} WHERE id = :id"
    db_client.execute(sql, params)
    return {"success": True, "message": "Data produk berhasil diperbarui"}

@router.delete("/products/{product_id}")
def delete_product(product_id: str, admin: dict = Depends(get_admin_user)):
    # Soft delete agar integritas relasional pesanan masa lalu tidak terputus
    db_client.execute("UPDATE products SET is_active = 0, updated_at = CURRENT_TIMESTAMP WHERE id = :id", {"id": product_id})
    return {"success": True, "message": "Produk berhasil dinonaktifkan (soft-delete)"}

@router.post("/inventory/restock")
def restock_product_rmi(req: RestockRequest, admin: dict = Depends(get_admin_user)):
    """
    Menambah stok melalui pemanggilan objek RMI InventoryService
    """
    try:
        with get_inventory_proxy() as proxy:
            res = proxy.restock_product(req.product_id, req.quantity, admin["id"])
            return {"success": True, "data": res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal memanggil RMI restock_product: {e}")
