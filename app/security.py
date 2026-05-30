# ============================================================
# FinRight AI — app/security.py
#
# Authentication, password hashing, rate limiting.
#
# TO PROTECT AN ENDPOINT add this parameter:
#   user = Depends(get_current_user)
#
# Example:
#   @router.get("/my-data")
#   async def get_data(user = Depends(get_current_user)):
#       user_id = user["id"]
# ============================================================

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.database import get_db
from app.constants import MSG, MAX_LOGIN_ATTEMPTS, LOCKOUT_SECONDS, PASSWORD_MIN_LENGTH
from collections import defaultdict
from datetime import datetime, timedelta
from passlib.context import CryptContext
import logging

logger = logging.getLogger(__name__)
bearer_scheme = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ── Token verification ─────────────────────────────────────

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
) -> dict:
    """
    Verify the JWT token from the request header.
    Frontend sends: Authorization: Bearer <supabase_token>
    Returns: {id, email, full_name, token}
    Raises 401 if invalid.
    """
    token = credentials.credentials
    if not token:
        raise HTTPException(status_code=401, detail=MSG["unauthorized"])
    try:
        response = get_db().auth.get_user(token)
        if not response or not response.user:
            raise HTTPException(status_code=401, detail=MSG["unauthorized"])
        user = response.user
        return {
            "id": user.id,
            "email": user.email,
            "full_name": user.user_metadata.get("full_name", ""),
            "token": token,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Auth error: {e}")
        raise HTTPException(status_code=401, detail=MSG["unauthorized"])


def get_user_id(user: dict = Depends(get_current_user)) -> str:
    """Shortcut — returns just the user ID string."""
    return user["id"]


# ── Password helpers ───────────────────────────────────────

def hash_password(password: str) -> str:
    """Hash a plain text password (one-way)."""
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """Check plain password against stored hash."""
    return pwd_context.verify(plain, hashed)


def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Check password meets requirements.
    Returns (True, "") if valid, (False, "error msg") if not.

    Rules: 8+ chars, 1 uppercase, 1 number, 1 special char
    """
    if len(password) < PASSWORD_MIN_LENGTH:
        return False, f"Password must be at least {PASSWORD_MIN_LENGTH} characters"
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one number"
    if not any(c in "!@#$%^&*()_+-=[]{}|;:,./<>?" for c in password):
        return False, "Password must contain at least one special character"
    return True, ""


# ── Rate limiting ──────────────────────────────────────────

_failed: dict = defaultdict(list)


def check_rate_limit(email: str) -> tuple[bool, int]:
    """
    Check if login is allowed.
    Returns (True, 0) if ok, (False, seconds) if locked out.
    """
    now = datetime.utcnow()
    window = now - timedelta(seconds=LOCKOUT_SECONDS)
    _failed[email] = [t for t in _failed[email] if t > window]
    if len(_failed[email]) >= MAX_LOGIN_ATTEMPTS:
        oldest = _failed[email][0]
        secs = int((oldest + timedelta(seconds=LOCKOUT_SECONDS) - now).total_seconds())
        return False, max(0, secs)
    return True, 0


def record_failed(email: str):
    """Record a failed login attempt."""
    _failed[email].append(datetime.utcnow())


def clear_failed(email: str):
    """Clear failed attempts after successful login."""
    _failed.pop(email, None)
