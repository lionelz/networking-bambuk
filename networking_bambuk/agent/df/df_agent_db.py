import subprocess
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
        
    def _already_started(self, f):
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
