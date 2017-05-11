import os
import subprocess
import traceback

from dragonflow.db import db_api

from networking_bambuk.common import config
from networking_bambuk.common.config import timefunc
from networking_bambuk.rpc import bambuk_rpc

from oslo_log import log

from oslo_utils import importutils

from tinydb import Query
from tinydb import TinyDB

LOG = log.getLogger(__name__)


def already_started(f):
    proc = subprocess.Popen(
        ['sudo', 'lsof'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    stdout, _ = proc.communicate()
    for l in stdout.split():
        if f in l:
            return True
    return False


class TinyDbDriver(db_api.DbApi, bambuk_rpc.BambukRpc):
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
        file_db = config.json_db_cache()
        if not os.path.exists(file_db) and file_db.split('.')[-1] != 'json':
            os.makedirs(file_db)
        if os.path.isdir(file_db):
            file_db = os.path.join(file_db, 'connect_db.json')
        # start the configured receiver
        LOG.info('TinyDbDriver json file: %s' % file_db)
        self._file_db = file_db
        if not already_started(file_db):
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
        
    def support_publish_subscribe(self):
        """Return if this DB support publish-subscribe.

           If this method returns True, the DB driver needs to
           implement register_notification_callback() API in this class

        :returns:          boolean (True or False)
        """
        return False

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

    def set_key(self, table, key, value, topic=None):
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

    def create_key(self, table, key, value, topic=None):
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

    def delete_key(self, table, key, topic=None):
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

    def _clear_all(self):
        self._db.purge_tables()

    #########################################################################
    def state(self, server_conf):
        """Return the agent configuration."""
        try:
            LOG.info('state(%s)', server_conf)
            # TODO(lionelz): use the server conf to keep the server ip in db
            self.server_conf = server_conf
            # TODO(lionelz): implement agent state
            self.agent_state = {
                'binary': 'bambuk-openvswitch-agent',
                'host': config.host(),
                'topic': 'N/A',
                'configurations': {
                    'tunnel_types': ['vxlan'],
                    'tunneling_ip': server_conf['local_ip'],
                    'l2_population': True,
                    'arp_responder_enabled': True,
                    'enable_distributed_routing': True,
                },
                'agent_type': 'bambuk-agent',
                'start_flag': True
            }
        except Exception:
            LOG.error(traceback.format_exc())
            return False
        return self.agent_state

    @timefunc
    def apply(self, connect_db):
        """Add objects to the database."""
        try:
            LOG.info('apply(%s)', connect_db)
            self._clear_all()
            for entry in connect_db:
                self.create_key(entry['table'], entry['key'], entry['value'])
        except Exception:
            LOG.error(traceback.format_exc())
            return False
        return True

    @timefunc
    def update(self, connect_db_update):
        """Update objects in the database."""
        try:
            if isinstance(connect_db_update, list):
                cdb_updates = connect_db_update
            else:
                cdb_updates = [connect_db_update]
            for cdb_update in cdb_updates:
                self.set_key(cdb_update['table'],
                             cdb_update['key'],
                             cdb_update['value'])
        except Exception:
            LOG.error(traceback.format_exc())
            return False
        return True

    def delete(self, connect_db_delete):
        """Delete objects from the database."""
        try:
            if isinstance(connect_db_delete, list):
                cdb_deletes = connect_db_delete
            else:
                cdb_deletes = [connect_db_delete]
            for cdb_delete in cdb_deletes:
                self.delete_key(cdb_delete['table'],
                                cdb_delete['key'])
        except Exception:
            LOG.error(traceback.format_exc())
            return False
        return True

    def process_ha(self):
        # Not needed in this driver
        pass

    def set_neutron_server(self, is_neutron_server):
        # Not needed in this driver
        pass
