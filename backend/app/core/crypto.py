import hashlib
from functools import lru_cache

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings


@lru_cache
def _fernet() -> Fernet:
    if settings.encryption_key:
        return Fernet(settings.encryption_key.encode())
    key = base64_key(settings.secret_key)
    return Fernet(key)


def base64_key(seed: str) -> bytes:
    import base64

    return base64.urlsafe_b64encode(hashlib.sha256(seed.encode()).digest())


def generate_key() -> str:
    return Fernet.generate_key().decode()


def encrypt(plain: str) -> str:
    return _fernet().encrypt(plain.encode()).decode()


def decrypt(token: str) -> str:
    try:
        return _fernet().decrypt(token.encode()).decode()
    except InvalidToken as exc:
        raise ValueError("Cannot decrypt secret: wrong ENCRYPTION_KEY?") from exc
