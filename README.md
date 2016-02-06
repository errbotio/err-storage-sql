## SQL storage plugin for errbot


### About
[Errbot](http://errbot.io) is a python chatbot, this storage plugin allows you to use it with SQL databases as a persistent storage.
By using [SQLAlchemy](sqlalchemy.org), it has the support for Firebird, Microsoft SQL Server, MySQL, Oracle, PostgreSQL, SQLite, Sybase, IBM DB2, Amazon Redshift, exasol, Sybase SQL Anywhere, MonetDB.

### Installation

1. Install the support for the database you want to use. See [SQLalchemy doc](http://docs.sqlalchemy.org/en/latest/dialects/)
2. Then you need to add this section to your config.py, following this example:
 ```python
 BOT_EXTRA_STORAGE_PLUGINS_DIR='/home/gbin/err-storage'
 STORAGE = 'SQL'
 STORAGE_CONFIG = {
    'data_url': 'postgresql://scott:tiger@localhost/test',
    }
 ```

3. Start your bot in text mode: `errbot -T` to give it a shot.

If you want to migrate from the local storage to SQL, you should be able to backup your data (with STORAGE commented)
then restore it back with STORAGE uncommented.
