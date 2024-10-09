from tonsdk.contract import Address
from tonsdk.contract.token.nft import NFTItem, NFTCollection

from .wallet import LIDUM_WALLET_ADDRESS
from ..config import ROYALTY, ROYALTY_BASE, FORWARD_AMOUNT
from .ton_client import get_last_index


def collection_mint_body(
    collection_content_uri: str,
    nft_item_content_base_uri: str,
    royalty_base: int = ROYALTY_BASE,
    royalty: int = ROYALTY,
    royalty_address: str = LIDUM_WALLET_ADDRESS,
    owner_address: str = LIDUM_WALLET_ADDRESS,
):

    collection = NFTCollection(
        royalty_base=royalty_base,
        royalty=royalty,
        royalty_address=Address(royalty_address),
        owner_address=Address(owner_address),
        collection_content_uri=collection_content_uri,
        nft_item_content_base_uri=nft_item_content_base_uri,
        nft_item_code_hex=NFTItem.code,
    )

    return collection


async def nft_mint_body(collection_address: str, nft_meta: str, ls_index: int, is_testnet: bool):

    body = NFTCollection().create_mint_body(
        item_index=await get_last_index(collection_address, ls_index, is_testnet),
        new_owner_address=Address(LIDUM_WALLET_ADDRESS),
        item_content_uri=nft_meta,
        amount=FORWARD_AMOUNT,
    )

    return body


async def batch_mint_body(
    collection_address: str,
    nfts_num: int,
    nft_meta: str,
    ls_index: int,
    is_testnet: bool,
):

    contents_and_owners = [(nft_meta, Address(LIDUM_WALLET_ADDRESS)) for _ in range(nfts_num)]

    body = NFTCollection().create_batch_mint_body(
        from_item_index=await get_last_index(collection_address, ls_index, is_testnet),
        contents_and_owners=contents_and_owners,
        amount_per_one=FORWARD_AMOUNT,
    )

    return body
