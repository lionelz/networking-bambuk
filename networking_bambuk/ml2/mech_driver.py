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

from neutron import manager
from neutron.api.v2 import attributes
from neutron.callbacks import events
from neutron.callbacks import registry
from neutron.callbacks import resources
from neutron.db.portbindings_base import PortBindingBaseMixin
from neutron.extensions import portbindings
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
