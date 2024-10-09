import os
import asyncio
from os import makedirs
from typing import Literal

import requests
from pytonapi import Tonapi
from pytonlib import TonlibClient
from tonsdk.utils import Address
from pytonapi.schema.nft import NftItem
from pytonlib.tonlibjson import TonlibError
from tonsdk.contract.token.nft import NFTItem, NFTCollection

from .wallet import LIDUM_WALLET, LIDUM_WALLET_ADDRESS
from ..config import ROYALTY, LS_CONFIG, TONAPI_KEY
from ..config import MINT_TIMEOUT, ROYALTY_BASE, KEYSTORE_PATH
from ..config import FORWARD_AMOUNT, TONLIB_TIMEOUT
from ..config import LS_CONFIG_TESTNET, NFT_TRANSFER_AMOUNT
from ..config import COLLECTION_TRANSFER_AMOUNT
from .convert import to_json_ext, address_to_friendly


class TonClient:

    def __init__(self, is_testnet: bool, ls_index: int | Literal["auto"] = "auto", verbose: bool = False):

        self.is_testnet = is_testnet
        self.config = get_config(is_testnet)
        self.ls_cnt = len(self.config["liteservers"])
        self.ls_index = ls_index
        self.verbose = verbose

        makedirs(KEYSTORE_PATH, exist_ok=True)

        self.client = TonlibClient(
            ls_index=ls_index if isinstance(ls_index, int) else 0,
            config=self.config,
            keystore=KEYSTORE_PATH,
            tonlib_timeout=TONLIB_TIMEOUT,
        )

    async def raw_send_message(self, serialized_boc):

        while True:

            try:
                if self.verbose:
                    print(f"An attempt to send a message to the ls with the index {self.client.ls_index}")

                await self.client.init()
                await self.client.raw_send_message(serialized_boc)

                return

            except TonlibError as e:

                if self.verbose:
                    print(f"An error occurred when sending a message on a ls with the index {self.client.ls_index}: {e}")

                if self.ls_index == "auto":
                    self.client.ls_index = (self.client.ls_index + 1) % self.ls_cnt

                else:
                    return

            finally:
                await self.client.close()

    async def collection_last_index(self, collection_address: str):

        await self.client.init()

        state = await self.client.raw_run_method(
            address=collection_address,
            method="get_collection_data",
            stack_data=[],
        )

        await self.client.close()
        return int(state["stack"][0][1], 16)

    async def raw_get_account_state(self, address: str):

        await self.client.init()

        data = await self.client.raw_get_account_state(address)

        await self.client.close()
        return data

    async def get_transactions(self, limit: int = 100):

        await self.client.init()

        data = await self.client.get_transactions(account=LIDUM_WALLET_ADDRESS, limit=limit)

        await self.client.close()
        return data

    async def raw_estimate_fees(self, destination, body, init_code=b"", init_data=b"", ignore_chksig=True):
        pass

    async def deploy_collection(self, collection: NFTCollection):
        """Минт пустой коллекции."""

        state_init = collection.create_state_init()["state_init"]
        collection_address = collection.address.to_string()

        # Проверка на существование коллекции с таким адресом на кошельке
        data = await self.raw_get_account_state(collection_address)

        if data["code"] != "":
            return True

        query = LIDUM_WALLET.create_transfer_message(
            to_addr=collection_address,
            amount=COLLECTION_TRANSFER_AMOUNT,
            seqno=await self.seqno,
            state_init=state_init,
        )

        await self.raw_send_message(query["message"].to_boc(False))

        # Ожидание появления пустой коллекции на кошельке
        timeout_cnt = 0

        while True:

            if timeout_cnt > MINT_TIMEOUT:
                return False

            data = await self.raw_get_account_state(collection_address)

            if data["code"] != "":
                return True

            await asyncio.sleep(1)
            timeout_cnt += 1

    async def deploy_one_item(self, collection_address: str, nft_meta: str):
        """Минт одного NFT в существующую коллекцию."""

        body = await self.nft_mint_body(
            collection_address=collection_address,
            nft_meta=nft_meta,
        )

        query = LIDUM_WALLET.create_transfer_message(
            to_addr=collection_address,
            amount=NFT_TRANSFER_AMOUNT,
            seqno=await self.seqno,
            payload=body,
        )

        await self.raw_send_message(query["message"].to_boc(False))

        # Ожидание появления NFT в коллекции
        timeout_cnt = 0

        start_nfts = account_nfts(is_testnet=self.is_testnet, collection_address=collection_address)
        start_nft_addresses = {nft["address"] for nft in start_nfts}

        while timeout_cnt <= MINT_TIMEOUT:

            cur_nfts = account_nfts(is_testnet=self.is_testnet, collection_address=collection_address)
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

    async def deploy_batch_items(self, collection_address: str, nfts_num: int, nft_meta: str):
        """Минт батча NFT в сущетсвующую коллекцию."""

        body = await self.batch_mint_body(
            collection_address=collection_address,
            nfts_num=nfts_num,
            nft_meta=nft_meta,
        )

        query = LIDUM_WALLET.create_transfer_message(
            to_addr=collection_address,
            amount=nfts_num * FORWARD_AMOUNT + NFT_TRANSFER_AMOUNT,
            seqno=self.seqno,
            payload=body,
        )

        await self.raw_send_message(query["message"].to_boc(False))

        # Ожидание появления NFT в коллекции
        timeout_cnt = 0

        start_nfts = account_nfts(is_testnet=self.is_testnet, collection_address=collection_address)
        start_nft_addresses = {nft["address"] for nft in start_nfts}

        while timeout_cnt <= MINT_TIMEOUT:

            cur_nfts = account_nfts(is_testnet=self.is_testnet, collection_address=collection_address)
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

    def collection_mint_body(self, collection_content_uri: str, nft_item_content_base_uri: str):

        collection = NFTCollection(
            royalty_base=ROYALTY_BASE,
            royalty=ROYALTY,
            royalty_address=Address(LIDUM_WALLET_ADDRESS),
            owner_address=Address(LIDUM_WALLET_ADDRESS),
            collection_content_uri=collection_content_uri,
            nft_item_content_base_uri=nft_item_content_base_uri,
            nft_item_code_hex=NFTItem.code,
        )

        return collection

    async def nft_mint_body(self, collection_address: str, nft_meta: str):

        body = NFTCollection().create_mint_body(
            item_index=await self.collection_last_index(collection_address),
            new_owner_address=Address(LIDUM_WALLET_ADDRESS),
            item_content_uri=nft_meta,
            amount=FORWARD_AMOUNT,
        )

        return body

    async def batch_mint_body(self, collection_address: str, nfts_num: int, nft_meta: str):

        contents_and_owners = [(nft_meta, Address(LIDUM_WALLET_ADDRESS)) for _ in range(nfts_num)]

        body = NFTCollection().create_batch_mint_body(
            from_item_index=await self.collection_last_index(collection_address),
            contents_and_owners=contents_and_owners,
            amount_per_one=FORWARD_AMOUNT,
        )

        return body

    @property
    async def seqno(self):

        await self.client.init()

        data = await self.client.raw_run_method(method="seqno", stack_data=[], address=LIDUM_WALLET_ADDRESS)

        await self.client.close()
        return int(data["stack"][0][1], 16)


def get_config(is_testnet: bool):
    config_url = LS_CONFIG_TESTNET if is_testnet else LS_CONFIG
    return requests.get(config_url).json()


async def get_client(is_testnet: bool, ls_index: int):
    """Возвращает экземпляр TonlibClient с указанным конфигом."""

    config = get_config(is_testnet)

    makedirs(KEYSTORE_PATH, exist_ok=True)

    client = TonlibClient(
        ls_index=ls_index,
        config=config,
        keystore=KEYSTORE_PATH,
        tonlib_timeout=TONLIB_TIMEOUT,
    )

    await client.init()
    return client


async def get_seqno(client: TonlibClient, address: str):
    data = await client.raw_run_method(method="seqno", stack_data=[], address=address)
    return int(data["stack"][0][1], 16)


async def get_last_index(collection_address: str, ls_index: int, is_testnet: bool):
    """Возвращает индекс последнего элемента в коллекции."""

    client = await get_client(is_testnet, ls_index)

    state = await client.raw_run_method(
        address=collection_address,
        method="get_collection_data",
        stack_data=[],
    )

    await client.close()
    return int(state["stack"][0][1], 16)


def parse_nft_items(nft_items: list[NftItem]):
    """Парсит информацию о NFT с pytonapi."""

    parsed_nfts = []

    for nft in nft_items:

        parsed_nft = dict()

        parsed_nft["address"] = nft.address.to_userfriendly()
        parsed_nft["owner"] = nft.owner.address.to_userfriendly()
        parsed_nft["name"] = nft.metadata["name"]
        parsed_nft["description"] = nft.metadata["description"]
        parsed_nft["image"] = nft.metadata["image"]

        parsed_nfts.append(parsed_nft)

    return parsed_nfts


def account_nfts(is_testnet: bool, collection_address: str = None):
    """Возвращает данные о всех NFT кошелька приложения, либо только данные о NFT из
    одной коллекции."""

    tonapi = Tonapi(api_key=TONAPI_KEY, is_testnet=is_testnet)
    nfts = tonapi.accounts.get_all_nfts(LIDUM_WALLET_ADDRESS, collection_address)

    return parse_nft_items(nfts.nft_items)


def get_nft(nft_address: str, is_testnet: bool):
    """Возвращает данные о NFT из указанной коллекции кошелька приложения."""

    nfts = account_nfts(is_testnet)

    for nft in nfts:
        if address_to_friendly(nft["address"]) == address_to_friendly(nft_address):
            return nft

    return None


def get_transaction_data(hash: str, is_testnet: bool):

    tonapi = Tonapi(api_key=TONAPI_KEY, is_testnet=is_testnet)
    return tonapi.blockchain.get_transaction_data(hash)
