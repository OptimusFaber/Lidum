from typing import Any

from .. import fernet


def encrypt(msg: Any):
    return fernet.encrypt(str(msg).encode()).decode()


def decrypt(msg: str):
    return fernet.decrypt(msg.encode()).decode()
