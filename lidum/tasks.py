import asyncio

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from celery.exceptions import MaxRetriesExceededError

from . import get_app, create_celery
from .utils import tasks_statuses
from .config import LS_INDEX, MINT_ATTEMPS_CNT
from .config import MINT_RETRY_DELAY, TRANSFER_ATTEMPS_CNT
from .config import TRANSFER_RETRY_DELAY
from .config import TRANSACTION_ATTEMPS_CNT
from .config import TRANSACTION_RETRY_DELAY
from .utils.db import author_by_tg_id, transaction_by_id
from .utils.deploy import deploy_one_item, deploy_collection
from .utils.convert import address_to_friendly
from .utils.ton_client import get_transaction_data
from .utils.mint_bodies import collection_mint_body
from .utils.transfer_nft import transfer_nft

app = get_app()
celery = create_celery(app)

engine = create_engine(
    app.config["SQLALCHEMY_DATABASE_URI"],
    pool_size=10,
    max_overflow=5,
    pool_timeout=30,
    pool_recycle=1800,
)

session_factory = sessionmaker(bind=engine)


@celery.task(queue="queue_test", bind=True, max_retries=TRANSACTION_ATTEMPS_CNT, default_retry_delay=TRANSACTION_RETRY_DELAY)
def process_transaction(self, transaction_id: int):
    """Фоновая задача на проверку статуса транзакции."""

    print(f"Processing transaction {transaction_id}...")
    session = session_factory()

    try:
        transaction = transaction_by_id(transaction_id=transaction_id, session=session)

        if transaction is None:
            print(f"Transaction with id {transaction_id} was not found")
            session.close()
            return

        hash = transaction.hash
        # amount = transaction.amount
        # source_address = transaction.source_address
        # destination_address = transaction.destination_address
        is_testnet = transaction.is_testnet

    except Exception as e:
        print(f"Error when trying to find a transaction {transaction_id}: {e}")
        session.close()
        return

    try:
        print(f"Attempt {self.request.retries} / {MINT_ATTEMPS_CNT}...")

        transaction.status = tasks_statuses.PENDING
        session.commit()

        transaction_data = get_transaction_data(hash=hash, is_testnet=is_testnet)

        if transaction_data.success:
            transaction.status = tasks_statuses.SUCCESS

        else:
            transaction.status = tasks_statuses.FAILED

        session.commit()
        return

    except Exception as e:

        try:
            raise self.retry(exc=e)

        except MaxRetriesExceededError:
            print(f"Error when trying to confirm the transaction {transaction_id}: {e}")

            transaction.status = tasks_statuses.CRUSHED
            session.commit()

    finally:
        session.close()


@celery.task(queue="queue_test", bind=True, max_retries=MINT_ATTEMPS_CNT, default_retry_delay=MINT_RETRY_DELAY)
def collection_mint(
    self, telegram_id: str | int, collection_content_uri: str, nft_item_content_base_uri: str, is_testnet: bool
):
    """Фоновая задача на минт пустой коллекции."""

    print(f"Launching the task of minting the collection with content_uri {collection_content_uri}...")
    session = session_factory()

    try:
        author = author_by_tg_id(telegram_id=telegram_id, session=session)

        if author is None:
            print(f"Author with id {telegram_id} was not found")
            session.close()
            return

        author.collection_status = tasks_statuses.PENDING
        session.commit()

    except Exception as e:
        print(f"Error when trying to find an author with id {telegram_id}: {e}")
        session.close()
        return

    collection = collection_mint_body(
        collection_content_uri=collection_content_uri,
        nft_item_content_base_uri=nft_item_content_base_uri,
    )

    collection_address = collection.address.to_string(True, True, True)

    print(f"Start minting collection with address {collection_address}...")
    print(f"Attempt {self.request.retries} / {MINT_ATTEMPS_CNT}...")

    try:
        success = asyncio.run(
            deploy_collection(
                collection=collection,
                ls_index=LS_INDEX,
                is_testnet=is_testnet,
            )
        )

        if success:
            author.collection_status = tasks_statuses.MINTED
            session.commit()
            session.close()
            print("The collection has been successfully minted!")

    except Exception as e:

        # Попытка повторного запуска задачи
        try:
            session.close()
            raise self.retry(exc=e)

        except MaxRetriesExceededError:
            print(f"The attempt to mint collection {collection_address} was unsuccessful")
            author.collection_status = tasks_statuses.FAILED
            session.commit()
            session.close()


@celery.task(queue="queue_test", bind=True, max_retries=MINT_ATTEMPS_CNT, default_retry_delay=MINT_RETRY_DELAY)
def nft_mint(
    self, author_telegram_id: str | int, dest_wallet_address: str, collection_address: str, nft_meta: str, is_testnet: bool
):

    print(f"Launching the task of minting the nft into collection {collection_address}...")
    session = session_factory()

    # Загрузка состояния минта коллекции из БД
    try:
        author = author_by_tg_id(telegram_id=author_telegram_id, session=session)

        if author is None:
            print(f"Author with id {author_telegram_id} was not found")
            session.close()
            return

        collection_status = author.collection_status

    except Exception as e:
        print(f"Error when trying to find an author with id {author_telegram_id}: {e}")
        session.close()
        return

    if collection_status == tasks_statuses.FAILED:
        print(f"The collection with the address {collection_address} has not been minted. Canceling this task...")
        session.close()
        return

    # Откладывание задачи, если коллекция ещё не заминчена
    elif collection_status != tasks_statuses.MINTED:
        session.close()
        raise self.retry(exc=f"Collection {collection_address} is still minting, retrying...")

    # Минт NFT
    print(f"Minting NFT to the collection {collection_address}...")
    print(f"Attempt {self.request.retries} / {MINT_ATTEMPS_CNT}...")

    success = False

    try:
        nft_address = asyncio.run(
            deploy_one_item(
                collection_address=collection_address,
                nft_meta=nft_meta,
                ls_index=LS_INDEX,
                is_testnet=is_testnet,
            )
        )

        if nft_address is not None:
            print("The minting of the NFT was successful!")
            success = True

            try:
                sending_nft.delay(nft_address, dest_wallet_address, is_testnet)

            except Exception as e:
                print(
                    "An error occurred when trying to add a task"
                    f"to the queue for sending nft from collection {collection_address}: {e}"
                )
                session.close()
                return

    except Exception as e:
        print(e)
        success = False

    if not success:
        try:
            session.close()
            self.retry()

        except MaxRetriesExceededError:
            session.close()
            print(f"The attempt to mint NFT to the collection {collection_address} was unsuccessful")


@celery.task(queue="queue_test", bind=True, max_retries=TRANSFER_ATTEMPS_CNT, default_retry_delay=TRANSFER_RETRY_DELAY)
def sending_nft(self, nft_address: str, dest_wallet_address: str, is_testnet: bool):

    nft_address = address_to_friendly(nft_address)
    dest_wallet_address = address_to_friendly(dest_wallet_address)

    print(f"Transfer of the NFT to the user {dest_wallet_address}...")

    # Передача NFT пользователю
    print(f"Attempt {self.request.retries} / {TRANSFER_ATTEMPS_CNT}...")

    success = False

    try:
        success = asyncio.run(
            transfer_nft(
                nft_address=nft_address,
                new_owner_address=dest_wallet_address,
                ls_index=LS_INDEX,
                is_testnet=is_testnet,
            )
        )

        if success:
            print(f"The transfer of the NFT {nft_address} was successful!")

    except Exception as e:
        print(e)
        success = False

    if not success:
        try:
            self.retry()

        except MaxRetriesExceededError:
            print(f"The attempt to send NFT {nft_address} to the user {dest_wallet_address} was unsuccessful")
