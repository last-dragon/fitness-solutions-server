import hashlib
from random import randbytes

from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str):
    return pwd_context.hash(password)


def verify_password(password: str, hashed_password: str):
    return pwd_context.verify(password, hashed_password)


def generate_authentication_token() -> tuple[str, str]:
    unhashed_token = randbytes(32)
    hashed_token = hashlib.sha256(unhashed_token).hexdigest()
    return (unhashed_token.hex(), hashed_token)


def unhashed_token_to_hashed_token(token: str) -> str:
    return hashlib.sha256(bytes.fromhex(token)).hexdigest()


def create_security_token() -> tuple[str, str]:
    token = randbytes(16)
    seucrity_code = hashlib.sha256(token).hexdigest()
    return (token.hex(), seucrity_code)


def security_token_to_code(token: str) -> str:
    return hashlib.sha256(bytes.fromhex(token)).hexdigest()
