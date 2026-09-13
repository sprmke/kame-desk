import base64
import hashlib
import json
from typing import Any

from cryptography.fernet import Fernet

from app.core.config import settings


def _fernet() -> Fernet:
    digest = hashlib.sha256(settings.secret_key.encode()).digest()
    key = base64.urlsafe_b64encode(digest)
    return Fernet(key)


def encrypt_json(payload: dict[str, Any]) -> str:
    return _fernet().encrypt(json.dumps(payload).encode()).decode()


def decrypt_json(blob: str) -> dict[str, Any]:
    return json.loads(_fernet().decrypt(blob.encode()).decode())
