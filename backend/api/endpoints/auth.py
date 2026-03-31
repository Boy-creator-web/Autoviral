"""Authentication endpoint for login and token issuance."""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from core.audit import audit_log
from core.database import get_db
from core.rate_limit import enforce_ip_rate_limit
from core.security import create_access_token, verify_password
from models.user import User

router = APIRouter()


@router.post("/login")
def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    enforce_ip_rate_limit(request)
    user = db.query(User).filter(User.email == form_data.username).first()
    if user is None or not verify_password(form_data.password, user.password_hash):
        audit_log(
            "auth.login_failed",
            actor=form_data.username,
            target="auth.login",
            metadata={"reason": "invalid_credentials"},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    token = create_access_token(user.id, user.role)
    audit_log(
        "auth.login_success",
        actor=str(user.id),
        target="auth.login",
        metadata={"email": user.email, "role": user.role},
    )
    return {"access_token": token, "token_type": "bearer"}
