import random
from os import listdir
from os.path import join

from PIL import Image

from ..config import NFT_LAYERS_PATH


def get_random_nft():
    """Смешивает случайные слои и возвращает NFT."""

    nft_type_dir = join(NFT_LAYERS_PATH, random.choice(listdir(NFT_LAYERS_PATH)))
    layers_dir = sorted([join(nft_type_dir, layer_dir) for layer_dir in listdir(nft_type_dir)])

    nft = None

    for layer_dir in layers_dir:

        images = [join(layer_dir, image) for image in listdir(layer_dir)]
        layer = Image.open(random.choice(images)).convert("RGBA")

        if nft is None:
            nft = layer

        else:
            nft = Image.alpha_composite(nft, layer)

    return nft
