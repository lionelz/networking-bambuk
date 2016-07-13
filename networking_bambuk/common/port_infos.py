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


from neutron import context as n_context
from neutron import manager
from neutron.extensions import allowedaddresspairs as addr_pair
from neutron.extensions import portsecurity as psec

from oslo_log import log

from oslo_serialization import jsonutils

LOG = log.getLogger(__name__)


class BambukPortInfo(object):

    def __init__(self, port, endpoints):
        self._plugin_property = None
        self._port = port
        self._endpoints = endpoints
        self._calculate_obj()

    @property
    def _plugin(self):
        if self._plugin_property is None:
            self._plugin_property = manager.NeutronManager.get_plugin()
        return self._plugin_property

    def _calculate_obj(self):
        ctx = n_context.get_admin_context()

        # lport
        self.lport = self._lport(self._port)

        # security groups
        self.secgroup = []
        if self.lport['security_groups']: 
            sgs = self._plugin.get_security_groups(
                ctx, {'id': self.lport['security_groups']})
            for sg in sgs:
                self.secgroup.append(self._secgroup(sg))

        # logical switch
        network = self._plugin.get_network(ctx, self._port['network_id'])
        subnets = self._plugin.get_subnets(
            ctx, filters={'network_id':[self._port['network_id']]})
        self.lswitch = self._lswitch(network, subnets)

        # list of chassis
        self.chassis = []
        print(self._endpoints)
        for entry in self._endpoints:
            for tunnel in entry['tunnels']:
                self.chassis.append({
                    'tunnel_type': entry['tunnel_type'],
                    'ip': tunnel['ip_address'],
                    'id': tunnel['host'],
                    'name': tunnel['host'],
                    'port': tunnel.get('udp_port'),
                })

    def to_db(self):
        port_connect_db = []
        port_connect_db.append({
            'table': 'lport',
            'key': self.lport['id'],
            'value': jsonutils.dumps(self.lport)
        })

        # security groups
        for sg in self.secgroup:
            port_connect_db.append({
                'table': 'secgroup',
                'key': sg['id'],
                'value': jsonutils.dumps(sg)
            })

        # logical switch
        port_connect_db.append({
            'table': 'lswitch',
            'key': self.lswitch['id'],
            'value': jsonutils.dumps(self.lswitch)
        })

        # list of chassis
        for chassis in self.chassis:
            port_connect_db.append({
                'table': 'chassis',
                'key': chassis['id'],
                'value': jsonutils.dumps(chassis)
            })

    def _lport(self, port):
        # TODO: calculate the tunnel_key
        tunnel_key = '1'
        ips = [ip['ip_address'] for ip in port.get('fixed_ips', [])]
        if port.get('device_owner') == "network:router_gateway":
            chassis = None
        else:
            chassis = port.get('binding:host_id', None)
        lport = {}
        lport['id'] = port['id']
        lport['lswitch_id'] = port['network_id']
        lport['macs'] =[port['mac_address']]
        lport['ips'] = ips
        lport['name'] = port.get('name', 'no_port_name')
        lport['enabled'] = port.get('admin_state_up', None)
        lport['chassis'] = chassis
        lport['tunnel_key'] = tunnel_key
        lport['device_owner'] = port.get('device_owner', None)
        lport['device_id'] = port.get('device_id', None)
        lport['security_groups'] = port.get('security_groups', None)
        lport['port_security_enabled'] = port.get(psec.PORTSECURITY, False)
        lport['allowed_address_pairs'] = port.get(addr_pair.ADDRESS_PAIRS, None)
        return lport

    def _secgroup(self, sg):
        secgroup = {}
        secgroup['id'] = sg['id']
        secgroup['name'] = sg.get('name', 'no_sg_name')
        secgroup['rules'] = sg['security_group_rules']
        return secgroup

    def _subnet(self, subnet):
        lsubnet = {}
        lsubnet['id'] = subnet['id']
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
        lswitch['name'] = network.get('name', 'no_network_name')
        lswitch['network_type'] = network.get('provider:network_type')
        lswitch['segmentation_id'] = network.get('provider:segmentation_id')
        lswitch['router_external'] = network['router:external']
        lswitch['mtu'] = network.get('mtu')
        lswitch['subnets'] = []
        LOG.debug(subnets)
        for subnet in subnets:
            lswitch['subnets'].append(self._subnet(subnet)) 
        return lswitch
