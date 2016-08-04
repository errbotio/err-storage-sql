import py
import pytest
import shutil
import tempfile
from errbot.backends.test import testbot
from os import path

STORAGE_CONFIG = {
    'StorageType': 'Memory'
}
extra_plugin_dir = path.join(path.dirname(path.realpath(__file__)),
                             'storagetest_plugin')


def connect_string(dialect):
    return {
        'mysql': 'mysql+pymysql://travis:@localhost/travis_ci_test',
        'postgres': 'postgresql://postgres:@localhost/travis_ci_test',
        'sqlite': 'sqlite:////tmp/errbot.db',
    }[dialect]


def config(dialect, restore=False):
    return {
        'STORAGE': 'SQL',
        'BOT_EXTRA_STORAGE_PLUGINS_DIR': path.join(
            path.dirname(path.realpath(__file__)), '..'),
        'STORAGE_CONFIG': {
            "data_url": connect_string(dialect)}}


@pytest.fixture(scope='session')
def sessiondir(request):
    d = py.path.local(tempfile.mkdtemp())
    request.addfinalizer(lambda: d.remove(rec=1))
    return d


@pytest.fixture
def restore_path(sessiondir):
    return sessiondir


@pytest.fixture
def restore_file(sessiondir):
    return '{}/backup.py'.format(sessiondir)


def test_run_backup(testbot, restore_file):
    backup_file = testbot.bot_config.BOT_DATA_DIR + '/backup.py'
    assert 'Plugin configuration done.' in testbot.exec_command(
        '!plugin config Storagetest {!r}'.format(STORAGE_CONFIG))

    assert '{!r}'.format(STORAGE_CONFIG) in \
        testbot.exec_command('!plugin config Storagetest')

    assert "The backup file has been written in '{}'".format(backup_file) in \
        testbot.exec_command('!backup')

    shutil.copy2(backup_file, restore_file)


restore_backup = True

extra_config = config('mysql')


def test_mysql_storage(testbot):
    assert '{!r}'.format(STORAGE_CONFIG) in \
        testbot.exec_command('!plugin config Storagetest')


extra_config = config('sqlite')


def test_sqlite_storage(testbot):
    assert '{!r}'.format(STORAGE_CONFIG) in \
        testbot.exec_command('!plugin config Storagetest')


extra_config = config('postgres')


def test_postgres_storage(testbot):
    assert '{!r}'.format(STORAGE_CONFIG) in \
        testbot.exec_command('!plugin config Storagetest')
