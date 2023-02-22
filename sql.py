# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

import logging
from contextlib import contextmanager
from jsonpickle import encode, decode
from typing import Any
from sqlalchemy import (
    Table, MetaData, Column, Integer, String,
    ForeignKey, create_engine, select)
from sqlalchemy.orm import registry, sessionmaker
from sqlalchemy.orm.exc import NoResultFound
from errbot.storage.base import StorageBase, StoragePluginBase

log = logging.getLogger('errbot.storage.sql')

DATA_URL_ENTRY = 'data_url'


class KV(object):
    """This is a basic key/value. Pickling in JSON."""
    def __init__(self, key: str, value: Any):
        self._key = key
        self._value = encode(value)

    @property
    def key(self) -> str:
        return self._key

    @property
    def value(self) -> Any:
        return decode(self._value)


class SQLStorage(StorageBase):
    def __init__(self, session, clazz):
        self.session = session
        self.clazz = clazz

    @contextmanager
    def _session_op(self):
        try:
            yield self.session
            self.session.commit()
        except:
            self.session.rollback()
            raise

    def get(self, key: str) -> Any:
        try:
            with self._session_op() as session:
                result = session.query(self.clazz).filter(self.clazz._key == key).one().value
        except NoResultFound:
            raise KeyError("%s doesn't exists." % key)
        return result

    def remove(self, key: str):
        try:
            with self._session_op() as session:
                session.query(self.clazz).filter(self.clazz._key == key).delete()
        except NoResultFound:
            raise KeyError("%s doesn't exists." % key)

    def set(self, key: str, value: Any) -> None:
        with self._session_op() as session:
            session.merge(self.clazz(key, value))

    def len(self):
        with self._session_op() as session:
            length = session.query(self.clazz).count()
        return length

    def keys(self):
        return (kv.key for kv in self.session.query(self.clazz).all())

    def close(self) -> None:
        self.session.commit()


class SQLPlugin(StoragePluginBase):
    def __init__(self, bot_config):
        super().__init__(bot_config)
        config = self._storage_config
        if DATA_URL_ENTRY not in config:
            raise Exception(
                'You need to specify a connection URL for the database in your'
                'config.py. For example:\n'
                'STORAGE_CONFIG={\n'
                '"data_url": "postgresql://'
                'scott:tiger@localhost/mydatabase/",\n'
                '}')

        # Hack around the multithreading issue in memory only sqlite.
        # This mode is useful for testing.
        if config[DATA_URL_ENTRY].startswith('sqlite://'):
            from sqlalchemy.pool import StaticPool
            self._engine = create_engine(
                config[DATA_URL_ENTRY],
                connect_args={'check_same_thread': False},
                poolclass=StaticPool,
                echo=bot_config.BOT_LOG_LEVEL == logging.DEBUG)
        else:
            self._engine = create_engine(
                config[DATA_URL_ENTRY],
                pool_recycle=config.get('connection_recycle', 1800),
                pool_pre_ping=config.get('connection_ping', True),
                echo=bot_config.BOT_LOG_LEVEL == logging.DEBUG)
        self._mapper_registry = registry()
        self._metadata = self._mapper_registry.metadata
        self._sessionmaker = sessionmaker()
        self._sessionmaker.configure(bind=self._engine)

    def open(self, namespace: str) -> StorageBase:

        # Create a table with the given namespace
        table = Table(namespace, self._metadata,
                      Column('key', String(767), primary_key=True),
                      Column('value', String(32768)),
                      extend_existing=True)

        class NewKV(KV):
            pass

        self._mapper_registry.map_imperatively(NewKV, table, properties={
            '_key': table.c.key,
            '_value': table.c.value})

        # ensure that the table for this namespace exists
        self._metadata.create_all(self._engine)

        # create an autonomous session for it.
        return SQLStorage(self._sessionmaker(), NewKV)
