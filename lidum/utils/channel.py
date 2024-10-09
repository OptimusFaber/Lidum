import requests
from bs4 import BeautifulSoup

from .convert import username_to_link


def get_channel_avatar(url: str):
    """Возвращает ссылку на автар телеграм-канала."""

    response = requests.get(username_to_link(url))

    soup = BeautifulSoup(response.text, "html.parser")

    avatar_tag = soup.find("img", class_="tgme_page_photo_image")

    if avatar_tag is None:
        return None

    return avatar_tag["src"]
