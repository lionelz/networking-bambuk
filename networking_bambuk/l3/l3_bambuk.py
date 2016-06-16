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

from neutron.common import utils as n_utils
from neutron import manager
from neutron.plugins.common import constants as n_constants
from neutron.services.l3_router import l3_router_plugin

from networking_bambuk._i18n import _LE, _LI
from networking_bambuk.common import constants


LOG = log.getLogger(__name__)

class BambukL3RouterPlugin(l3_router_plugin.L3RouterPlugin):
    """Implementation of the Bambuk L3 Router Service Plugin.

    This class implements a L3 service plugin that provides
    router and floatingip resources and manages associated
    request/response.
    """
    supported_extension_aliases = \
        constants.ML2_SUPPORTED_API_EXTENSIONS_BAMBUK_L3

    def __init__(self):
        LOG.info(_LI("Starting BambukL3RouterPlugin"))
        super(BambukL3RouterPlugin, self).__init__()
        self._plugin_property = None


    @property
    def _plugin(self):
        if self._plugin_property is None:
            self._plugin_property = manager.NeutronManager.get_plugin()
        return self._plugin_property

    def get_plugin_type(self):
        return n_constants.L3_ROUTER_NAT

    def get_plugin_description(self):
        """returns string description of the plugin."""
        return ("L3 Router Service Plugin for L3 forwarding (hybrid-Cloud)")

    def create_router(self, context, router):
        router = super(BambukL3RouterPlugin, self).create_router(
            context, router)
        #TODO: implement it
        return router


    def update_router(self, context, router_id, router):
        original_router = self.get_router(context, router_id)
        result = super(BambukL3RouterPlugin, self).update_router(
            context, router_id, router)

        #TODO: implement it
        update = {}
        added = []
        removed = []
        if 'admin_state_up' in router['router']:
            enabled = router['router']['admin_state_up']
            if enabled != original_router['admin_state_up']:
                update['enabled'] = enabled

        """ Update static routes """
        if 'routes' in router['router']:
            routes = router['router']['routes']
            added, removed = n_utils.diff_list_of_dict(
                original_router['routes'], routes)

        if update or added or removed:
            try:
                pass
            except Exception as ex:
                LOG.exception(_LE('Unable to update router for %s'), id)
                # roll-back
                super(BambukL3RouterPlugin, self).update_router(context,
                                                             id,
                                                             original_router)
                raise ex

        return result

    def delete_router(self, context, router_id):
        ret_val = super(BambukL3RouterPlugin, self).delete_router(
            context, router_id)
        #TODO: implement it
        return ret_val


    def add_router_interface(self, context, router_id, interface_info):
        router_interface_info = \
            super(BambukL3RouterPlugin, self).add_router_interface(
                context, router_id, interface_info)
        #TODO: implement it
        return router_interface_info

    def remove_router_interface(self, context, router_id, interface_info):
        router_interface_info = \
            super(BambukL3RouterPlugin, self).remove_router_interface(
                context, router_id, interface_info)
        #TODO: implement it
        return router_interface_info
