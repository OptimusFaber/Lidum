import asyncio

from ton.utils import read_address
from tonsdk.boc import Cell, Slice
from tonsdk.utils import b64str_to_bytes
from tonsdk.contract import Address
from tonsdk.contract.token.nft import NFTItem

from .wallet import LIDUM_WALLET, LIDUM_WALLET_ADDRESS
from ..config import TRANSFER_TIMEOUT, NFT_TRANSFER_AMOUNT
from ..config import NFT_TRANSFER_FORWARD_AMOUNT
from .ton_client import get_seqno, get_client


async def get_nft_owner(nft_address: str, ls_index: int, is_testnet: bool):
    """Возвращает адрес владельца NFT."""

    client = await get_client(is_testnet, ls_index)

    stack = await client.raw_run_method(address=nft_address, method="get_nft_data", stack_data=[])

    owner_address = Cell.one_from_boc(b64str_to_bytes(stack["stack"][3][1]["bytes"]))
    owner_address = Slice(owner_address).read_msg_addr()
    owner_address = Address(owner_address).to_string(True, True, True)

    await client.close()
    return owner_address


async def nft_address_by_index(collection_address: str, index: int, ls_index: int, is_testnet: bool):
    """Возвращает адрес NFT по его индексу в коллекции."""

    client = await get_client(is_testnet, ls_index)

    stack = await client.raw_run_method(
        address=collection_address,
        method="get_nft_address_by_index",
        stack_data=[["number", index]],
    )

    nft_address = Cell.one_from_boc(b64str_to_bytes(stack["stack"][0][1]["bytes"]))
    nft_address = read_address(nft_address).to_string(True, True, True)

    return nft_address


async def transfer_nft(nft_address: str, new_owner_address: str, ls_index: int, is_testnet: bool):
    """Передает NFT из коллекции на указанный адрес."""

    # Начальная проверка владельца NFT
    nft_owner = await get_nft_owner(nft_address=nft_address, ls_index=ls_index, is_testnet=is_testnet)

    if nft_owner == new_owner_address:
        return True

    body = NFTItem().create_transfer_body(
        new_owner_address=Address(new_owner_address),
        response_address=Address(LIDUM_WALLET_ADDRESS),
        forward_amount=NFT_TRANSFER_FORWARD_AMOUNT,
    )

    client = await get_client(is_testnet, ls_index)
    seqno = await get_seqno(client, LIDUM_WALLET_ADDRESS)

    query = LIDUM_WALLET.create_transfer_message(
        to_addr=nft_address,
        amount=NFT_TRANSFER_AMOUNT,
        seqno=seqno,
        payload=body,
    )

    await client.raw_send_message(query["message"].to_boc(False))
    await client.close()

    # Ожидание перевода NFT
    timeout_cnt = 0

    while timeout_cnt <= TRANSFER_TIMEOUT:

        nft_owner = await get_nft_owner(nft_address=nft_address, ls_index=ls_index, is_testnet=is_testnet)

        if nft_owner == new_owner_address:
            return True

        await asyncio.sleep(1)
        timeout_cnt += 1

    return False
