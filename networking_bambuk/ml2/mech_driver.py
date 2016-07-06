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

from networking_bambuk._i18n import _LI
from networking_bambuk.rpc.bambuk_rpc import BambukAgentClient

from neutron import context as n_context
from neutron import manager
from neutron.api.v2 import attributes
from neutron.callbacks import events
from neutron.callbacks import registry
from neutron.callbacks import resources
from neutron.db import api as db_api
from neutron.db.portbindings_base import PortBindingBaseMixin
from neutron.extensions import allowedaddresspairs as addr_pair
from neutron.extensions import portsecurity as psec
from neutron.plugins.ml2.driver_api import MechanismDriver

from oslo_log import log

from oslo_serialization import jsonutils


LOG = log.getLogger(__name__)


class BambukMechanismDriver(MechanismDriver, PortBindingBaseMixin):
    """Bambuk ML2 mechanism driver
    """
    
    def initialize(self):
        LOG.info(_LI("Starting BambukMechanismDriver"))
        self._bambuk_client = BambukAgentClient()
        self._plugin_property = None
                            
        # Handle security group/rule notifications
        registry.subscribe(self.create_security_group,
                           resources.SECURITY_GROUP,
                           events.AFTER_CREATE)
        registry.subscribe(self.delete_security_group,
                           resources.SECURITY_GROUP,
                           events.BEFORE_DELETE)
        registry.subscribe(self.create_security_group_rule,
                           resources.SECURITY_GROUP_RULE,
                           events.AFTER_CREATE)
        registry.subscribe(self.delete_security_group_rule,
                           resources.SECURITY_GROUP_RULE,
                           events.BEFORE_DELETE)

    @property
    def _plugin(self):
        if self._plugin_property is None:
            self._plugin_property = manager.NeutronManager.get_plugin()
        return self._plugin_property

    def _get_attribute(self, obj, attribute):
        res = obj.get(attribute)
        if res is attributes.ATTR_NOT_SPECIFIED:
            res = None
        return res

    def _update(self, table, key, value, vms):
        self._bambuk_client.update({
            'table': table,
            'key': key,
            'value': value,
        }, vms)

    def _delete(self, table, key):
        self._bambuk_client.delete({
            'table': table,
            'key': key
        })

    def create_security_group(self, resource, event, trigger, **kwargs):
        sg = kwargs['security_group']
        sg_id = sg['id']
        if not 'name' in sg:
            sg['name'] = 'no_sg_name'
        rules = sg.get('security_group_rules')
        for rule in rules:
            del rule['tenant_id']

        sg_json = jsonutils.dumps(sg)

        self._update('secgroup', sg_id, sg_json)

    def delete_security_group(self, resource, event, trigger, **kwargs):
        sg_id = kwargs['security_group_id']
        self._delete('secgroup', sg_id)

    def create_security_group_rule(self, resource, event, trigger, **kwargs):
        sg_rule = kwargs['security_group_rule']
        sg_id = sg_rule['security_group_id']
        # TODO: read the sg from the Db and update sg or create table secgrouprule

    def delete_security_group_rule(self, resource, event, trigger, **kwargs):
        sg_rule = kwargs['security_group_rule']
        sg_id = sg_rule['security_group_id']
        # TODO: read the sg from the Db and update sg or create table secgrouprule

    def _apply_port(self, context, port):
        binding_profile = port['binding:profile']
        device_id = port['device_id']
        provider_mgnt_ip = binding_profile['provider_mgnt_ip']
        if 'provider_data_ip' in binding_profile:
            provider_data_ip = binding_profile['provider_data_ip']
        else:
            provider_data_ip = provider_mgnt_ip
        server_conf = {
            'device_id': device_id,
            'local_ip': provider_data_ip
        }

        # get agent state
        agent_state =  self._bambuk_client.state(server_conf, provider_mgnt_ip)
        if not agent_state:
            return

        # create or update the agent
        agent = self._plugin.create_or_update_agent(
            n_context.get_admin_context_without_session(), agent_state)
        LOG.debug(agent)
        agents = self._plugin.get_agents(
            context,
            filters={
                'agent_type': agent_state['agent_type'],
                'host': device_id
            }
        )
        if not agents:
            return

        # lport
        # TODO: calculate the tunnel_key
        tunnel_key = '1'
        ips = [ip['ip_address'] for ip in port.get('fixed_ips', [])]
        if port.get('device_owner') == "network:router_gateway":
            chassis = None
        else:
            chassis = port.get('binding:host_id', None)
        lport = {}
        lport['id'] = port['id']
        lport['lswitch'] = port['network_id']
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
        lport_json = jsonutils.dumps(lport)

        # TODO: security groups
        sg_info = self._plugin.security_group_info_for_ports(
            context, {port['id']: port})
        LOG.debug(sg_info)

        # TODO: list of endpoints

        self._bambuk_client.apply(
            [{'table': 'lport', 'key': port['id'], 'value': lport_json}],
            provider_mgnt_ip)

    def create_port_precommit(self, context):
        port = context.current
        binding_profile = port['binding:profile']
        if 'provider_mgnt_ip' in binding_profile:
            self._apply_port(context, port)

    def update_port_precommit(self, context):
        port = context.current
        binding_profile = port['binding:profile']
        if 'provider_mgnt_ip' in binding_profile:
            self._apply_port(context, port)
