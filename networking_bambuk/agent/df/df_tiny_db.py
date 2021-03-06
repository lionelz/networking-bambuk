import os

from dragonflow.db import db_api

from networking_bambuk.agent.df import df_agent_db
from networking_bambuk.common import config

from oslo_log import log

from oslo_utils import importutils

from tinydb import Query
from tinydb import TinyDB

LOG = log.getLogger(__name__)


class TinyDbDriver(db_api.DbApi, df_agent_db.AgentDbDriver):
    """Tiny DB Driver for Dragonflow DB."""

    def __init__(self):
        """Constructor."""
        super(TinyDbDriver, self).__init__()

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
        LOG.info('TinyDbDriver initialize - begin')
        file_db = os.path.join(config.db_dir(), 'connect_db.json')

        # start the configured receiver
        LOG.info('TinyDbDriver json file: %s' % file_db)
        self._file_db = file_db
        if not self._already_started(file_db):
            LOG.info('TinyDbDriver initializing bambuk receiver')
            self._bambuk_receiver = importutils.import_object(
                config.receiver(), bambuk_agent=self)
        LOG.info('TinyDbDriver initialize - end')

    @property
    def _db(self):
        if not hasattr(self, '_db_obj'):
            # open json file with tinyDb
            self._db_obj = TinyDB(self._file_db)
        return self._db_obj
        
    def create_table(self, table):
        """Create a table.

        :param table:      table name
        :type table:       string
        :returns:          None
        """
        self._db.table(table)

    def delete_table(self, table):
        """Delete a table.

        :param table:      table name
        :type table:       string
        :returns:          None
        """
        self._db.purge_table(table)

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
        t_entries = self._db.table(table)
        entry = t_entries.get(Query().key == key)
        if entry:
            return entry['value']
        else:
            return None

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
        t_entries = self._db.table(table)
        if t_entries.get(Query().key == key):
            t_entries.update({'value': value}, Query().key == key)
        else:
            self.create_key(table, key, value, topic)

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
        t_entries = self._db.table(table)
        t_entries.insert({'key': key, 'value': value})

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
        t_entries = self._db.table(table)
        t_entries.remove(Query().key == key)

    def get_all_entries(self, table, topic=None):
        """Return a list of all table entries values.

        :param table:      table name
        :type table:       string
        :param topic:      get only entries matching this topic
        :type topic:       string
        :returns:          list of values
        :raises:           DragonflowException.DBKeyNotFound if key not found
        """
        t_entries = self._db.table(table)
        res = []
        for entry in t_entries.all():
            res.append(entry['value'])
        return res

    def get_all_keys(self, table, topic=None):
        """Return a list of all table entries keys.

        :param table:      table name
        :type table:       string
        :param topic:      get all keys matching this topic
        :type topic:       string
        :returns:          list of keys
        :raises:           DragonflowException.DBKeyNotFound if key not found
        """
        t_entries = self._db.table(table)
        res = []
        for entry in t_entries.all():
            res.append(entry['key'])
        return res

    def support_publish_subscribe(self):
        """Return if this DB support publish-subscribe.

           If this method returns True, the DB driver needs to
           implement register_notification_callback() API in this class

        :returns:          boolean (True or False)
        """
        return False

    def register_notification_callback(self, callback, topics=None):
        """Register for DB changes notifications.

           DB driver should call callback method for every change.
           DB driver is responsible to start the appropriate listener
           threads on DB changes and send changes to callback.

           Returning the callback with action=='sync' will trigger
           a full sync process by the controller
           (Reading all entries for all tables)

        :param callback:  callback method to call for every db change
        :type callback :  callback method of type:
                          callback(table, key, action, value)
                          table - table name
                          key - object key
                          action = 'create' / 'set' / 'delete' / 'sync'
                          value = new object value
        :param topics:    topics to register for DB notifications
        :type topics :     list of strings (topics)
        :returns:         None
        """
        pass

    def register_topic_for_notification(self, topic):
        """Register new topic, start receiving updates on this topic.

        :param topic:  topic to register for DB notifications
        :type topic :  string
        :returns:      None
        """
        pass

    def unregister_topic_for_notification(self, topic):
        """Un-register topic, stop receiving updates on this topic.

        :param topic:  topic to un-register for DB notifications
        :type topic :  string
        :returns:      None
        """
        pass

    def allocate_unique_key(self):
        """Allocate a unique id in the system.

           Used to allocate ports unique numbers

        :returns:     Unique id
        """
        return '1'

    def process_ha(self):
        # Not needed in this driver
        pass

    def set_neutron_server(self, is_neutron_server):
        # Not needed in this driver
        pass
    ##########################################################################

    ##########################################################################
    def sync(self):
        pass

    def clear_all(self):
        self._db.purge_tables()
    ##########################################################################
