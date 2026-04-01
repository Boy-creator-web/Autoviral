from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from core.security import get_password_hash
from models.synthetic_human import SyntheticHuman
from models.user import User

_COMPAT_USER_EMAIL = "synthetic-human-bot@autoviral.local"
_COMPAT_USER_NAME = "Synthetic Human Bot"


def get_or_create_compat_user(db: Session) -> User:
    user = db.scalar(select(User).where(User.email == _COMPAT_USER_EMAIL))
    if user is not None:
        return user

    user = User(
        email=_COMPAT_USER_EMAIL,
        password_hash=get_password_hash("TempPass#12345"),
        name=_COMPAT_USER_NAME,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_human_compat(
    db: Session,
    *,
    name: str,
    age: int,
    gender: str,
    style: str,
) -> SyntheticHuman:
    user = get_or_create_compat_user(db)
    row = SyntheticHuman(
        name=name.strip(),
        age=age,
        gender=gender.strip(),
        style=style.strip(),
        user_id=user.id,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def list_human_compat(db: Session) -> list[SyntheticHuman]:
    return list(db.scalars(select(SyntheticHuman).order_by(SyntheticHuman.id.asc())).all())


def train_human_voice_compat(db: Session, *, human_id: int, text: str) -> tuple[SyntheticHuman, str]:
    row = db.get(SyntheticHuman, human_id)
    if row is None:
        raise ValueError("Synthetic human not found")

    # CPU-safe fallback: generate deterministic pseudo-mp3 bytes.
    # This keeps compatibility for smoke tests where only file generation is required.
    ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    safe_name = "".join(ch for ch in row.name.lower().replace(" ", "_") if ch.isalnum() or ch in {"_", "-"})
    output_path = Path(f"/tmp/voice_{human_id}_{safe_name}_{ts}.mp3")
    voice_payload = _build_mock_mp3_payload(text=text, speaker=row.name)
    output_path.write_bytes(voice_payload)
    return row, str(output_path)


def _build_mock_mp3_payload(*, text: str, speaker: str) -> bytes:
    title = f"{speaker}: {text[:80]}".encode("utf-8", errors="ignore")[:80]
    id3_header = b"ID3\x03\x00\x00\x00\x00\x00\x3f"
    tit2_frame = b"TIT2" + b"\x00\x00\x00\x1f" + b"\x00\x00" + b"\x03" + title.ljust(30, b" ")
    tpe1_frame = b"TPE1" + b"\x00\x00\x00\x11" + b"\x00\x00" + b"\x03" + speaker.encode("utf-8", errors="ignore")[:16].ljust(16, b" ")
    # Minimal fake audio frame-like payload for smoke tests.
    fake_audio = (b"\xff\xfb\x90\x64" + b"\x00" * 256) * 4
    return id3_header + tit2_frame + tpe1_frame + fake_audio
