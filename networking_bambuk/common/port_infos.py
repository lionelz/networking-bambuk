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
from neutron import manager
from neutron.extensions import allowedaddresspairs as addr_pair
from neutron.extensions import portsecurity as psec

from oslo_log import log as o_log

from oslo_serialization import jsonutils

LOG = o_log.getLogger(__name__)


class BambukPortInfo(object):

    def __init__(self, port, other_ports, endpoints, router, router_ports):
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

    """ Creates a lswitch object for a given port
    """
    def _get_lswitch(self, ctx, port, subnets):
        network = self._plugin.get_network(ctx, port['network_id'])
        _subnets = self._plugin.get_subnets(
            ctx,
            filters={'network_id': [port['network_id']]})
        for subnet in _subnets:
            subnets[subnet['id']] = subnet
        return self._lswitch(network, _subnets), network

    """ Creates a lswitch object for the updated port
        This will also set the segmentation ID for our port
    """
    # TODO: As the segmentation ID code is commented out,
    #       can we remove this and use the _get_lswitch instead?
    def _get_port_lswitch(self, ctx, port, subnets):
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
        for port in self._router_ports:
            lswitch, _ = self._get_lswitch(ctx, port, subnets)
            if lswitch['id'] not in self.lswitches:
                self.lswitches[lswitch['id']] = lswitch

        # port
        if self._port:
            self.lport = self._lport(self._port)
        else:
            self.lport = None

        # router
        self.lrouter = self._lrouter(self._router, self._router_ports, subnets)

        # other ports
        self.other_lports = []
        for port in self._other_ports:
            self.other_lports.append(self._lport(port))

        # security groups
        self.secgroup = []
        if self.lport and self.lport['security_groups']:
            sgs = self._plugin.get_security_groups(
                ctx, {'id': self.lport['security_groups']})
            for sg in sgs:
                self.secgroup.append(self._secgroup(sg))

        # list of chassis
        self.chassis = []
        LOG.debug(self._endpoints)
        for entry in self._endpoints:
            for tunnel in entry['tunnels']:
                self.chassis.append({
                    'tunnel_type': entry['tunnel_type'],
                    'topic': None,
                    'ip': tunnel['ip_address'],
                    'id': tunnel['host'],
                    'name': tunnel['host'],
                    'port': tunnel.get('udp_port'),
                })

    def port_db(self, c_db_in=None):
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

    def to_db(self):
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
        port_connect_db.append({
            'table': 'lrouter',
            'key': self.lrouter['id'],
            'value': jsonutils.dumps(self.lrouter)
        })

        return port_connect_db

    def _lport(self, port):
        ips = [ip['ip_address'] for ip in port.get('fixed_ips', [])]
        if port.get('device_owner') == "network:router_gateway":
            chassis = None
        else:
            chassis = port.get('binding:host_id', None)
        lport = {}
        lport['id'] = port['id']
        lport['topic'] = None
        lport['lswitch'] = port['network_id']
        lport['macs'] = [port['mac_address']]
        lport['ips'] = ips
        lport['name'] = port.get('name', 'no_port_name')
        lport['enabled'] = port.get('admin_state_up', None)
        lport['chassis'] = chassis
        lport['tunnel_key'] = port['standard_attr_id']
#         if self.segmentation_id:
#             lport['tunnel_key'] = self.segmentation_id
#         else:
#             lport['tunnel_key'] = port['standard_attr_id']
        lport['device_owner'] = port.get('device_owner', None)
        lport['device_id'] = port.get('device_id', None)
        lport['security_groups'] = port.get('security_groups', None)
        lport['port_security_enabled'] = port.get(psec.PORTSECURITY, False)
        lport['allowed_address_pairs'] = (
            port.get(addr_pair.ADDRESS_PAIRS, None))
        return lport

    def _secgroup(self, sg):
        secgroup = {}
        secgroup['id'] = sg['id']
        secgroup['topic'] = None
        secgroup['name'] = sg.get('name', 'no_sg_name')
        secgroup['rules'] = sg['security_group_rules']
        return secgroup

    def _subnet(self, subnet):
        lsubnet = {}
        lsubnet['id'] = subnet['id']
        lsubnet['topic'] = None
        lsubnet['lswitch'] = subnet['network_id']
        lsubnet['name'] = subnet.get('name', 'no_subnet_name')
        lsubnet['enable_dhcp'] = subnet['enable_dhcp']
        lsubnet['cidr'] = subnet['cidr']
        lsubnet['dhcp_ip'] = subnet['allocation_pools'][0]['start']
        lsubnet['gateway_ip'] = subnet['gateway_ip']
        lsubnet['dns_nameservers'] = subnet.get('dns_nameservers', [])
        lsubnet['host_routes'] = subnet.get('host_routes', [])
        return lsubnet

    def _lswitch(self, network, subnets):
        lswitch = {}
        lswitch['id'] = network['id']
        lswitch['topic'] = None
        lswitch['name'] = network.get('name', 'no_network_name')
        lswitch['network_type'] = network.get('provider:network_type')
        lswitch['segmentation_id'] = network.get('provider:segmentation_id')
        lswitch['router_external'] = network['router:external']
        lswitch['mtu'] = network.get('mtu')
        lswitch['subnets'] = []
        LOG.debug(subnets)
        lswitch['subnets'] = [self._subnet(subnet) for subnet in subnets]
        return lswitch

    def _get_subnet(self, subnets, subnet_id):
        if subnet_id not in subnets:
            # Try to read the network if it is not in the cache
            ctx = n_context.get_admin_context()
            subnets[subnet_id] = self._plugin.get_subnet(ctx, subnet_id)
        return subnets[subnet_id]

    def _lrouter_port(self, router_port, subnets):
        port = self._lport(router_port)
        port['mac'] = port['macs'][0]
        f_ips = router_port.get('fixed_ips', [])
        subnet_id = f_ips[0]['subnet_id']
        subnet = self._get_subnet(subnets, subnet_id)
        if subnet:
            cidr = netaddr.IPNetwork(subnet['cidr'])
            network = "%s/%s" % (router_port['fixed_ips'][0]['ip_address'],
                                 str(cidr.prefixlen))
            port['network'] = network
        port['topic'] = router_port['tenant_id']
        del port['macs']
        del port['ips']
        return port

    def _lrouter(self, router, router_ports, subnets):
        if not router:
            return None
        lrouter = {}
        lrouter['id'] = router['id']
        lrouter['topic'] = router['tenant_id']
        lrouter['name'] = router['name']
        lrouter['ports'] = \
            [self._lrouter_port(port, subnets) for port in router_ports]
        return lrouter
