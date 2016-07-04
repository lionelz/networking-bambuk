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

from dragonflow.neutron.common import constants as df_const

from networking_bambuk._i18n import _LI
from networking_bambuk.rpc.bambuk_rpc import BambukAgentClient

from neutron import context as n_context
from neutron import manager
from neutron.api.v2 import attributes
from neutron.callbacks import events
from neutron.callbacks import registry
from neutron.callbacks import resources
from neutron.plugins.ml2 import driver_api

from oslo_log import log

from oslo_serialization import jsonutils


LOG = log.getLogger(__name__)


class BambukMechanismDriver(driver_api.MechanismDriver):
    """Bambuk ML2 mechanism driver
    """

    def initialize(self):
        LOG.info(_LI("Starting BambukMechanismDriver"))
        self._bambuk_client = BambukAgentClient()

        registry.subscribe(self.post_fork_initialize,
                           resources.PROCESS,
                           events.AFTER_CREATE)

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

    def update_network_postcommit(self, context):
        port = context.current
        original_port = context.original
        LOG.info("port %s" % port)
        LOG.info("original_port %s" % original_port)
        # check if profile
        if 'binding:host_id' in port and 'binding:profile' in port:
            #create or update agent
            host_id = port['binding:host_id']
            profile = port['binding:profile']
            server_ip = ''
            provider_mgnt_ip = profile['provider_mgnt_ip']
            provider_data_ip = profile['provider_data_ip']
            state = self._bambuk_client.state(
                {
                    'host': host_id,
                    'server_ip': server_ip,
                    'provider_mgnt_ip': provider_mgnt_ip,
                    'provider_data_ip': provider_data_ip
                },
                provider_mgnt_ip)
            agent_status = self.plugin.create_or_update_agent(
                context, state)


    def _update(self, table, key, value):
        self._bambuk_client.update({
            'table': table,
            'key': key,
            'value': value,
        })

    def _delete(self, table, key):
        self._bambuk_client.delete({
            'table': table,
            'key': key
        })

    def create_security_group(self, resource, event, trigger, **kwargs):
        sg = kwargs['security_group']
        sg_id = sg['id']
        if not 'name' in sg:
            sg['name'] = df_const.DF_SG_DEFAULT_NAME
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
