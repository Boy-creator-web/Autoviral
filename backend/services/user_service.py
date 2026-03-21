import base64
import hashlib
import hmac
import os

from sqlalchemy.orm import Session

from api.schemas import UserCreate
from models.user import User

PBKDF2_ITERATIONS = 120000


def hash_password(password: str) -> str:
    """Hash password with PBKDF2-HMAC-SHA256."""
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PBKDF2_ITERATIONS,
    )
    return (
        f"pbkdf2_sha256${PBKDF2_ITERATIONS}$"
        f"{base64.b64encode(salt).decode('ascii')}$"
        f"{base64.b64encode(digest).decode('ascii')}"
    )


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Verify plaintext password against PBKDF2 hash format."""
    try:
        scheme, iter_s, salt_b64, digest_b64 = password_hash.split("$", 3)
        if scheme != "pbkdf2_sha256":
            return False
        iterations = int(iter_s)
        salt = base64.b64decode(salt_b64.encode("ascii"))
        expected = base64.b64decode(digest_b64.encode("ascii"))
        candidate = hashlib.pbkdf2_hmac(
            "sha256",
            plain_password.encode("utf-8"),
            salt,
            iterations,
        )
        return hmac.compare_digest(candidate, expected)
    except Exception:
        return False


def create_user(db: Session, user_data: UserCreate) -> User:
    """Create a new user."""
    existing = db.query(User).filter(User.email == user_data.email).first()
    if existing is not None:
        raise ValueError("Email already registered")

    hashed = hash_password(user_data.password)
    db_user = User(
        email=user_data.email,
        password_hash=hashed,
        name=user_data.name,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_user_by_email(db: Session, email: str) -> User | None:
    """Get user by email."""
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db: Session, user_id: int) -> User | None:
    """Get user by ID."""
    return db.query(User).filter(User.id == user_id).first()


def list_users(db: Session, skip: int = 0, limit: int = 100) -> list[User]:
    """List all users."""
    return db.query(User).offset(skip).limit(limit).all()
