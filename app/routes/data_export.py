# FinRight AI — Data & Export Routes
# Export transactions as CSV, full data backup, import data

from fastapi import APIRouter, Depends, Query, Response
from fastapi.responses import StreamingResponse
from typing import Optional
from app.database import db_fetch_all
from app.security import get_current_user
import csv
import io
import json
from datetime import datetime

router = APIRouter(prefix="/data", tags=["Data & Export"])


@router.get("/export/csv")
async def export_transactions_csv(
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    type: Optional[str] = Query(None),
    user: dict = Depends(get_current_user)
):
    """
    Export transactions as a CSV file.
    Downloads directly in the browser.
    """
    txns = await db_fetch_all("transactions", user["id"])

    # Apply filters
    if type:
        txns = [t for t in txns if t.get("type") == type]
    if date_from:
        txns = [t for t in txns if t.get("date", "") >= date_from]
    if date_to:
        txns = [t for t in txns if t.get("date", "") <= date_to]

    # Sort by date
    txns.sort(key=lambda t: t.get("date", ""), reverse=True)

    # Build CSV
    output = io.StringIO()
    writer = csv.writer(output)

    # Header row
    writer.writerow([
        "Date", "Type", "Category", "Sub-Category",
        "Amount", "Currency", "Account", "Note", "Recurring"
    ])

    # Data rows
    for t in txns:
        writer.writerow([
            t.get("date", ""),
            t.get("type", ""),
            t.get("category", ""),
            t.get("sub_category", ""),
            t.get("amount", 0),
            t.get("orig_currency", "NPR"),
            t.get("account", ""),
            t.get("note", ""),
            "Yes" if t.get("is_recurring") else "No",
        ])

    output.seek(0)
    filename = f"finright-transactions-{datetime.now().strftime('%Y%m%d')}.csv"

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/export/json")
async def export_full_backup(user: dict = Depends(get_current_user)):
    """
    Full data backup as JSON.
    Exports: transactions, goals, accounts, budgets, taxonomy, profile.
    """
    uid = user["id"]

    # Load all user data
    txns      = await db_fetch_all("transactions", uid)
    goals     = await db_fetch_all("goals", uid)
    accounts  = await db_fetch_all("accounts", uid)
    budgets   = await db_fetch_all("budgets", uid)
    taxonomy  = await db_fetch_all("taxonomy", uid)
    profiles  = await db_fetch_all("profiles", uid)
    shopping  = await db_fetch_all("shopping_items", uid)
    income    = await db_fetch_all("income_sources", uid)

    backup = {
        "export_date": datetime.now().isoformat(),
        "app": "FinRight AI",
        "version": "1.0.0",
        "user_id": uid,
        "data": {
            "transactions":   txns,
            "goals":          goals,
            "accounts":       accounts,
            "budgets":        budgets,
            "taxonomy":       taxonomy,
            "profile":        profiles[0] if profiles else {},
            "shopping_items": shopping,
            "income_sources": income,
        },
        "stats": {
            "total_transactions": len(txns),
            "total_goals":        len(goals),
            "total_accounts":     len(accounts),
        }
    }

    json_str = json.dumps(backup, indent=2, default=str)
    filename = f"finright-backup-{datetime.now().strftime('%Y%m%d')}.json"

    return StreamingResponse(
        iter([json_str]),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/summary")
async def data_summary(user: dict = Depends(get_current_user)):
    """
    Summary of all data stored for the user.
    Shown in Settings > Data & Export page.
    """
    uid = user["id"]
    txns     = await db_fetch_all("transactions", uid)
    goals    = await db_fetch_all("goals", uid)
    accounts = await db_fetch_all("accounts", uid)
    budgets  = await db_fetch_all("budgets", uid)
    shopping = await db_fetch_all("shopping_items", uid)
    taxonomy = await db_fetch_all("taxonomy", uid)

    # Date range of transactions
    dates = sorted(t.get("date", "") for t in txns if t.get("date"))
    date_range = f"{dates[0]} → {dates[-1]}" if dates else "No data"

    return {
        "transactions": len(txns),
        "goals": len(goals),
        "accounts": len(accounts),
        "budgets": len(budgets),
        "shopping_items": len(shopping),
        "custom_categories": len([t for t in taxonomy if not t.get("is_default")]),
        "date_range": date_range,
        "last_transaction": dates[-1] if dates else None,
    }


@router.delete("/delete-all")
async def delete_all_data(
    confirm: str = Query(..., description="Must be 'DELETE_ALL_MY_DATA' to confirm"),
    user: dict = Depends(get_current_user)
):
    """
    ⚠ DANGER: Delete ALL user data.
    Requires explicit confirmation string.
    """
    if confirm != "DELETE_ALL_MY_DATA":
        return {"success": False, "message": "Incorrect confirmation string"}

    from app.database import get_db
    db = get_db()
    uid = user["id"]

    tables = [
        "transactions", "goals", "accounts", "budgets",
        "taxonomy", "shopping_items", "income_sources",
        "activity_log", "org_settings"
    ]

    deleted = {}
    for table in tables:
        try:
            result = db.table(table).delete().eq("user_id", uid).execute()
            deleted[table] = True
        except Exception as e:
            deleted[table] = f"Error: {e}"

    # Reset profile but keep it
    db.table("profiles").update({
        "onboarded": False,
        "currency": "NPR",
    }).eq("id", uid).execute()

    return {
        "success": True,
        "message": "All data deleted. Your account still exists.",
        "deleted": deleted
    }
