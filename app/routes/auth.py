# FinRight AI — Auth Routes
# Handles: signup, login, logout, forgot password, reset password

from fastapi import APIRouter, HTTPException, status
from app.schema import (
    SignUpRequest, LoginRequest,
    ForgotPasswordRequest, ResetPasswordRequest,
    MessageResponse
)
from app.database import get_db
from app.security import (
    check_rate_limit, record_failed_attempt, clear_failed_attempts
)
from app.constants import MSG
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/signup", response_model=MessageResponse)
async def signup(data: SignUpRequest):
    """
    Create a new user account.
    Sends confirmation email automatically via Supabase.
    """
    try:
        db = get_db()
        response = db.auth.sign_up({
            "email": data.email,
            "password": data.password,
            "options": {
                "data": {"full_name": data.full_name}
            }
        })

        if response.user:
            return MessageResponse(
                success=True,
                message=MSG["signup_success"]
            )
        raise HTTPException(status_code=400, detail="Signup failed")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Signup error: {e}")
        # Check for duplicate email
        if "already" in str(e).lower():
            raise HTTPException(status_code=400, detail="Email already registered")
        raise HTTPException(status_code=500, detail=MSG["server_error"])


@router.post("/login", response_model=MessageResponse)
async def login(data: LoginRequest):
    """
    Log in with email and password.
    Returns the Supabase session token.
    """
    # Rate limit check
    allowed, wait_secs = check_rate_limit(data.email)
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail=f"Too many attempts. Try again in {wait_secs} seconds."
        )

    try:
        db = get_db()
        response = db.auth.sign_in_with_password({
            "email": data.email,
            "password": data.password
        })

        if response.user and response.session:
            clear_failed_attempts(data.email)
            return MessageResponse(
                success=True,
                message=MSG["login_success"],
                data={
                    "access_token": response.session.access_token,
                    "refresh_token": response.session.refresh_token,
                    "user_id": response.user.id,
                    "email": response.user.email,
                    "full_name": response.user.user_metadata.get("full_name", "")
                }
            )

        record_failed_attempt(data.email)
        raise HTTPException(status_code=401, detail=MSG["invalid_credentials"])

    except HTTPException:
        raise
    except Exception as e:
        record_failed_attempt(data.email)
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=401, detail=MSG["invalid_credentials"])


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(data: ForgotPasswordRequest):
    """
    Send password reset email.
    Always returns success (security — don't reveal if email exists).
    """
    try:
        db = get_db()
        db.auth.reset_password_email(data.email)
        return MessageResponse(
            success=True,
            message="If that email exists, a reset link has been sent"
        )
    except Exception as e:
        logger.error(f"Forgot password error: {e}")
        # Always return success for security
        return MessageResponse(success=True, message="Reset email sent if account exists")


@router.post("/logout", response_model=MessageResponse)
async def logout():
    """Log out the current user"""
    try:
        db = get_db()
        db.auth.sign_out()
        return MessageResponse(success=True, message=MSG["logout_success"])
    except Exception as e:
        logger.error(f"Logout error: {e}")
        return MessageResponse(success=True, message=MSG["logout_success"])
