import os
import asyncio

from tonsdk.contract.token.nft import NFTCollection

from .wallet import LIDUM_WALLET, LIDUM_WALLET_ADDRESS
from ..config import MINT_TIMEOUT, FORWARD_AMOUNT
from ..config import NFT_TRANSFER_AMOUNT
from ..config import COLLECTION_TRANSFER_AMOUNT
from .convert import to_json_ext
from .ton_client import get_seqno, get_client, account_nfts
from .ton_client import get_last_index
from .mint_bodies import nft_mint_body, batch_mint_body


async def deploy_wallet(is_testnet: bool, ls_index: int):
    """Инициализация пользовательского кошелька."""

    client = await get_client(is_testnet, ls_index)

    query = LIDUM_WALLET.create_init_external_message()

    deploy_message = query["message"].to_boc(False)

    await client.raw_send_message(deploy_message)
    await client.close()


async def deploy_collection(collection: NFTCollection, ls_index: int, is_testnet: bool):
    """Минт пустой коллекции."""

    state_init = collection.create_state_init()["state_init"]

    client = await get_client(is_testnet, ls_index)
    seqno = await get_seqno(client, LIDUM_WALLET_ADDRESS)

    collection_address = collection.address.to_string()

    query = LIDUM_WALLET.create_transfer_message(
        to_addr=collection_address,
        amount=COLLECTION_TRANSFER_AMOUNT,
        seqno=seqno,
        state_init=state_init,
    )

    await client.raw_send_message(query["message"].to_boc(False))
    await client.close()

    # Ожидание прохождения транзакции
    timeout_cnt = 0

    while True:

        if timeout_cnt > MINT_TIMEOUT:
            return False

        index = await get_last_index(collection_address, ls_index, is_testnet)

        if index == 0:
            break

        await asyncio.sleep(1)
        timeout_cnt += 1

    return True


async def deploy_one_item(
    collection_address: str,
    nft_meta: str,
    ls_index: int,
    is_testnet: bool,
):
    """Минт одного NFT в существующую коллекцию."""

    body = await nft_mint_body(
        collection_address=collection_address,
        nft_meta=nft_meta,
        ls_index=ls_index,
        is_testnet=is_testnet,
    )

    client = await get_client(is_testnet, ls_index)
    seqno = await get_seqno(client, LIDUM_WALLET_ADDRESS)

    query = LIDUM_WALLET.create_transfer_message(
        to_addr=collection_address,
        amount=NFT_TRANSFER_AMOUNT,
        seqno=seqno,
        payload=body,
    )

    await client.raw_send_message(query["message"].to_boc(False))
    await client.close()

    # Ожидание появления NFT в коллекции
    timeout_cnt = 0

    start_nfts = account_nfts(is_testnet=is_testnet, collection_address=collection_address)
    start_nft_addresses = {nft["address"] for nft in start_nfts}

    while timeout_cnt <= MINT_TIMEOUT:

        cur_nfts = account_nfts(is_testnet=is_testnet, collection_address=collection_address)
        cur_nft_addresses = {nft["address"] for nft in cur_nfts}

        new_nft_addresses = cur_nft_addresses - start_nft_addresses

        # Проверка на появление нужного NFT
        if len(new_nft_addresses) > 0:
            for new_nft in cur_nfts:
                if new_nft["address"] in new_nft_addresses:

                    if to_json_ext(os.path.split(new_nft["image"])[1]) == nft_meta:
                        return new_nft["address"]

        await asyncio.sleep(1)
        timeout_cnt += 1

    return None


async def deploy_batch_items(
    collection_address: str,
    nfts_num: int,
    nft_meta: str,
    ls_index: int,
    is_testnet: bool,
):
    """Минт батча NFT в сущетсвующую коллекцию."""

    body = await batch_mint_body(
        collection_address=collection_address,
        nfts_num=nfts_num,
        nft_meta=nft_meta,
        ls_index=ls_index,
        is_testnet=is_testnet,
    )

    client = await get_client(is_testnet, ls_index)
    seqno = await get_seqno(client, LIDUM_WALLET_ADDRESS)

    query = LIDUM_WALLET.create_transfer_message(
        to_addr=collection_address,
        amount=nfts_num * FORWARD_AMOUNT + NFT_TRANSFER_AMOUNT,
        seqno=seqno,
        payload=body,
    )

    await client.raw_send_message(query["message"].to_boc(False))
    await client.close()

    # Ожидание появления NFT в коллекции
    timeout_cnt = 0

    start_nfts = account_nfts(is_testnet=is_testnet, collection_address=collection_address)
    start_nft_addresses = {nft["address"] for nft in start_nfts}

    while timeout_cnt <= MINT_TIMEOUT:

        cur_nfts = account_nfts(is_testnet=is_testnet, collection_address=collection_address)
        cur_nft_addresses = {nft["address"] for nft in cur_nfts}

        new_nft_addresses = cur_nft_addresses - start_nft_addresses

        # Проверка на появление нужного NFT
        if len(new_nft_addresses) > 0:

            addresses = []

            for new_nft in cur_nfts:
                if new_nft["address"] in new_nft_addresses:

                    if to_json_ext(os.path.split(new_nft["image"])[1]) == nft_meta:
                        addresses.append(new_nft["address"])

            if len(addresses) == nfts_num:
                return addresses

        await asyncio.sleep(1)
        timeout_cnt += 1

    return None
