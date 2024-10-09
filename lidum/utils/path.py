from os.path import join

from ..config import IMAGES_PATH, PROJECT_URL, PROJECT_ROOT
from ..config import METADATA_PATH
from .convert import to_json_ext


def get_user_path(telegram_id: int | str, return_url: bool = False):
    """Возвращает абсолютный путь до директории коллекций пользователя."""

    base = PROJECT_URL if return_url else PROJECT_ROOT
    return join(base, "collections")


def get_collection_path(collection_name: str, telegram_id: int | str, return_url: bool = False):
    """Возвращает абсолютный путь до директории коллекции пользователя."""

    return join(get_user_path(str(telegram_id), return_url), collection_name)


def get_nft_image_path(collection_name: str, telegram_id: int | str, image_name: str, return_url: bool = False):
    """Возвращает абсолютный путь до указанного изображения в директории коллекции
    пользователя."""

    collection_path = get_collection_path(collection_name, str(telegram_id), return_url)
    return join(collection_path, IMAGES_PATH, image_name)


def get_nft_metadata_path(collection_name: str, telegram_id: int | str, image_name: str, return_url: bool = False):
    """Возвращает абсолютный путь до файла метаданных указанного изображения в
    директории коллекции пользователя."""

    collection_path = get_collection_path(collection_name, str(telegram_id), return_url)
    return join(collection_path, METADATA_PATH, to_json_ext(image_name))


def get_collection_metadata_path(collection_name: str, telegram_id: int | str, return_url: bool = False):
    """Возвращает абсолютный путь до файла метаданных указанной коллекции
    пользователя."""

    collection_path = get_collection_path(collection_name, str(telegram_id), return_url)
    return join(collection_path, METADATA_PATH, to_json_ext(collection_name))
