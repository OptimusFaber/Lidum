from ..config import DROP_COMISSION, FORWARD_AMOUNT
from ..config import PRICE_FRACTION, NFT_TRANSFER_AMOUNT
from ..config import COLLECTION_TRANSFER_AMOUNT
from .convert import ton_from_nano


def get_event_price(nfts_cnt: int, is_new: bool):
    """Вычислияет оплату за новое событие."""

    price = 0.0

    if is_new:
        price += COLLECTION_TRANSFER_AMOUNT

    price += nfts_cnt * (FORWARD_AMOUNT + NFT_TRANSFER_AMOUNT)
    price += price * PRICE_FRACTION

    return ton_from_nano(price)


def get_drop_price(nfts_cnt: int):
    """Вычислияет оплату за drop."""

    price = nfts_cnt * DROP_COMISSION

    return ton_from_nano(price)
