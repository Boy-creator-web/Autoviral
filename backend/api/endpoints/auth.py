"""Authentication endpoint for login and token issuance."""

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from core.audit import audit_log
from core.database import get_db
from core.rate_limit import (
    apply_rate_limit_headers,
    check_login_lock,
    clear_login_failures,
    enforce_ip_rate_limit,
    register_login_failure,
)
from core.security import create_access_token, verify_password
from models.user import User

router = APIRouter()


@router.post("/login")
def login(
    request: Request,
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    ip = request.client.host if request.client else "unknown"
    username = form_data.username.strip().lower()

    locked_email_ttl = check_login_lock("email", username)
    locked_ip_ttl = check_login_lock("ip", ip)
    lock_ttl = max(locked_email_ttl, locked_ip_ttl)
    if lock_ttl > 0:
        audit_log(
            "auth.login_blocked",
            actor=username,
            target="auth.login",
            metadata={"reason": "temporary_lock", "lock_ttl_seconds": lock_ttl, "ip": ip},
            db=db,
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Login temporarily locked. Retry in {lock_ttl}s",
            headers={"Retry-After": str(lock_ttl)},
        )

    ip_limit = enforce_ip_rate_limit(request)
    apply_rate_limit_headers(response, ip_limit)
    user = db.query(User).filter(User.email == form_data.username).first()
    if user is None or not verify_password(form_data.password, user.password_hash):
        email_locked_now, email_lock_ttl = register_login_failure("email", username)
        ip_locked_now, ip_lock_ttl = register_login_failure("ip", ip)
        lock_now = email_locked_now or ip_locked_now
        lock_ttl = max(email_lock_ttl, ip_lock_ttl)
        audit_log(
            "auth.login_failed",
            actor=form_data.username,
            target="auth.login",
            metadata={
                "reason": "invalid_credentials",
                "ip": ip,
                "temporary_lock_applied": lock_now,
                "lock_ttl_seconds": lock_ttl if lock_now else 0,
            },
            db=db,
        )
        if lock_now:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many failed logins. Retry in {lock_ttl}s",
                headers={"Retry-After": str(lock_ttl)},
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    clear_login_failures("email", username)
    clear_login_failures("ip", ip)
    token = create_access_token(user.id, user.role)
    audit_log(
        "auth.login_success",
        actor=str(user.id),
        target="auth.login",
        metadata={"email": user.email, "role": user.role},
        db=db,
    )
    return {"access_token": token, "token_type": "bearer"}
