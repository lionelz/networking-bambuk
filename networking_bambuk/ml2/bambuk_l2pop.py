
from neutron.agent import rpc as agent_rpc
from neutron.common import topics
from neutron.plugins.ml2.drivers.l2pop.rpc_manager import l2population_rpc

from oslo_log import log

LOG = log.getLogger(__name__)


class BambukL2Pop(l2population_rpc.L2populationRpcCallBackTunnelMixin):

    def __init__(self):
        self.connection = agent_rpc.create_consumers(
            [self],
            topics.AGENT,
            [topics.L2POPULATION, topics.UPDATE],
            start_listening=False
        )
        self.connection.consume_in_threads()

    def fdb_add(self, context, fdb_entries):
        LOG.debug('fdb_add %s' % fdb_entries)

    def fdb_remove(self, context, fdb_entries):
        LOG.debug('fdb_remove %s' % fdb_entries)

    def add_fdb_flow(self, br, port_info, remote_ip, lvm, ofport):
        LOG.debug('add_fdb_flow %s, %s, %s, %s, %s' % (
            br, port_info, remote_ip, lvm, str(ofport)))

    def del_fdb_flow(self, br, port_info, remote_ip, lvm, ofport):
        LOG.debug('del_fdb_flow %s, %s, %s, %s, %s' % (
            br, port_info, remote_ip, lvm, str(ofport)))

    def setup_tunnel_port(self, br, remote_ip, network_type):
        LOG.debug('setup_tunnel_port %s, %s, %s' % (
            br, remote_ip, network_type))

    def cleanup_tunnel_port(self, br, tun_ofport, tunnel_type):
        LOG.debug('cleanup_tunnel_port %s, %s, %s' % (
            br, tun_ofport, tunnel_type))

    def setup_entry_for_arp_reply(self, br, action, local_vid, mac_address,
                                  ip_address):
        LOG.debug('setup_entry_for_arp_reply %s, %s, %s, %s, %s' % (
            br, action, local_vid, mac_address, ip_address))
