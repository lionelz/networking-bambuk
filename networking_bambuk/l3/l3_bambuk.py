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

from oslo_log import log as o_log

from neutron import manager
from neutron.plugins.common import constants as n_constants
from neutron.services.l3_router import l3_router_plugin

from networking_bambuk._i18n import _LE, _LI
from networking_bambuk.common import constants

from networking_bambuk.db.bambuk import bambuk_db
from networking_bambuk.db.bambuk import create_update_log


LOG = o_log.getLogger(__name__)


class BambukL3RouterPlugin(l3_router_plugin.L3RouterPlugin):
    """Implementation of the Bambuk L3 Router Service Plugin.

    This class implements a L3 service plugin that provides
    router and floating IP resources and manages associated
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

    def update_router(self, context, router_id, router):
        original_router = self.get_router(context, router_id)
        with context.session.begin(subtransactions=True):
            result = super(BambukL3RouterPlugin, self).update_router(
                context, router_id, router)

            update = {}
            if 'admin_state_up' in router['router']:
                enabled = router['router']['admin_state_up']
                if enabled != original_router['admin_state_up']:
                    update['enabled'] = enabled
            if update:
                try:
                    create_update_log.create_bambuk_update_log(
                        context,
                        result,
                        bambuk_db.OBJ_TYPE_ROUTER,
                        bambuk_db.ACTION_UPDATE
                    )
                except Exception as ex:
                    LOG.exception(_LE('Unable to update router for %s'), id)
                    raise ex
        create_update_log.awake()
        return result

    def add_router_interface(self, context, router_id, interface_info):
        with context.session.begin(subtransactions=True):
            router_interface_info = \
                super(BambukL3RouterPlugin, self).add_router_interface(
                    context, router_id, interface_info)

            create_update_log.create_bambuk_update_log(
                context,
                router_interface_info,
                bambuk_db.OBJ_TYPE_ROUTER_IFACE,
                bambuk_db.ACTION_ATTACH,
            )
        create_update_log.awake()
        return router_interface_info

    def remove_router_interface(self, context, router_id, interface_info):
        with context.session.begin(subtransactions=True):
            router_interface_info = (
                super(BambukL3RouterPlugin, self).remove_router_interface(
                    context, router_id, interface_info))

            network_id = router_interface_info['network_id']
            LOG.debug("Removing router interface  %s", router_interface_info)
            create_update_log.create_bambuk_update_log(
                context,
                router_interface_info,
                bambuk_db.OBJ_TYPE_ROUTER_IFACE,
                bambuk_db.ACTION_DETACH,
                network_id
            )
        create_update_log.awake()
        return router_interface_info
