from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from backend.common.db_client import db_client

router = APIRouter(prefix="/api/v1", tags=["Products & Categories"])

@router.get("/categories")
def get_categories():
    rows = db_client.query("SELECT id, name, slug, description, icon_url FROM categories ORDER BY name ASC")
    return {"success": True, "data": rows}

@router.get("/products")
def get_products(
    q: Optional[str] = None,
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    sort: str = "newest",
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=12, ge=1, le=100)
):
    conditions = ["p.is_active = 1"]
    params = {}

    if q:
        conditions.append("(p.name LIKE :q OR p.description LIKE :q)")
        params["q"] = f"%{q}%"

    if category:
        conditions.append("c.slug = :category")
        params["category"] = category

    if min_price is not None:
        conditions.append("p.price >= :min_price")
        params["min_price"] = min_price

    if max_price is not None:
        conditions.append("p.price <= :max_price")
        params["max_price"] = max_price

    where_clause = " WHERE " + " AND ".join(conditions)

    # Sorting
    sort_dict = {
        "price_asc": "p.price ASC",
        "price_desc": "p.price DESC",
        "name_asc": "p.name ASC",
        "newest": "p.created_at DESC"
    }
    order_clause = f" ORDER BY {sort_dict.get(sort, 'p.created_at DESC')}"

    # Hitung total
    count_sql = f"SELECT COUNT(*) as total FROM products p LEFT JOIN categories c ON p.category_id = c.id {where_clause}"
    count_row = db_client.query_one(count_sql, params)
    total_items = count_row["total"] if count_row else 0

    # Paginasi
    offset = (page - 1) * limit
    params["limit"] = limit
    params["offset"] = offset

    data_sql = f"""
    SELECT p.id, p.sku, p.name, p.slug, p.price, p.stock, p.image_url, p.is_active, p.version,
           c.id as category_id, c.name as category_name, c.slug as category_slug
    FROM products p
    LEFT JOIN categories c ON p.category_id = c.id
    {where_clause}
    {order_clause}
    LIMIT :limit OFFSET :offset
    """
    rows = db_client.query(data_sql, params)

    total_pages = (total_items + limit - 1) // limit

    return {
        "success": True,
        "meta": {
            "page": page,
            "limit": limit,
            "total_items": total_items,
            "total_pages": total_pages
        },
        "data": rows
    }

@router.get("/products/{id_or_slug}")
def get_product_detail(id_or_slug: str):
    sql = """
    SELECT p.id, p.sku, p.name, p.slug, p.description, p.price, p.stock, p.image_url, p.version, p.is_active, p.created_at, p.updated_at,
           c.id as category_id, c.name as category_name, c.slug as category_slug
    FROM products p
    LEFT JOIN categories c ON p.category_id = c.id
    WHERE p.id = :id OR p.slug = :id
    """
    row = db_client.query_one(sql, {"id": id_or_slug})
    if not row:
        raise HTTPException(status_code=404, detail="Produk tidak ditemukan")
    return {"success": True, "data": row}
