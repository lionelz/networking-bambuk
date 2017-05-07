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

import netaddr

from neutron import context as n_context
from neutron.extensions import allowedaddresspairs as addr_pair
from neutron.extensions import portsecurity as psec
from neutron import manager

from oslo_log import log as o_log

from oslo_serialization import jsonutils

LOG = o_log.getLogger(__name__)


def lport(port):
    ips = [ip['ip_address'] for ip in port.get('fixed_ips', [])]
    subnets = [ip['subnet_id'] for ip in port.get('fixed_ips', [])]
    chassis = port.get('binding:host_id', None)
    lport = {}
    lport['id'] = port['id']
    lport['topic'] = port['tenant_id']
    lport['remote_vtep'] = False
    lport['lswitch'] = port['network_id']
    lport['macs'] = [port['mac_address']]
    lport['ips'] = ips
    lport['name'] = port.get('name', 'no_port_name')
    lport['enabled'] = port.get('admin_state_up', None)
    lport['chassis'] = chassis
    lport['unique_key'] = port['standard_attr_id']
    lport['device_owner'] = port.get('device_owner', None)
    lport['device_id'] = port.get('device_id', None)
    lport['security_groups'] = port.get('security_groups', None)
    lport['port_security_enabled'] = port.get(psec.PORTSECURITY, False)
    lport['allowed_address_pairs'] = (
        port.get(addr_pair.ADDRESS_PAIRS, None))

    lport['subnets'] = subnets
    lport['binding_profile'] = port.get('binding:profile')
    lport['extra_dhcp_opts'] = port.get('extra_dhcp_opts')
    lport['device_owner'] = port.get('device_owner')
    lport['device_id'] = port.get('device_id')
    lport['version'] = 1
    lport['qos_policy_id'] = None
    lport['binding_vnic_type'] = port.get('binding:vnic_type')
  
    return lport


def lsecgroup(sg):
    secgroup = {}
    secgroup['id'] = sg['id']
    secgroup['topic'] = sg['tenant_id']
    secgroup['name'] = sg.get('name', 'no_sg_name')
    secgroup['rules'] = []
    secgroup['version'] = 1
    for sgr in sg['security_group_rules']:
        secgroupr = {}
        for k in ['id', 'direction', 'protocol', 'port_range_max',
                  'remote_group_id', 'remote_ip_prefix',
                  'security_group_id', 'port_range_min', 'ethertype']:
            secgroupr[k] = sgr[k]
        secgroupr['topic'] = sg['tenant_id']
        secgroupr['version'] = 1
        secgroupr['version'] = 1
        secgroup['rules'].append(secgroupr)
    secgroup['unique_key'] = sg['standard_attr_id']
    return secgroup


def lsubnet(subnet):
    lsubnet = {}
    lsubnet['id'] = subnet['id']
    lsubnet['topic'] = subnet['tenant_id']
    lsubnet['name'] = subnet.get('name', 'no_subnet_name')
    lsubnet['enable_dhcp'] = subnet['enable_dhcp']
    lsubnet['cidr'] = subnet['cidr']
    lsubnet['dhcp_ip'] = subnet['allocation_pools'][0]['start']
    lsubnet['gateway_ip'] = subnet['gateway_ip']
    lsubnet['dns_nameservers'] = subnet.get('dns_nameservers', [])
    lsubnet['host_routes'] = subnet.get('host_routes', [])
    return lsubnet

def lswitch(network, subnets):
    lswitch = {}
    lswitch['id'] = network['id']
    lswitch['topic'] = network['tenant_id']
    lswitch['name'] = network.get('name', 'no_network_name')
    lswitch['network_type'] = network.get('provider:network_type')
    lswitch['segmentation_id'] = network.get('provider:segmentation_id')
    lswitch['is_external'] = network['router:external']
    lswitch['mtu'] = network.get('mtu')
    lswitch['subnets'] = [lsubnet(subnet) for subnet in subnets]
    lswitch['unique_key'] = network['standard_attr_id']
    lswitch['version'] = 1
    return lswitch


class BambukPortInfo(object):
    """Port info object, used to construct the messages to the clients."""

    def __init__(self, port, other_ports, endpoints, router, router_ports):
        """Constructor."""
        self._plugin_property = None
        self._port = port
        self._other_ports = other_ports
        self._endpoints = endpoints
        self._router = router
        self._router_ports = router_ports
        self._calculate_obj()

    @property
    def _plugin(self):
        if self._plugin_property is None:
            self._plugin_property = manager.NeutronManager.get_plugin()
        return self._plugin_property

    def _get_subnet(self, subnets, subnet_id):
        if subnet_id not in subnets:
            # Try to read the network if it is not in the cache
            ctx = n_context.get_admin_context()
            subnets[subnet_id] = self._plugin.get_subnet(ctx, subnet_id)
        return subnets[subnet_id]

    def _get_lswitch(self, ctx, port, subnets):
        """Create a lswitch object for a given port."""
        network = self._plugin.get_network(ctx, port['network_id'])
        _subnets = self._plugin.get_subnets(
            ctx,
            filters={'network_id': [port['network_id']]})
        for subnet in _subnets:
            subnets[subnet['id']] = subnet
        return lswitch(network, _subnets), network

    # TODO(lionelz): As the segmentation ID code is commented out,
    #                can we remove this and use the _get_lswitch instead?
    def _get_port_lswitch(self, ctx, port, subnets):
        """Create a lswitch object for the updated port.

        This will also set the segmentation ID for our port
        """
        lswitch, network = self._get_lswitch(ctx, port, subnets)
        self.segmentation_id = network.get('provider:segmentation_id')
        return lswitch

    def _calculate_obj(self):
        ctx = n_context.get_admin_context()

        # logical switch
        subnets = {}
        self.lswitches = {}
        if self._port:
            lswitch = self._get_port_lswitch(ctx, self._port, subnets)
            self.lswitches[lswitch['id']] = lswitch
        # Get lswitch for other networks as well...
        if self._router_ports:
            for port in self._router_ports:
                lswitch, _ = self._get_lswitch(ctx, port, subnets)
                if lswitch['id'] not in self.lswitches:
                    self.lswitches[lswitch['id']] = lswitch

        # port
        if self._port:
            self.lport = lport(self._port)
        else:
            self.lport = None

        # router
        self.lrouter = self._lrouter(
            self._router, self._router_ports, subnets)

        # other ports
        self.other_lports = []
        for port in self._other_ports:
            if port.get('device_owner').startswith('nova:'):
                self.other_lports.append(lport(port))

        # security groups
        self.secgroup = []
        if self.lport and self.lport['security_groups']:
            sgs = self._plugin.get_security_groups(
                ctx, {'id': self.lport['security_groups']})
            for sg in sgs:
                self.secgroup.append(lsecgroup(sg))

        # list of chassis
        self.chassis = []
        LOG.debug(self._endpoints)
        for entry in self._endpoints:
            for tunnel in entry['tunnels']:
                self.chassis.append({
                    'tunnel_types': [entry['tunnel_type']],
                    'ip': tunnel['ip_address'],
                    'id': tunnel['host'],
                })

    def port_db(self, c_db_in=None):
        """Return a DB representation of the ports."""
        if c_db_in:
            c_db = c_db_in
        else:
            c_db = []
        if self.lport:
            c_db.append({
                'table': 'lport',
                'key': self.lport['id'],
                'value': jsonutils.dumps(self.lport)
            })
        return c_db

    def chassis_db(self, c_db_in=None):
        """Return a DB representation of the chassis."""
        if c_db_in:
            c_db = c_db_in
        else:
            c_db = []
        # list of chassis
        for chassis in self.chassis:
            c_db.append({
                'table': 'chassis',
                'key': chassis['id'],
                'value': jsonutils.dumps(chassis)
            })
        return c_db

    def lswitch_db(self, c_db_in=None):
        """Return a DB representation of the logical switches."""
        if c_db_in:
            c_db = c_db_in
        else:
            c_db = []
        for lswitch_id in self.lswitches:
            c_db.append({
                'table': 'lswitch',
                'key': lswitch_id,
                'value': jsonutils.dumps(self.lswitches[lswitch_id])
            })
        return c_db

    def lrouter_db(self, c_db_in=None):
        """Return a DB representation of the logical router."""
        if c_db_in:
            c_db = c_db_in
        else:
            c_db = []
        if self.lrouter:
            c_db.append({
                'table': 'lrouter',
                'key': self.lrouter['id'],
                'value': jsonutils.dumps(self.lrouter)
            })
        return c_db

    def to_db(self):
        """Convert the message to a DB structure."""
        port_connect_db = self.port_db()

        # list of other ports
        for port in self.other_lports:
            port_connect_db.append({
                'table': 'lport',
                'key': port['id'],
                'value': jsonutils.dumps(port)
            })

        # security groups
        for sg in self.secgroup:
            port_connect_db.append({
                'table': 'secgroup',
                'key': sg['id'],
                'value': jsonutils.dumps(sg)
            })

        # logical switch
        self.lswitch_db(port_connect_db)

        # list of chassis
        self.chassis_db(port_connect_db)

        # logical router
        self.lrouter_db(port_connect_db)

        return port_connect_db

    def _lrouter_port(self, router_port, subnets):
        port = {}
        f_ips = router_port.get('fixed_ips', [])
        subnet_id = f_ips[0]['subnet_id']
        subnet = self._get_subnet(subnets, subnet_id)
        if subnet:
            cidr = netaddr.IPNetwork(subnet['cidr'])
            network = "%s/%s" % (router_port['fixed_ips'][0]['ip_address'],
                                 str(cidr.prefixlen))
            port['network'] = network
        port['topic'] = router_port['tenant_id']
        port['id'] = router_port['id']
        port['lswitch'] = router_port['network_id']
        port['mac'] = router_port['mac_address']
        port['unique_key'] = router_port['standard_attr_id']
        return port

    def _lrouter(self, router, router_ports, subnets):
        if not router:
            return None
        lrouter = {}
        lrouter['id'] = router['id']
        lrouter['topic'] = router['tenant_id']
        lrouter['name'] = router['name']
        lrouter['unique_key'] = router['standard_attr_id']
        lrouter['ports'] = (
            [self._lrouter_port(port, subnets) for port in router_ports]
        )
        lrouter['version'] = 1
        return lrouter
