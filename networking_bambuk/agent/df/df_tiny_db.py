#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
#

import sys

from dragonflow.db import db_api

from networking_bambuk.common import config
from networking_bambuk.rpc import bambuk_rpc

from oslo_log import log

from oslo_utils import importutils

from tinydb import TinyDB, Query

LOG = log.getLogger(__name__)


class TinyDbDriver(db_api.DbApi, bambuk_rpc.BambukRpc):
    
    def __init__(self):
        super(TinyDbDriver, self).__init__()

    ##########################################################################
    def initialize(self, db_ip, db_port, **args):
        # open json file with tinyDb
        self._db = TinyDB(config.get_json_db_cache())
        # start the configured receiver
        self._bambuk_receiver = importutils.import_object(
            config.get_receiver(), bambuk_agent=self)
        # TODO: check if server in DB and refresh the connectivity DB

    def support_publish_subscribe(self):
        return False

    def create_table(self, table):
        self._db.table(table)

    def delete_table(self, table):
        self._db.purge_table(table)

    def get_key(self, table, key, topic=None):
        t_entries = self._db.table(table)
        entry = t_entries.get(Query().key == key)
        if entry:
            return entry['value']
        else:
            return None

    def set_key(self, table, key, value, topic=None):
        t_entries = self._db.table(table)
        if t_entries.get(Query().key == key):
            t_entries.update({'value': value}, Query().key == key)
        else:
            self.create_key(table, key, value, topic)

    def create_key(self, table, key, value, topic=None):
        t_entries = self._db.table(table)
        t_entries.insert({'key': key, 'value': value})

    def delete_key(self, table, key, topic=None):
        t_entries = self._db.table(table)
        t_entries.remove(Query().key == key)

    def get_all_entries(self, table, topic=None):
        t_entries = self._db.table(table)
        res = []
        for entry in t_entries.all():
            res.append(entry['value'])
        return res

    def get_all_keys(self, table, topic=None):
        t_entries = self._db.table(table)
        res = []
        for entry in t_entries.all():
            res.append(entry['key'])
        return res

    def register_notification_callback(self, callback, topics=None):
        pass

    def register_topic_for_notification(self, topic):
        pass

    def unregister_topic_for_notification(self, topic):
        pass

    def allocate_unique_key(self):
        return '1'

    def clear_all(self):
        self._db.purge_tables()

    #########################################################################
    def state(self, server_conf):
        try:
            # TODO: use the server conf to keep the server ip in db
            self.server_conf = server_conf
            # TODO: implement agent state
            self.agent_state = {
                'binary': 'bambuk-openvswitch-agent',
                'host': server_conf['device_id'],
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
        except:
            e = sys.exc_info()[0]
            LOG.error('an error occurs %s' % e)
            return False
        return self.agent_state

    def apply(self, connect_db):
        try:
            self.clear_all()
            for entry in connect_db:
                self.create_key(entry['table'], entry['key'], entry['value'])
        except Exception:
            LOG.error('an error occurs', sys.exc_info())
            return False
        return True

    def update(self, connect_db_update):
        try:
            self.set_key(connect_db_update['table'],
                         connect_db_update['key'],
                         connect_db_update['value'])
        except:
            e = sys.exc_info()[0]
            LOG.error('an error occurs %s' % e)
            return False
        return True

    def delete(self, connect_db_delete):
        try:
            self.delete_key(connect_db_delete['table'],
                            connect_db_delete['key'])
        except:
            e = sys.exc_info()[0]
            LOG.error('an error occurs %s' % e)
            return False
        return True
