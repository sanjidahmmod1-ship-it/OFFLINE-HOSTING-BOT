from cryptography.fernet import Fernet, InvalidToken
from config import ENCRYPTION_KEY

_cipher = Fernet(ENCRYPTION_KEY.encode())

def encrypt_token(token: str) -> str:
    return _cipher.encrypt(token.encode("utf-8")).decode("utf-8")

def decrypt_token(encrypted: str) -> str:
    try:
        return _cipher.decrypt(encrypted.encode("utf-8")).decode("utf-8")
    except InvalidToken as exc:
        raise RuntimeError("Cannot decrypt bot token. Check your ENCRYPTION_KEY.") from exc
