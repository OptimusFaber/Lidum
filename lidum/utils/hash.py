import hashlib


def sha256_hash(msg: str):
    """Возвращает хэш сообщения."""

    return hashlib.sha256(msg.encode()).hexdigest()
