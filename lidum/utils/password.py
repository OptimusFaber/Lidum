from .hash import sha256_hash


def compare_passwords(cur_password: str, event_password: str):
    """Хэширует введеный пароль и сравнивает с хэшем коллекции."""

    cur_hash = sha256_hash(cur_password)
    return cur_hash == event_password
