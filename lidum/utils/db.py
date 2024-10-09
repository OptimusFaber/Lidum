from datetime import datetime, timezone

from sqlalchemy.dialects.postgresql import JSON

from . import tasks_statuses
from .. import db
from .hash import sha256_hash
from .convert import address_to_raw, address_to_friendly


def add_database_entries(entries, session):
    "Загружает записи в базу данных"

    if not isinstance(entries, list):
        entries = [entries]

    for entry in entries:
        session.add(entry)
        session.commit()


def author_by_tg_id(telegram_id: str | int, session):
    return session.query(Author).filter_by(telegram_id=int(telegram_id)).first()


def subcriber_by_tg_id(telegram_id: str | int, session):
    return session.query(Subscriber).filter_by(telegram_id=int(telegram_id)).first()


def event_by_id(event_id: int, session):
    return session.query(Event).filter_by(id=event_id).first()


def event_ids_by_tg_id(telegram_id: str | int, session):
    """Возвращает список id событий, привязанных к id пользователя."""

    events = session.query(Event).filter_by(telegram_id=int(telegram_id)).all()

    if events is None:
        return []

    return [event.id for event in events]


def transaction_by_id(transaction_id: int, session):
    return session.query(Transaction).filter_by(id=transaction_id).first()


def wallet_addresses_by_tg_id(telegram_id: str | int, session):
    """Возвращает список адресов кошельков по привязанному id пользователя."""

    authors = session.query(Author).filter_by(chat_id=int(telegram_id)).all()

    if authors is None:
        return []

    return [author.wallet_address for author in authors]


def tg_user_by_id(telegram_id: str | int, session):
    return session.query(Telegram_User).filter_by(id=int(telegram_id)).first()


def authors_tg_ids(session):
    """Возвращает список id авторов событий."""

    authors = session.query(Author).filter(Author.chat_id.isnot(None)).all()

    if authors is None:
        return []

    return [author.chat_id for author in authors]


def tg_users(session):
    """Возвращает список id авторов событий."""
    return session.query(Telegram_User).filter(Telegram_User.id.isnot(None)).all()


class Author(db.Model):
    __tablename__ = "authors"

    telegram_id = db.Column(db.BigInteger, db.ForeignKey("telegram_users.id"), primary_key=True)
    collection_name = db.Column(db.String(64), nullable=False)
    _collection_address = db.Column("collection_address", db.String(66), nullable=False)
    collection_status = db.Column(db.Text, nullable=False, default=tasks_statuses.NEW)
    _is_testnet = db.Column("is_testnet", db.Boolean, nullable=False)

    @property
    def is_testnet(self):
        return bool(self._is_testnet)

    @is_testnet.setter
    def is_testnet(self, value):
        self._is_testnet = value

    @property
    def collection_address(self):
        return self._collection_address

    @collection_address.setter
    def collection_address(self, address):
        self._collection_address = address_to_friendly(address)


class Event(db.Model):
    __tablename__ = "events"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    telegram_id = db.Column(db.BigInteger, db.ForeignKey("authors.telegram_id"), nullable=False)
    event_name = db.Column(db.String(64), nullable=False)
    event_description = db.Column(db.Text, nullable=False)
    transaction_id = db.Column("transaction_id", db.BigInteger, db.ForeignKey("transactions.id"), nullable=False)
    minted_nfts = db.Column(db.Integer, nullable=False, default=0)
    nfts_cnt = db.Column(db.Integer, nullable=False)
    image_name = db.Column(db.Text, nullable=False)
    start_date = db.Column(db.String(16), nullable=False)
    end_date = db.Column(db.String(16), nullable=False)
    _password = db.Column("password", db.String(64), nullable=False)
    invites = db.Column(db.Integer, nullable=False)
    user_timezone = db.Column(db.SmallInteger, nullable=False)
    subscriptions = db.Column(JSON, nullable=False)

    @property
    def password(self):
        return self._password

    @password.setter
    def password(self, password):
        self._password = sha256_hash(password)


class Subscriber(db.Model):
    __tablename__ = "subscribers"

    telegram_id = db.Column(db.BigInteger, db.ForeignKey("telegram_users.id"), primary_key=True)
    visited_channels = db.Column(JSON, default=[])
    participated_events = db.Column(JSON, default=[])


class Transaction(db.Model):
    __tablename__ = "transactions"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    hash = db.Column(db.String(64))
    _source_address = db.Column("source_address", db.String(66), nullable=False)
    _destination_address = db.Column("destination_address", db.String(66), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.Text, nullable=False, default=tasks_statuses.NEW)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), nullable=False)
    _is_testnet = db.Column("is_testnet", db.Boolean, nullable=False)

    @property
    def is_testnet(self):
        return bool(self._is_testnet)

    @is_testnet.setter
    def is_testnet(self, value):
        self._is_testnet = value

    @property
    def source_address(self):
        return self._source_address

    @source_address.setter
    def source_address(self, address):
        self._source_address = address_to_raw(address)

    @property
    def destination_address(self):
        return self._destination_address

    @destination_address.setter
    def destination_address(self, address):
        self._destination_address = address_to_raw(address)


class Drop(db.Model):
    __tablename__ = "drops"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    telegram_id = db.Column(db.BigInteger, db.ForeignKey("authors.telegram_id"), nullable=False)
    start_date = db.Column(db.String(16), nullable=False)
    end_date = db.Column(db.String(16), nullable=False)
    price = db.Column(db.Float, nullable=False)
    prizes = db.Column(JSON, nullable=False)

    @property
    def wallet_address(self):
        return self._wallet_address

    @wallet_address.setter
    def wallet_address(self, address):
        self._wallet_address = address_to_friendly(address)


class Telegram_User(db.Model):
    __tablename__ = "telegram_users"

    id = db.Column(db.BigInteger, primary_key=True)
    username = db.Column(db.String(32), nullable=False)
    last_enter = db.Column(db.DateTime, default=datetime.now(timezone.utc), nullable=False)
