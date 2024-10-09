import logging
from os import makedirs
from typing import Any
from os.path import join
from collections.abc import Callable, Awaitable

from flask import Flask, has_app_context
from celery import Celery
from aiogram import Bot, Dispatcher, BaseMiddleware
from aiogram.types import Update
from flask_limiter import Limiter
from sqlalchemy.orm import sessionmaker, scoped_session
from flask_sqlalchemy import SQLAlchemy
from flask_limiter.util import get_remote_address
from cryptography.fernet import Fernet
from aiogram.dispatcher.router import Router
from aiogram.fsm.storage.redis import RedisStorage

from .config import BOT_TOKEN, LOGS_PATH, REDIS_ADDRESS
from .config import FERNET_PRIVATE_KEY, Flask_Config
from .utils.ton_client import TonClient

_app = None
_session_factory = None
_Session = None

db = SQLAlchemy()
fernet = Fernet(FERNET_PRIVATE_KEY)
limiter = Limiter(get_remote_address, storage_uri=REDIS_ADDRESS, default_limits=["5 per second"])

client = TonClient(is_testnet=Flask_Config.TESTNET)


def create_session(app: Flask):

    with app.app_context():
        session_factory = sessionmaker(bind=db.engine)
        Session = scoped_session(session_factory)

    return session_factory, Session


def get_session(app: Flask):
    global _session_factory
    global _Session

    if _session_factory is None or _Session is None:
        _session_factory, _Session = create_session(app)

    return _session_factory, _Session


def create_bot(app: Flask):
    """Создает экземпляр Telegram-бота, работающий в контексте app."""

    bot = Bot(token=BOT_TOKEN)

    storage = RedisStorage.from_url(REDIS_ADDRESS)
    dp = Dispatcher(storage=storage)

    router = Router()
    dp.include_router(router)

    class AppContextMiddleware(BaseMiddleware):
        def __init__(self, app: Flask):
            self.app = app
            super().__init__()

        async def __call__(
            self,
            handler: Callable[[Update, dict[str, Any]], Awaitable[Any]],
            event: Update,
            data: dict[str, Any],
        ):
            with self.app.app_context():
                return await handler(event, data)

    dp.update.middleware(AppContextMiddleware(app))

    return bot, dp, router


def create_celery(app: Flask):
    """Создает экземпляр celery, работающий в контексте app."""

    celery = Celery(__name__)

    celery.conf.broker_url = app.config["CELERY_BROKER_URL"]
    celery.conf.result_backend = app.config["CELERY_RESULT_BACKEND"]

    celery.conf.update(app.config)
    TaskBase = celery.Task

    class ContextTask(TaskBase):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)

    celery.Task = ContextTask
    return celery


def get_app():
    """Возвращает текущий экземпляр Flask, либо инициализирует новый экземпляр."""
    global _app

    if _app is None:
        _app = create_app()

    if not has_app_context():
        with _app.app_context():
            return _app

    return _app


def create_app():
    """Создает экземпляр Flask и инициализирует необходимые части приложения."""

    makedirs(LOGS_PATH, exist_ok=True)

    logging.basicConfig(
        level=logging.ERROR,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(join(LOGS_PATH, "lidum.log")),
            logging.StreamHandler(),
        ],
    )

    app = Flask(__name__)
    app.config.from_object(Flask_Config)

    limiter.init_app(app)
    db.init_app(app)

    with app.app_context():
        db.create_all()

    return app
