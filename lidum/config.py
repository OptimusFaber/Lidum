import os

from dotenv import load_dotenv

from .utils.convert import ton_to_nano

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

env_path = os.path.join(PROJECT_ROOT, ".env")
load_dotenv(env_path)

PROJECT_URL = os.getenv("PROJECT_URL")

REDIS_ADDRESS = os.getenv("REDIS_ADDRESS")
REDIS_DB_NUMBER = os.getenv("REDIS_DB_NUMBER")
REDIS_DB_URL = os.path.join(REDIS_ADDRESS, REDIS_DB_NUMBER)

TONCONNECT_MANIFEST = os.path.join(PROJECT_URL, "tonconnect-manifest.json")

LIDUM_MNEMONIC = os.getenv("LIDUM_MNEMONIC").split()

BOT_TOKEN = os.getenv("BOT_TOKEN")
BOT_USERNAME = os.getenv("BOT_USERNAME")
APP_NAME = os.getenv("APP_NAME")

FERNET_PRIVATE_KEY = os.getenv("FERNET_PRIVATE_KEY")
TONAPI_KEY = os.getenv("TONAPI_KEY")

LS_CONFIG = os.getenv("LS_CONFIG")
LS_CONFIG_TESTNET = os.getenv("LS_CONFIG_TESTNET")
LS_INDEX = int(os.getenv("LS_INDEX")) if os.getenv("LS_INDEX") else None

KEYSTORE_PATH = os.path.join(PROJECT_ROOT, os.getenv("KEYSTORE_PATH"))
NFT_LAYERS_PATH = os.path.join(PROJECT_ROOT, os.getenv("NFT_LAYERS_PATH"))
METADATA_PATH = os.getenv("METADATA_PATH")
IMAGES_PATH = os.getenv("IMAGES_PATH")
LOGS_PATH = os.getenv("LOGS_PATH")

ROYALTY_BASE = int(os.getenv("ROYALTY_BASE"))
ROYALTY = float(os.getenv("ROYALTY"))

FORWARD_AMOUNT = ton_to_nano(os.getenv("FORWARD_AMOUNT"))
COLLECTION_TRANSFER_AMOUNT = ton_to_nano(os.getenv("COLLECTION_TRANSFER_AMOUNT"))
NFT_TRANSFER_AMOUNT = ton_to_nano(os.getenv("NFT_TRANSFER_AMOUNT"))
NFT_TRANSFER_FORWARD_AMOUNT = ton_to_nano(os.getenv("NFT_TRANSFER_FORWARD_AMOUNT"))

TRANSFER_TIMEOUT = int(os.getenv("TRANSFER_TIMEOUT"))
MINT_TIMEOUT = int(os.getenv("MINT_TIMEOUT"))
TONLIB_TIMEOUT = int(os.getenv("TONLIB_TIMEOUT"))

TRANSACTION_RETRY_DELAY = int(os.getenv("TRANSACTION_RETRY_DELAY"))
MINT_RETRY_DELAY = int(os.getenv("MINT_RETRY_DELAY"))
TRANSFER_RETRY_DELAY = int(os.getenv("TRANSFER_RETRY_DELAY"))

TRANSACTION_ATTEMPS_CNT = int(os.getenv("TRANSACTION_ATTEMPS_CNT"))
MINT_ATTEMPS_CNT = int(os.getenv("MINT_ATTEMPS_CNT"))
TRANSFER_ATTEMPS_CNT = int(os.getenv("TRANSFER_ATTEMPS_CNT"))

PRICE_FRACTION = float(os.getenv("PRICE_FRACTION"))
DROP_COMISSION = float(os.getenv("DROP_COMISSION"))

POSTGRESQL_USER = os.getenv("POSTGRESQL_USER")
POSTGRESQL_USER_PASSWORD = os.getenv("POSTGRESQL_USER_PASSWORD")
DATABASE_NAME = os.getenv("DATABASE_NAME")

ADMIN_IDS = os.getenv("ADMIN_IDS").split()


class Flask_Config:
    SQLALCHEMY_DATABASE_URI = f"postgresql+psycopg2://{POSTGRESQL_USER}:{POSTGRESQL_USER_PASSWORD}@localhost/{DATABASE_NAME}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    CELERY_BROKER_URL = REDIS_DB_URL
    CELERY_RESULT_BACKEND = REDIS_DB_URL

    TESTNET = True
