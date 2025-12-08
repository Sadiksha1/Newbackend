import os
import hashlib
import secrets
from datetime import datetime, timedelta

from jose import jwt

# JWT settings
JWT_SECRET = os.getenv("JWT_SECRET", "change-this-secret")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))


def _get_salt() -> str:
    return os.getenv("ADMIN_PASSWORD_SALT", "static-salt")


def hash_password(password: str) -> str:
    salt = _get_salt()
    return hashlib.sha256(f"{salt}:{password}".encode()).hexdigest()


def verify_password(password: str, stored_hash: str) -> bool:
    computed = hash_password(password)
    return secrets.compare_digest(computed, stored_hash)


def create_access_token(subject: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])

