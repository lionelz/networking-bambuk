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

from oslo_log import log

from neutron import context as n_context
from neutron import manager
from neutron.api.v2 import attributes
from neutron.callbacks import events
from neutron.callbacks import registry
from neutron.callbacks import resources
from neutron.plugins.ml2 import driver_api

from networking_bambuk._i18n import _LI


LOG = log.getLogger(__name__)



class BambukMechanismDriver(driver_api.MechanismDriver):
    """Bambuk ML2 mechanism driver

    A mechanism driver is called on the creation, update, and deletion
    of networks and ports. For every event, there are two methods that
    get called - one within the database transaction (method suffix of
    _precommit), one right afterwards (method suffix of _postcommit).

    Exceptions raised by methods called inside the transaction can
    rollback, but should not make any blocking calls (for example,
    REST requests to an outside controller). Methods called after
    transaction commits can make blocking external calls, though these
    will block the entire process. Exceptions raised in calls after
    the transaction commits may cause the associated resource to be
    deleted.

    Because rollback outside of the transaction is not done in the
    update network/port case, all data validation must be done within
    methods that are part of the database transaction.
    """

    def initialize(self):
        LOG.info(_LI("Starting BambukMechanismDriver"))
        self.subscribe()

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

    def subscribe(self):
        registry.subscribe(self.post_fork_initialize,
                           resources.PROCESS,
                           events.AFTER_CREATE)

        # Handle security group/rule notifications
        registry.subscribe(self._process_sg_notification,
                           resources.SECURITY_GROUP,
                           events.AFTER_UPDATE)
        registry.subscribe(self._process_sg_notification,
                           resources.SECURITY_GROUP_RULE,
                           events.AFTER_CREATE)
        registry.subscribe(self._process_sg_notification,
                           resources.SECURITY_GROUP_RULE,
                           events.BEFORE_DELETE)

    def post_fork_initialize(self, resource, event, trigger, **kwargs):
        LOG.info(_LI("post_fork_initialize BambukMechanismDriver"))

    def _process_sg_notification(self, resource, event, trigger, **kwargs):
        sg_id = None
        sg_rule = None
        is_add_acl = True

        admin_context = n_context.get_admin_context()
        if resource == resources.SECURITY_GROUP:
            sg_id = kwargs.get('security_group_id')
        elif resource == resources.SECURITY_GROUP_RULE:
            if event == events.AFTER_CREATE:
                sg_rule = kwargs.get('security_group_rule')
                sg_id = sg_rule['security_group_id']
            elif event == events.BEFORE_DELETE:
                sg_rule = self._plugin.get_security_group_rule(
                    admin_context, kwargs.get('security_group_rule_id'))
                sg_id = sg_rule['security_group_id']
                is_add_acl = False



    def update_port_precommit(self, context):
        port = context.current
        original_port = context.original
        # check if profile
        if 'binding:host_id' in port:
            #create or update agent
            
            # TODO: call the agent to receive the state
            agent_state = {
                'binary': 'neutron-openvswitch-agent',
                'host': port['binding:host_id'],
                'configurations': {
                    'bridge_mappings': '',
                    'tunnel_types': self.tunnel_types,
                    'tunneling_ip': self.local_ip,
# 'l2_population': True,
# 'arp_responder_enabled': True,
# 'enable_distributed_routing': True,
# 'vhostuser_socket_dir': ovs_conf.vhostuser_socket_dir},
                    'resource_versions': resources.LOCAL_RESOURCE_VERSIONS,
                    'agent_type': agent_conf.agent_type,
                    'start_flag': True
                }
            }
            agent_status = self.plugin.create_or_update_agent(
                context, agent_state)

