from fastapi import APIRouter, HTTPException, Depends
from backend.common.db_client import db_client
from backend.server3_api.auth import get_current_user

router = APIRouter(prefix="/api/v1/orders", tags=["Orders"])

@router.get("")
def get_orders(user: dict = Depends(get_current_user)):
    sql = """
    SELECT o.id, o.order_number, o.total_amount, o.status, o.shipping_courier, o.shipping_cost, o.created_at,
           COUNT(oi.id) as total_items_count
    FROM orders o
    LEFT JOIN order_items oi ON o.id = oi.order_id
    WHERE o.user_id = :uid
    GROUP BY o.id
    ORDER BY o.created_at DESC
    """
    orders = db_client.query(sql, {"uid": user["id"]})
    return {"success": True, "data": orders}

@router.get("/{order_id}")
def get_order_detail(order_id: str, user: dict = Depends(get_current_user)):
    order_sql = """
    SELECT id, order_number, user_id, total_amount, status, shipping_address, shipping_courier, shipping_cost, created_at, updated_at
    FROM orders
    WHERE id = :id OR order_number = :id
    """
    order = db_client.query_one(order_sql, {"id": order_id})
    if not order:
        raise HTTPException(status_code=404, detail="Pesanan tidak ditemukan")

    # Pastikan user hanya dapat mengakses pesanannya sendiri kecuali Admin
    if order["user_id"] != user["id"] and user.get("role") != "ADMIN":
        raise HTTPException(status_code=403, detail="Akses ditolak")

    items_sql = """
    SELECT oi.id, oi.product_id, oi.quantity, oi.unit_price, oi.subtotal,
           p.name as product_name, p.image_url
    FROM order_items oi
    JOIN products p ON oi.product_id = p.id
    WHERE oi.order_id = :oid
    """
    items = db_client.query(items_sql, {"oid": order["id"]})

    payment_sql = "SELECT payment_method, payment_status, transaction_reference, amount, paid_at FROM payments WHERE order_id = :oid"
    payment = db_client.query_one(payment_sql, {"oid": order["id"]})

    return {
        "success": True,
        "data": {
            **order,
            "items": items,
            "payment": payment
        }
    }
