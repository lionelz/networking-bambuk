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
from neutron.db import db_base_plugin_v2
from neutron.db.portbindings_base import PortBindingBaseMixin
from neutron.callbacks import events
from neutron.callbacks import registry
from neutron.callbacks import resources
from neutron.common import topics
from neutron.extensions import portbindings
from neutron.plugins.ml2 import driver_api
from neutron.plugins.ml2 import managers
from neutron.plugins.ml2 import rpc

from oslo_log import log

from oslo_serialization import jsonutils
from networking_bambuk.ml2 import bambuk_db


LOG = log.getLogger(__name__)


def _extend_port_dict_standard_attr_id(res, port):
    res['standard_attr_id'] = port['standard_attr_id']
    return res


class BambukMechanismDriver(driver_api.MechanismDriver, PortBindingBaseMixin):
    """Bambuk ML2 mechanism driver
    """
    
    def initialize(self):
        LOG.info(_LI("Starting BambukMechanismDriver"))
        # Register dict extend port attributes
        db_base_plugin_v2.NeutronDbPluginV2.register_dict_extend_funcs(
            attributes.PORTS, ['_extend_port_dict_standard_attr_id'])
        self._bambuk_client = BambukAgentClient()
        self._plugin_property = None
                            
        self.supported_vnic_types = [portbindings.VNIC_NORMAL]
        self.vif_type = portbindings.VIF_TYPE_OVS,
        self.vif_details = {
            portbindings.CAP_PORT_FILTER: True,
            portbindings.OVS_HYBRID_PLUG: True
        }

        # Handle security group/rule notifications
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
            self._plugin_property._extend_port_dict_standard_attr_id = (
                _extend_port_dict_standard_attr_id)
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


    def _get_vms(self, ports, exclude_ids=None):
        vms = set()
        for port in ports:
            if exclude_ids and port['id'] in exclude_ids:
                continue 
            binding_profile = port['binding:profile']
            if 'provider_mgnt_ip' in binding_profile:
                vms.add(binding_profile['provider_mgnt_ip'])
        return vms

    def _update_sg(self, sg_id):
        # get all the ports connected to the sg
        ctx = n_context.get_admin_context()
        ports = bambuk_db.get_ports_by_secgroup(ctx, sg_id)
        sg = self._plugin.get_security_group(ctx, sg_id)
        vms = self._get_vms(ports)
            
        self._bambuk_client.update(
            {
                'table': 'secgroup',
                'key': self.secgroup['id'],
                'value': jsonutils.dumps(sg)
            }, vms)

    def create_security_group_rule(self, resource, event, trigger, **kwargs):
        sg_rule = kwargs['security_group_rule']
        sg_id = sg_rule['security_group_id']
        self._update_sg(sg_id)

    def delete_security_group_rule(self, resource, event, trigger, **kwargs):
        sg_rule = kwargs['security_group_rule']
        sg_id = sg_rule['security_group_id']
        self._update_sg(sg_id)

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

        if config.get_l2_population():
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

        #the other port of the network
        other_ports = self._plugin.get_ports(
            ctx,
            filters={'network_id': [port['network_id']]}
        )
        LOG.debug(port['network_id'])
        LOG.debug(other_ports)
        for op in other_ports:
            if port['id'] == op['id']:
                port_db = op

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
        port_info = port_infos.BambukPortInfo(port_db, other_ports, endpoints)

        self._bambuk_client.apply(port_info.to_db(), provider_mgnt_ip)

        # update all other ports for the maybe new endpoint
        vms = self._get_vms(other_ports, [port['id']])
        update_connect_db = port_info.chassis_db()
        port_info.port_db(update_connect_db)
        self._bambuk_client.update(update_connect_db, vms)

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
