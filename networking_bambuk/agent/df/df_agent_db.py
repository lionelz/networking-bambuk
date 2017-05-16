import traceback

from networking_bambuk.common import config
from networking_bambuk.common.config import timefunc
from networking_bambuk.rpc import bambuk_rpc

from oslo_log import log


LOG = log.getLogger(__name__)


class AgentDbDriver(bambuk_rpc.BambukRpc):
    """Bambuk Agent DB Driver for Dragonflow DB."""

    def __init__(self):
        """Constructor."""
        super(AgentDbDriver, self).__init__()
        
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
            self.clear_all()
            for entry in connect_db:
                self.create_key(entry['table'],
                                entry['key'],
                                entry['value'],
                                topic=None,
                                sync=False)
            self.sync()
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
                             cdb_update['value'],
                             topic=None,
                             sync=False)
            self.sync()
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
                                cdb_delete['key'],
                                topic=None,
                                sync=False)
            self.sync()
        except Exception:
            LOG.error(traceback.format_exc())
            return False
        return True

    ###############
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
