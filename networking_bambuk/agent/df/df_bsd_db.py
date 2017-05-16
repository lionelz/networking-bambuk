import os

from bsddb3 import db                   # the Berkeley db data base

from dragonflow.db import db_api

from networking_bambuk.agent.df import df_agent_db
from networking_bambuk.common import config

from oslo_log import log

from oslo_serialization import jsonutils


LOG = log.getLogger(__name__)


class BSDDbDriver(db_api.DbApi, df_agent_db.AgentDbDriver):
    """BSD DB Driver for Dragonflow DB."""

    def __init__(self):
        """Constructor."""
        super(BSDDbDriver, self).__init__()

    ##########################################################################
    def initialize(self, db_ip, db_port, **args):
        """Initialize the DB client.

        :param db_ip:      DB server IP address
        :type db_ip:       string
        :param db_port:    DB server port number
        :type db_port:     int
        :param args:       Additional args that were read from configuration
                           file
        :type args:        dictionary of <string, object>
        :returns:          None
        """
        LOG.info('BSDDbDriver initialize - begin')
        self._db_dir = config.db_dir()
        self._tables = {}

        LOG.info('BSDDbDriver initialize - end')

    def _get_db(self, table):
        if table in self._tables:
            return self._tables[table]
        filename = os.path.join(self._db_dir, table)
        tDB = db.DB()
        tDB.open(filename, None, db.DB_HASH, db.DB_CREATE)
        self._tables[table] = tDB
        tDB.sync()
        return tDB
        
    def create_table(self, table):
        """Create a table.

        :param table:      table name
        :type table:       string
        :returns:          None
        """
        self._get_db(table)

    def delete_table(self, table):
        """Delete a table.

        :param table:      table name
        :type table:       string
        :returns:          None
        """
        filename = os.path.join(self._db_dir, table)
        if table in self._tables:
            self._tables[table].close()
            del self._tables[table]
        os.remove(filename)

    def get_key(self, table, key, topic=None):
        """Get the value of a specific key in a table.

        :param table:      table name
        :type table:       string
        :param key:        key name
        :type key:         string
        :param topic:      topic for key
        :type topic:       string
        :returns:          string - the key value
        :raises:           DragonflowException.DBKeyNotFound if key not found
        """
        _db = self._get_db(table)
        value = _db.get(key)
        if value:
            return jsonutils.loads(value)
        return value

    def set_key(self, table, key, value, topic=None, sync=True):
        """Set a specific key in a table with value.

        :param table:      table name
        :type table:       string
        :param key:        key name
        :type key:         string
        :param value:      value to set for the key
        :type value:       string
        :param topic:      topic for key
        :type topic:       string
        :returns:          None
        :raises:           DragonflowException.DBKeyNotFound if key not found
        """
        _db = self._get_db(table)
        _db.put(key, jsonutils.dumps(value))
        if sync:
            _db.sync()

    def create_key(self, table, key, value, topic=None, sync=True):
        """Create a specific key in a table with value.

        :param table:      table name
        :type table:       string
        :param key:        key name
        :type key:         string
        :param value:      value to set for the created key
        :type value:       string
        :param topic:      topic for key
        :type topic:       string
        :returns:          None
        """
        _db = self._get_db(table)
        _db.put(key, jsonutils.dumps(value))
        if sync:
            _db.sync()

    def delete_key(self, table, key, topic=None, sync=True):
        """Delete a specific key from a table.

        :param table:      table name
        :type table:       string
        :param key:        key name
        :type key:         string
        :param topic:      topic for key
        :type topic:       string
        :returns:          None
        :raises:           DragonflowException.DBKeyNotFound if key not found
        """
        _db = self._get_db(table)
        _db.delete(key)
        if sync:
            _db.sync()

    def get_all_entries(self, table, topic=None):
        """Return a list of all table entries values.

        :param table:      table name
        :type table:       string
        :param topic:      get only entries matching this topic
        :type topic:       string
        :returns:          list of values
        :raises:           DragonflowException.DBKeyNotFound if key not found
        """
        _db = self._get_db(table)
        return [jsonutils.loads(v) for v in _db.values()]

    def get_all_keys(self, table, topic=None):
        """Return a list of all table entries keys.

        :param table:      table name
        :type table:       string
        :param topic:      get all keys matching this topic
        :type topic:       string
        :returns:          list of keys
        :raises:           DragonflowException.DBKeyNotFound if key not found
        """
        _db = self._get_db(table)
        return _db.keys()

    def sync(self):
        for table in self._tables:
            table.sync()

    def clear_all(self):
        for f in os.listdir(self._db_dir):
            self.delete_table(f)
