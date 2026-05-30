# ============================================================
# FinRight AI — app/database.py
#
# Supabase connection + helper functions.
# All DB calls go through here — never call Supabase directly
# from routes. Use these helpers instead.
#
# SECURITY: Every helper includes user_id check so users
# can only read/write their own data.
#
# USAGE:
#   from app.database import db_fetch_all, db_insert, db_update, db_delete
# ============================================================

from supabase import create_client, Client
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# Singleton — created once, reused
_db: Client | None = None


def get_db() -> Client:
    """Returns Supabase client. Creates it once on first call."""
    global _db
    if _db is None:
        if not settings.supabase_url or not settings.supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in .env")
        _db = create_client(settings.supabase_url, settings.supabase_key)
        logger.info("✓ Supabase connected")
    return _db


async def db_fetch_all(table: str, user_id: str, filters: dict = None) -> list:
    """
    Get all rows for a user from a table.
    Optionally filter by extra columns.

    Example:
        txns = await db_fetch_all("transactions", user_id)
        goals = await db_fetch_all("goals", user_id, {"priority": "High"})
    """
    try:
        q = get_db().table(table).select("*").eq("user_id", user_id)
        if filters:
            for k, v in filters.items():
                q = q.eq(k, v)
        return q.execute().data or []
    except Exception as e:
        logger.error(f"db_fetch_all [{table}]: {e}")
        return []


async def db_insert(table: str, data: dict) -> dict | None:
    """
    Insert a new row. Returns created row or None.

    Example:
        row = await db_insert("transactions", {"id": uuid, "user_id": uid, ...})
    """
    try:
        r = get_db().table(table).insert(data).execute()
        return r.data[0] if r.data else None
    except Exception as e:
        logger.error(f"db_insert [{table}]: {e}")
        return None


async def db_update(table: str, record_id: str, user_id: str, data: dict) -> dict | None:
    """
    Update a row — only if it belongs to the user.
    Returns updated row or None.

    Example:
        row = await db_update("goals", goal_id, user_id, {"saved": 5000})
    """
    try:
        r = (get_db().table(table)
             .update(data)
             .eq("id", record_id)
             .eq("user_id", user_id)   # security check
             .execute())
        return r.data[0] if r.data else None
    except Exception as e:
        logger.error(f"db_update [{table}/{record_id}]: {e}")
        return None


async def db_delete(table: str, record_id: str, user_id: str) -> bool:
    """
    Delete a row — only if it belongs to the user.
    Returns True on success, False on error.

    Example:
        ok = await db_delete("transactions", txn_id, user_id)
    """
    try:
        (get_db().table(table)
         .delete()
         .eq("id", record_id)
         .eq("user_id", user_id)   # security check
         .execute())
        return True
    except Exception as e:
        logger.error(f"db_delete [{table}/{record_id}]: {e}")
        return False


async def db_upsert(table: str, data: dict) -> dict | None:
    """
    Insert or update a row (used for profiles, settings, taxonomy).
    Returns row or None.

    Example:
        row = await db_upsert("profiles", {"id": user_id, "currency": "NPR"})
    """
    try:
        r = get_db().table(table).upsert(data).execute()
        return r.data[0] if r.data else None
    except Exception as e:
        logger.error(f"db_upsert [{table}]: {e}")
        return None
