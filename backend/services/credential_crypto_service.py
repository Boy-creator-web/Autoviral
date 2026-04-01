import base64
import hashlib

from cryptography.fernet import Fernet
from core.config import settings


def _derive_key_material() -> bytes:
    secret = settings.social_credentials_encryption_key.strip()
    if not secret:
        secret = "autoviral-fallback-key"
    digest = hashlib.sha256(secret.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


def encrypt_secret(plain_text: str) -> str:
    key = _derive_key_material()
    return Fernet(key).encrypt(plain_text.encode("utf-8")).decode("ascii")


def decrypt_secret(cipher_text: str) -> str:
    key = _derive_key_material()
    return Fernet(key).decrypt(cipher_text.encode("ascii")).decode("utf-8")
