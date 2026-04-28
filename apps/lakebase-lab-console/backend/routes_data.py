"""Data playground routes: CRUD on workshop tables."""

import json
import re
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from .db import execute_query, execute_write

router = APIRouter(prefix="/api/data", tags=["data"])


class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str = ""
    price: float = Field(..., ge=0)
    stock_quantity: int = Field(default=0, ge=0)
    category: str = "General"
    tags: list[str] = []


class ProductUpdate(BaseModel):
    name: str | None = None
    price: float | None = None
    stock_quantity: int | None = None
    category: str | None = None


class EventCreate(BaseModel):
    event_type: str = Field(..., min_length=1)
    source: str = "manual"
    payload: dict = {}


# --- Products ---

@router.get("/products")
def list_products(category: str | None = None, limit: int = 50):
    """List products, optionally filtered by category."""
    if category:
        return execute_query(
            "SELECT * FROM products WHERE category = %s ORDER BY product_id LIMIT %s",
            (category, limit),
        )
    return execute_query(
        "SELECT * FROM products ORDER BY product_id LIMIT %s", (limit,)
    )


@router.get("/products/{product_id}")
def get_product(product_id: int):
    """Get a single product."""
    rows = execute_query(
        "SELECT * FROM products WHERE product_id = %s", (product_id,)
    )
    if not rows:
        raise HTTPException(404, "Product not found")
    return rows[0]


@router.post("/products")
def create_product(req: ProductCreate):
    """Insert a new product."""
    return execute_write(
        "INSERT INTO products (name, description, price, stock_quantity, category, tags) "
        "VALUES (%s, %s, %s, %s, %s, %s) RETURNING *",
        (req.name, req.description, req.price, req.stock_quantity, req.category, req.tags),
    )


@router.put("/products/{product_id}")
def update_product(product_id: int, req: ProductUpdate):
    """Update an existing product (partial)."""
    sets = []
    values = []
    if req.name is not None:
        sets.append("name = %s")
        values.append(req.name)
    if req.price is not None:
        sets.append("price = %s")
        values.append(req.price)
    if req.stock_quantity is not None:
        sets.append("stock_quantity = %s")
        values.append(req.stock_quantity)
    if req.category is not None:
        sets.append("category = %s")
        values.append(req.category)

    if not sets:
        raise HTTPException(400, "No fields to update")

    sets.append("updated_at = CURRENT_TIMESTAMP")
    values.append(product_id)

    return execute_write(
        f"UPDATE products SET {', '.join(sets)} WHERE product_id = %s RETURNING *",
        tuple(values),
    )


@router.delete("/products/{product_id}")
def delete_product(product_id: int):
    """Delete a product."""
    result = execute_write(
        "DELETE FROM products WHERE product_id = %s", (product_id,)
    )
    if result[0].get("rowcount", 0) == 0:
        raise HTTPException(404, "Product not found")
    return {"status": "deleted", "product_id": product_id}


# --- Events ---

@router.get("/events")
def list_events(event_type: str | None = None, limit: int = 100):
    """List recent events."""
    if event_type:
        return execute_query(
            "SELECT * FROM events WHERE event_type = %s ORDER BY created_at DESC LIMIT %s",
            (event_type, limit),
        )
    return execute_query(
        "SELECT * FROM events ORDER BY created_at DESC LIMIT %s", (limit,)
    )


@router.post("/events")
def create_event(req: EventCreate):
    """Insert a new event."""
    return execute_write(
        "INSERT INTO events (event_type, source, payload) VALUES (%s, %s, %s) RETURNING *",
        (req.event_type, req.source, json.dumps(req.payload)),
    )


@router.delete("/events/loadtest")
def clear_loadtest_events():
    """Delete all events from load tests."""
    return execute_write("DELETE FROM events WHERE event_type = 'loadtest'")


# --- Audit Log ---

@router.get("/audit")
def list_audit_log(table_name: str | None = None, limit: int = 50):
    """View the audit log."""
    if table_name:
        return execute_query(
            "SELECT * FROM audit_log WHERE table_name = %s ORDER BY created_at DESC LIMIT %s",
            (table_name, limit),
        )
    return execute_query(
        "SELECT * FROM audit_log ORDER BY created_at DESC LIMIT %s", (limit,)
    )


# --- Table stats ---

@router.get("/stats")
def table_stats():
    """Get row counts for all workshop tables."""
    tables = ["products", "events", "agent_sessions", "agent_messages", "audit_log"]
    stats = {}
    for t in tables:
        try:
            rows = execute_query(f"SELECT count(*) as cnt FROM {t}")
            stats[t] = rows[0]["cnt"]
        except Exception:
            stats[t] = -1
    return stats


class QueryRequest(BaseModel):
    sql: str = Field(..., min_length=1, max_length=5000)


_BLOCKED_PATTERNS = re.compile(
    r"\b(DROP\s+TABLE|DROP\s+SCHEMA|DROP\s+DATABASE|TRUNCATE|ALTER\s+SYSTEM|"
    r"CREATE\s+ROLE|DROP\s+ROLE|GRANT|REVOKE)\b",
    re.IGNORECASE,
)


@router.post("/query")
def run_query(req: QueryRequest):
    """Run a read-only SQL query for the SQL playground."""
    sql = req.sql.strip().rstrip(";")
    if _BLOCKED_PATTERNS.search(sql):
        raise HTTPException(400, "DDL/DCL statements are not allowed in the query playground")
    try:
        return execute_query(sql)
    except Exception as e:
        raise HTTPException(400, str(e))
