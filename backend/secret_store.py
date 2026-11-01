from cryptography.fernet import Fernet, InvalidToken

from . import db


def _cipher():
    if not db.SUPABASE_ENABLED:
        return None
    try:
        return Fernet(db.APP_ENCRYPTION_KEY.encode("ascii"))
    except (ValueError, TypeError) as exc:
        raise RuntimeError("APP_ENCRYPTION_KEY must be a valid Fernet key.") from exc


def validate_configuration():
    _cipher()


def encrypt_api_key(value):
    cipher = _cipher()
    if cipher is None:
        return value
    return "enc:v1:" + cipher.encrypt(value.encode("utf-8")).decode("ascii")


def decrypt_api_key(value):
    if not value.startswith("enc:v1:"):
        if db.SUPABASE_ENABLED:
            raise RuntimeError("An API key in Supabase is not encrypted.")
        return value
    cipher = _cipher()
    if cipher is None:
        raise RuntimeError("Cannot decrypt an account API key outside Supabase mode.")
    try:
        return cipher.decrypt(value.removeprefix("enc:v1:").encode("ascii")).decode("utf-8")
    except (InvalidToken, UnicodeDecodeError) as exc:
        raise RuntimeError("Could not decrypt an account API key.") from exc
