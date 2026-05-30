# FinRight AI — Shopping List Routes
# Create lists, add items, check/uncheck, delete

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.database import db_fetch_all, db_insert, db_update, db_delete
from app.security import get_current_user
from app.constants import MSG
import uuid

router = APIRouter(prefix="/shopping", tags=["Shopping Lists"])


# ── Schemas ──────────────────────────────────────────────────
class ShoppingItemCreate(BaseModel):
    name: str
    amount: float = 0
    list_name: str = "My List"
    list_id: Optional[str] = None
    priority: str = "Normal"
    quantity: int = 1


class ShoppingItemUpdate(BaseModel):
    name: Optional[str] = None
    amount: Optional[float] = None
    checked: Optional[bool] = None
    priority: Optional[str] = None
    quantity: Optional[int] = None


# ── Routes ───────────────────────────────────────────────────
@router.get("/")
async def list_shopping_lists(user: dict = Depends(get_current_user)):
    """
    Get all shopping items grouped by list name.
    Returns each list with its items, total amount, and completion %.
    """
    items = await db_fetch_all("shopping_items", user["id"])

    # Group by list_name
    lists: dict = {}
    for item in items:
        list_name = item.get("list_name") or "My List"
        if list_name not in lists:
            lists[list_name] = {
                "name": list_name,
                "list_id": item.get("list_id"),
                "items": [],
                "total_amount": 0,
                "checked_count": 0,
            }
        lists[list_name]["items"].append(item)
        lists[list_name]["total_amount"] += item.get("amount", 0)
        if item.get("checked"):
            lists[list_name]["checked_count"] += 1

    # Add completion percentage
    result = []
    for lst in lists.values():
        total = len(lst["items"])
        lst["completion_pct"] = round(lst["checked_count"] / total * 100) if total else 0
        result.append(lst)

    return {
        "lists": sorted(result, key=lambda x: x["name"]),
        "total_lists": len(result),
        "total_items": len(items),
    }


@router.get("/{list_name}")
async def get_list(list_name: str, user: dict = Depends(get_current_user)):
    """Get all items in a specific shopping list"""
    items = await db_fetch_all("shopping_items", user["id"])
    list_items = [i for i in items if i.get("list_name") == list_name]

    if not list_items:
        return {"list_name": list_name, "items": [], "total_amount": 0}

    total = sum(i.get("amount", 0) for i in list_items)
    checked = sum(1 for i in list_items if i.get("checked"))

    return {
        "list_name": list_name,
        "items": list_items,
        "total_amount": total,
        "checked_count": checked,
        "completion_pct": round(checked / len(list_items) * 100) if list_items else 0,
    }


@router.post("/items", status_code=201)
async def add_item(data: ShoppingItemCreate, user: dict = Depends(get_current_user)):
    """Add an item to a shopping list"""
    row = {
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "name": data.name,
        "amount": data.amount,
        "list_name": data.list_name,
        "list_id": data.list_id or str(uuid.uuid4()),
        "priority": data.priority,
        "quantity": data.quantity,
        "checked": False,
    }
    result = await db_insert("shopping_items", row)
    if not result:
        raise HTTPException(status_code=500, detail=MSG["server_error"])
    return {"success": True, "message": "Item added", "data": result}


@router.patch("/items/{item_id}")
async def update_item(
    item_id: str,
    data: ShoppingItemUpdate,
    user: dict = Depends(get_current_user)
):
    """Update an item — including checking/unchecking"""
    updates = data.model_dump(exclude_none=True)
    result = await db_update("shopping_items", item_id, user["id"], updates)
    if not result:
        raise HTTPException(status_code=404, detail=MSG["not_found"])
    return {"success": True, "message": "Item updated", "data": result}


@router.patch("/items/{item_id}/toggle")
async def toggle_item(item_id: str, user: dict = Depends(get_current_user)):
    """Toggle an item's checked state"""
    items = await db_fetch_all("shopping_items", user["id"])
    item = next((i for i in items if i["id"] == item_id), None)
    if not item:
        raise HTTPException(status_code=404, detail=MSG["not_found"])

    new_state = not item.get("checked", False)
    result = await db_update("shopping_items", item_id, user["id"], {"checked": new_state})
    return {"success": True, "checked": new_state, "data": result}


@router.delete("/items/{item_id}")
async def delete_item(item_id: str, user: dict = Depends(get_current_user)):
    """Delete a shopping item"""
    success = await db_delete("shopping_items", item_id, user["id"])
    if not success:
        raise HTTPException(status_code=404, detail=MSG["not_found"])
    return {"success": True, "message": "Item removed"}


@router.delete("/lists/{list_name}")
async def delete_list(list_name: str, user: dict = Depends(get_current_user)):
    """Delete an entire shopping list"""
    items = await db_fetch_all("shopping_items", user["id"])
    list_items = [i for i in items if i.get("list_name") == list_name]

    count = 0
    for item in list_items:
        if await db_delete("shopping_items", item["id"], user["id"]):
            count += 1

    return {"success": True, "message": f"Deleted list with {count} items"}
