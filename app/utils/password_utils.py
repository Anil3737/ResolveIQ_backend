from passlib.context import CryptContext
from werkzeug.security import check_password_hash as werkzeug_verify

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    # Handle legacy werkzeug hashes
    if password_hash and password_hash.startswith("pbkdf2:sha256:"):
        return werkzeug_verify(password_hash, plain_password)
    
    # Handle passlib bcrypt hashes
    try:
        return pwd_context.verify(plain_password, password_hash)
    except Exception:
        return False
