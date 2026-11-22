import uuid
from fastapi import APIRouter, HTTPException, Depends
from backend.common.db_client import db_client
from backend.server3_api.auth import get_current_user
from backend.server3_api.schemas import CartItemAddRequest, CartItemUpdateRequest

router = APIRouter(prefix="/api/v1/cart", tags=["Shopping Cart"])

@router.get("")
def get_cart(user: dict = Depends(get_current_user)):
    sql = """
    SELECT ci.id as cart_item_id, ci.product_id, ci.quantity, ci.created_at,
           p.name, p.sku, p.price as unit_price, p.stock as current_stock, p.image_url,
           (ci.quantity * p.price) as subtotal
    FROM cart_items ci
    JOIN products p ON ci.product_id = p.id
    WHERE ci.user_id = :uid
    ORDER BY ci.created_at DESC
    """
    items = db_client.query(sql, {"uid": user["id"]})
    total_amount = sum(float(it["subtotal"]) for it in items)
    return {
        "success": True,
        "data": {
            "items": items,
            "total_items": len(items),
            "total_amount": total_amount
        }
    }

@router.post("/items")
def add_to_cart(req: CartItemAddRequest, user: dict = Depends(get_current_user)):
    product = db_client.query_one("SELECT id, stock, is_active FROM products WHERE id = :pid", {"pid": req.product_id})
    if not product or not product["is_active"]:
        raise HTTPException(status_code=404, detail="Produk tidak ditemukan atau tidak aktif")

    if product["stock"] < req.quantity:
        raise HTTPException(status_code=400, detail="Stok produk tidak mencukupi")

    existing = db_client.query_one(
        "SELECT id, quantity FROM cart_items WHERE user_id = :uid AND product_id = :pid",
        {"uid": user["id"], "pid": req.product_id}
    )

    if existing:
        new_qty = existing["quantity"] + req.quantity
        if new_qty > product["stock"]:
            raise HTTPException(status_code=400, detail="Total kuantitas melebihi stok yang tersedia")
        db_client.execute(
            "UPDATE cart_items SET quantity = :qty, updated_at = CURRENT_TIMESTAMP WHERE id = :id",
            {"qty": new_qty, "id": existing["id"]}
        )
        item_id = existing["id"]
    else:
        item_id = str(uuid.uuid4())
        db_client.execute(
            "INSERT INTO cart_items (id, user_id, product_id, quantity) VALUES (:id, :uid, :pid, :qty)",
            {"id": item_id, "uid": user["id"], "pid": req.product_id, "qty": req.quantity}
        )

    return {"success": True, "message": "Item berhasil ditambahkan ke keranjang", "data": {"cart_item_id": item_id}}

@router.put("/items/{cart_item_id}")
def update_cart_item(cart_item_id: str, req: CartItemUpdateRequest, user: dict = Depends(get_current_user)):
    item = db_client.query_one(
        "SELECT ci.id, ci.product_id, p.stock FROM cart_items ci JOIN products p ON ci.product_id = p.id WHERE ci.id = :id AND ci.user_id = :uid",
        {"id": cart_item_id, "uid": user["id"]}
    )
    if not item:
        raise HTTPException(status_code=404, detail="Item keranjang tidak ditemukan")

    if req.quantity > item["stock"]:
        raise HTTPException(status_code=400, detail="Kuantitas melebihi stok produk yang tersedia")

    db_client.execute(
        "UPDATE cart_items SET quantity = :qty, updated_at = CURRENT_TIMESTAMP WHERE id = :id",
        {"qty": req.quantity, "id": cart_item_id}
    )
    return {"success": True, "message": "Kuantitas berhasil diperbarui"}

@router.delete("/items/{cart_item_id}")
def remove_cart_item(cart_item_id: str, user: dict = Depends(get_current_user)):
    affected = db_client.execute(
        "DELETE FROM cart_items WHERE id = :id AND user_id = :uid",
        {"id": cart_item_id, "uid": user["id"]}
    )
    if affected == 0:
        raise HTTPException(status_code=404, detail="Item keranjang tidak ditemukan")
    return {"success": True, "message": "Item berhasil dihapus dari keranjang"}
