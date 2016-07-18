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
from networking_bambuk.common import config
from networking_bambuk.common import port_infos
from networking_bambuk.rpc.bambuk_rpc import BambukAgentClient

from neutron import context as n_context
from neutron import manager
from neutron.api.v2 import attributes
from neutron.callbacks import events
from neutron.callbacks import registry
from neutron.callbacks import resources
from neutron.common import topics
from neutron.db.portbindings_base import PortBindingBaseMixin
from neutron.extensions import portbindings
from neutron.plugins.ml2 import driver_api
from neutron.plugins.ml2 import managers
from neutron.plugins.ml2 import rpc

from oslo_log import log

from oslo_serialization import jsonutils


LOG = log.getLogger(__name__)


class BambukMechanismDriver(driver_api.MechanismDriver, PortBindingBaseMixin):
    """Bambuk ML2 mechanism driver
    """
    
    def initialize(self):
        LOG.info(_LI("Starting BambukMechanismDriver"))
        self._bambuk_client = BambukAgentClient()
        self._plugin_property = None
                            
        self.supported_vnic_types = [portbindings.VNIC_NORMAL]
        self.vif_type = portbindings.VIF_TYPE_OVS,
        self.vif_details = {
            portbindings.CAP_PORT_FILTER: True,
            portbindings.OVS_HYBRID_PLUG: True
        }

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

        self.notifier = rpc.AgentNotifierApi(topics.AGENT)
        self.type_manager = managers.TypeManager()
        self.rpc_tunnel = rpc.RpcCallbacks(self.notifier, self.type_manager)

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
        if 'provider_mgnt_ip' not in binding_profile:
            return

        host_id = port['binding:host_id']
        provider_mgnt_ip = binding_profile['provider_mgnt_ip']
        if 'provider_data_ip' in binding_profile:
            provider_data_ip = binding_profile['provider_data_ip']
        else:
            provider_data_ip = provider_mgnt_ip
        server_conf = {
            'device_id': host_id,
            'local_ip': provider_data_ip
        }

        # get agent state
        agent_state =  self._bambuk_client.state(server_conf, provider_mgnt_ip)
        if not agent_state:
            return

        ctx = n_context.get_admin_context()
        # create or update the agent
        agent = self._plugin.create_or_update_agent(
            ctx, agent_state)
        LOG.debug(agent)
        agents = self._plugin.get_agents(
            ctx,
            filters={
                'agent_type': [agent_state['agent_type']],
                'host': [host_id]
            }
        )
        LOG.debug(agents)
        if not agents or len(agents) == 0:
            return
        if not config.get_l2_population():
            endpoints = []

            for tunnel_type in agent_state['configurations']['tunnel_types']:
                entry = self.rpc_tunnel.tunnel_sync(
                    ctx,
                    tunnel_ip=provider_data_ip,
                    tunnel_type=tunnel_type,
                    host=host_id
                )
                entry['tunnel_type'] = tunnel_type
                endpoints.append(entry)
            port_info = port_infos.BambukPortInfo(port, endpoints)
        self._bambuk_client.apply(port_info.to_db(), provider_mgnt_ip)

    def create_port_postcommit(self, context):
        port = context.current
        self._apply_port(context, port)

    def update_port_postcommit(self, context):
        port = context.current
        self._apply_port(context, port)

    def bind_port(self, context):
        port = context.current
        vnic_type = port.get(portbindings.VNIC_TYPE, portbindings.VNIC_NORMAL)
        if vnic_type not in self.supported_vnic_types:
            LOG.debug("Refusing to bind due to unsupported vnic_type: %s",
                      vnic_type)
            return
        for segment_to_bind in context.segments_to_bind:
            context.set_binding(segment_to_bind[driver_api.ID],
                                self.vif_type,
                                self.vif_details,
                                'ACTIVE')
