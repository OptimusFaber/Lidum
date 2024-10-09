from pathlib import Path

from tonsdk.utils import to_nano, from_nano
from tonsdk.contract import Address


def to_json_ext(image_name: str):
    """Возвращает название файла с .json расширением."""
    return str(Path(image_name).with_suffix(".json"))


def username_to_link(username: str):
    """Преобразует имя пользователя, начинающееся с @, в полную телеграм-ссылку."""

    if "@" in username:
        return username.replace("@", "https://t.me//")

    return username


def link_to_username(link: str):
    """Преобразует телеграм-ссылку в полное имя пользователя, начинающееся с @."""

    if "@" not in link:
        return link.replace("https://t.me//", "@")

    return link


def address_to_raw(address: str):
    """Возвращает адрес смарт-контракта в raw виде."""

    return Address(address).to_string(False, True, True)


def address_to_friendly(address: str):
    """Возвращает адрес смарт-контракта в user-friendly виде."""

    return Address(address).to_string(True, True, True)


def ton_to_nano(value: int | float | str):
    """Возвращает значение в нанотон."""

    return int(to_nano(value, "ton"))


def ton_from_nano(value: int):
    """Возвращает значение в тон."""

    return float(from_nano(value, "ton"))
