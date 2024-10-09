import base64
from io import BytesIO
from os import makedirs
from os.path import split

from PIL import Image


def decode_base64_image(image: str):
    """Декодирует изображение, находящее в base64 строке."""

    image = image.split(",")[1]
    image = base64.b64decode(image)

    return image


def save_base64_image(image: bytes, image_path: str):
    """Сохраняет в директории коллекции полученное изображение."""

    # Создание директории коллекции для изображений
    makedirs(split(image_path)[0], exist_ok=True)

    # Сохранение пользовательского изображения
    image = Image.open(BytesIO(image))
    image.save(image_path)
