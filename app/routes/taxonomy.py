# FinRight AI — Taxonomy Routes
# Custom categories: manage the Type > Category > Sub-Category dropdowns

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from app.schema import TaxonomyCreate, MessageResponse
from app.database import db_fetch_all, db_insert, db_delete, db_upsert
from app.security import get_current_user
from app.constants import DEFAULT_TAXONOMY, TRANSACTION_TYPES, MSG
import uuid

router = APIRouter(prefix="/taxonomy", tags=["Taxonomy"])


@router.get("/")
async def list_taxonomy(
    type: Optional[str] = Query(None, description="Filter by type"),
    user: dict = Depends(get_current_user)
):
    """
    Get all taxonomy items (default + custom).
    Used to populate Type > Category > Sub-Category dropdowns.
    """
    db_items = await db_fetch_all("taxonomy", user["id"])

    # Merge DB items with defaults (DB takes priority)
    db_keys = {f"{i['type']}|{i['category']}|{i['sub_category']}" for i in db_items}
    defaults = [
        {**d, "is_default": True, "is_recurring": False}
        for d in DEFAULT_TAXONOMY
        if f"{d['type']}|{d['category']}|{d['sub_category']}" not in db_keys
    ]

    all_items = db_items + defaults

    # Filter by type if requested
    if type:
        all_items = [i for i in all_items if i.get("type") == type]

    # Build structured dropdown tree
    tree = _build_tree(all_items)

    return {
        "items": all_items,
        "tree": tree,
        "total": len(all_items),
        "custom_count": len(db_items),
    }


@router.get("/tree")
async def get_taxonomy_tree(user: dict = Depends(get_current_user)):
    """
    Returns taxonomy as a nested tree for dropdown rendering:
    {
      "Expenses": {
        "Fixed": ["Rent", "Insurance", "EMI"],
        "Variable": ["Food", "Transport", ...]
      }
    }
    """
    db_items = await db_fetch_all("taxonomy", user["id"])
    db_keys = {f"{i['type']}|{i['category']}|{i['sub_category']}" for i in db_items}
    defaults = [
        {**d, "is_default": True}
        for d in DEFAULT_TAXONOMY
        if f"{d['type']}|{d['category']}|{d['sub_category']}" not in db_keys
    ]
    all_items = db_items + defaults
    return _build_tree(all_items)


@router.post("/", response_model=MessageResponse, status_code=201)
async def add_taxonomy_item(
    data: TaxonomyCreate,
    user: dict = Depends(get_current_user)
):
    """Add a custom category option"""
    # Check for duplicate
    existing = await db_fetch_all("taxonomy", user["id"])
    duplicate = any(
        i["type"] == data.type and
        i["category"] == data.category and
        i["sub_category"] == data.sub_category
        for i in existing
    )
    if duplicate:
        raise HTTPException(status_code=400, detail="This category already exists")

    row = {
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "type": data.type,
        "category": data.category,
        "sub_category": data.sub_category,
        "is_recurring": data.is_recurring,
        "is_default": False,
    }
    result = await db_insert("taxonomy", row)
    if not result:
        raise HTTPException(status_code=500, detail=MSG["server_error"])

    return MessageResponse(
        success=True,
        message=f"Added: {data.type} → {data.category} → {data.sub_category}",
        data=result
    )


@router.delete("/{item_id}", response_model=MessageResponse)
async def delete_taxonomy_item(item_id: str, user: dict = Depends(get_current_user)):
    """Remove a custom category (cannot remove default ones)"""
    items = await db_fetch_all("taxonomy", user["id"])
    item = next((i for i in items if i["id"] == item_id), None)

    if not item:
        raise HTTPException(status_code=404, detail=MSG["not_found"])
    if item.get("is_default"):
        raise HTTPException(status_code=400, detail="Cannot remove default categories")

    await db_delete("taxonomy", item_id, user["id"])
    return MessageResponse(success=True, message="Category removed")


@router.patch("/{item_id}/recurring")
async def toggle_recurring(item_id: str, user: dict = Depends(get_current_user)):
    """Toggle whether a category is recurring (shows in bills tracker)"""
    from app.database import db_fetch_all, db_update
    items = await db_fetch_all("taxonomy", user["id"])
    item = next((i for i in items if i["id"] == item_id), None)
    if not item:
        raise HTTPException(status_code=404, detail=MSG["not_found"])

    new_state = not item.get("is_recurring", False)
    await db_update("taxonomy", item_id, user["id"], {"is_recurring": new_state})
    return {"success": True, "is_recurring": new_state}


def _build_tree(items: list) -> dict:
    """Build nested Type > Category > [Sub-categories] structure"""
    tree: dict = {}
    for item in items:
        t = item.get("type", "Other")
        c = item.get("category", "Other")
        s = item.get("sub_category", "Other")
        if t not in tree:
            tree[t] = {}
        if c not in tree[t]:
            tree[t][c] = []
        if s not in tree[t][c]:
            tree[t][c].append(s)
    return tree
