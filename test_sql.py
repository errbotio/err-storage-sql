import logging

import pytest
from sqlalchemy.exc import ArgumentError

import sql


class MockBotConfig:
    def __init__(self, data_url=None):
        self.STORAGE_CONFIG = {}
        if data_url is not None:
            self.STORAGE_CONFIG["data_url"] = data_url
        self.BOT_LOG_LEVEL = logging.WARNING


def test_plugin_init_missing_config():
    config = MockBotConfig()
    with pytest.raises(Exception, match="You need to specify a connection URL"):
        sql.SQLPlugin(config)


def test_plugin_init_invalid_url():
    config = MockBotConfig(data_url="invalid_url://")
    with pytest.raises((ArgumentError, Exception)):
        plugin = sql.SQLPlugin(config)
        plugin.open("test")


def test_storage_operations():
    config = MockBotConfig(data_url="sqlite:///:memory:")
    plugin = sql.SQLPlugin(config)
    storage = plugin.open("test_namespace")

    # Initial state
    assert storage.len() == 0
    assert list(storage.keys()) == []

    # Get non-existent
    with pytest.raises(KeyError):
        storage.get("key1")

    # Set and get basic values
    storage.set("key1", "value1")
    assert storage.len() == 1
    assert storage.get("key1") == "value1"
    assert list(storage.keys()) == ["key1"]

    # Set and get complex objects (list, dict, int)
    storage.set("key2", {"a": 1, "b": [2, 3]})
    assert storage.len() == 2
    assert storage.get("key2") == {"a": 1, "b": [2, 3]}
    assert set(storage.keys()) == {"key1", "key2"}

    # Overwrite value
    storage.set("key1", "new_value1")
    assert storage.get("key1") == "new_value1"

    # Remove non-existent key
    with pytest.raises(KeyError):
        storage.remove("nonexistent")

    # Remove existing key
    storage.remove("key1")
    assert storage.len() == 1
    with pytest.raises(KeyError):
        storage.get("key1")

    assert list(storage.keys()) == ["key2"]

    # Close storage
    storage.close()


def test_multiple_namespaces():
    config = MockBotConfig(data_url="sqlite:///:memory:")
    plugin = sql.SQLPlugin(config)

    storage_a = plugin.open("namespace_a")
    storage_b = plugin.open("namespace_b")

    storage_a.set("shared_key", "value_a")
    storage_b.set("shared_key", "value_b")

    assert storage_a.get("shared_key") == "value_a"
    assert storage_b.get("shared_key") == "value_b"

    assert storage_a.len() == 1
    assert storage_b.len() == 1

    storage_a.close()
    storage_b.close()


def test_simple_store_retrieve():
    from errbot.storage import StoreMixin

    config = MockBotConfig(data_url="sqlite:///:memory:")
    plugin = sql.SQLPlugin(config)
    sm = StoreMixin()
    sm.open_storage(plugin, "ns")
    sm["toto"] = "titui"
    assert sm["toto"] == "titui"
    sm.close_storage()


def test_mutable():
    from errbot.storage import StoreMixin

    config = MockBotConfig(data_url="sqlite:///:memory:")
    plugin = sql.SQLPlugin(config)
    sm = StoreMixin()
    sm.open_storage(plugin, "ns")
    sm["toto"] = [1, 3]

    with sm.mutable("toto") as titi:
        titi[1] = 5

    assert sm["toto"] == [1, 5]
    sm.close_storage()
