import json
from os import makedirs
from os.path import join, isfile

from .path import get_nft_image_path, get_collection_path
from .path import get_nft_metadata_path
from .path import get_collection_metadata_path
from ..config import IMAGES_PATH, METADATA_PATH


def create_metadata(
    telegram_id: str | int,
    collection_name: str,
    collection_description: str,
    image_name: str,
):
    """Создает метадату для нового изображения и коллекции."""

    telegram_id = str(telegram_id)

    collection_dir = get_collection_path(collection_name, telegram_id, False)
    collection_meta_path = get_collection_metadata_path(collection_name, telegram_id)

    # Создание директории коллекции для метадаты
    makedirs(join(collection_dir, METADATA_PATH), exist_ok=True)

    # Создать метадату для коллекции, если коллекция новая
    if not isfile(collection_meta_path):
        create_collection_metadata(
            telegram_id=telegram_id,
            collection_name=collection_name,
            logo_name=image_name,
        )

    # Создать метадату для загруженного изображения
    create_nft_metadata(
        telegram_id=telegram_id,
        collection_name=collection_name,
        image_name=image_name,
        nft_name=f"NFT from {collection_name}",
        description=collection_description,
    )

    return None


def create_collection_metadata(telegram_id: str | int, collection_name: str, logo_name: str):
    """Создает .json файл с данными для коллекции."""

    telegram_id = str(telegram_id)

    collection_url = get_collection_path(collection_name, telegram_id, True)
    collection_meta_path = get_collection_metadata_path(collection_name, telegram_id)

    metadata = {
        "image": join(collection_url, IMAGES_PATH, logo_name),
        "name": collection_name,
        "description": "Created by @lidum_bot",
        "social_links": [],
        "marketplace": "getgems.io",
    }

    # Сохранить метадату в директории коллекции
    with open(collection_meta_path, "w") as file:
        json.dump(metadata, file)


def create_nft_metadata(
    telegram_id: str | int,
    collection_name: str,
    image_name: str,
    nft_name: str,
    description: str,
):
    """Создает .json файл с данными для указанного изображения."""

    nft_image_path = get_nft_image_path(collection_name, telegram_id, image_name, True)
    nft_meta_path = get_nft_metadata_path(collection_name, telegram_id, image_name)

    metadata = {
        "name": nft_name,
        "description": description + "\n\nCreated by @lidum_bot",
        "image": nft_image_path,
        "attributes": [],
    }

    # Сохранить метадату в директории коллекции
    with open(nft_meta_path, "w") as file:
        json.dump(metadata, file)
