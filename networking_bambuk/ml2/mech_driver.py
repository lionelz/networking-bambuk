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

from neutron import manager
from neutron.api.v2 import attributes
from neutron.callbacks import events
from neutron.callbacks import registry
from neutron.callbacks import resources
from neutron.plugins.ml2 import driver_api
from neutron.services.qos import qos_consts

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

    supported_qos_rule_types = [qos_consts.RULE_TYPE_BANDWIDTH_LIMIT]

    def initialize(self):
        """Perform driver initialization.

        Called after all drivers have been loaded and the database has
        been initialized. No abstract methods defined below will be
        called prior to this method being called.
        """
        LOG.info(_LI("Starting BambukMechanismDriver"))

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

    def process_create_network(self, plugin_context, data, result):
        """Process extended attributes for create network.

        :param plugin_context: plugin request context
        :param data: dictionary of incoming network data
        :param result: network dictionary to extend

        Called inside transaction context on plugin_context.session to
        validate and persist any extended network attributes defined by this
        driver. Extended attribute values must also be added to
        result.
        """
        pass

    def process_create_subnet(self, plugin_context, data, result):
        """Process extended attributes for create subnet.

        :param plugin_context: plugin request context
        :param data: dictionary of incoming subnet data
        :param result: subnet dictionary to extend

        Called inside transaction context on plugin_context.session to
        validate and persist any extended subnet attributes defined by this
        driver. Extended attribute values must also be added to
        result.
        """
        pass

    def process_create_port(self, plugin_context, data, result):
        """Process extended attributes for create port.

        :param plugin_context: plugin request context
        :param data: dictionary of incoming port data
        :param result: port dictionary to extend

        Called inside transaction context on plugin_context.session to
        validate and persist any extended port attributes defined by this
        driver. Extended attribute values must also be added to
        result.
        """
        pass

    def process_update_network(self, plugin_context, data, result):
        """Process extended attributes for update network.

        :param plugin_context: plugin request context
        :param data: dictionary of incoming network data
        :param result: network dictionary to extend

        Called inside transaction context on plugin_context.session to
        validate and update any extended network attributes defined by this
        driver. Extended attribute values, whether updated or not,
        must also be added to result.
        """
        pass

    def process_update_subnet(self, plugin_context, data, result):
        """Process extended attributes for update subnet.

        :param plugin_context: plugin request context
        :param data: dictionary of incoming subnet data
        :param result: subnet dictionary to extend

        Called inside transaction context on plugin_context.session to
        validate and update any extended subnet attributes defined by this
        driver. Extended attribute values, whether updated or not,
        must also be added to result.
        """
        pass

    def process_update_port(self, plugin_context, data, result):
        """Process extended attributes for update port.

        :param plugin_context: plugin request context
        :param data: dictionary of incoming port data
        :param result: port dictionary to extend

        Called inside transaction context on plugin_context.session to
        validate and update any extended port attributes defined by this
        driver. Extended attribute values, whether updated or not,
        must also be added to result.
        """
        pass

    def extend_network_dict(self, session, base_model, result):
        """Add extended attributes to network dictionary.

        :param session: database session
        :param base_model: network model data
        :param result: network dictionary to extend

        Called inside transaction context on session to add any
        extended attributes defined by this driver to a network
        dictionary to be used for mechanism driver calls and/or
        returned as the result of a network operation.
        """
        pass

    def extend_subnet_dict(self, session, base_model, result):
        """Add extended attributes to subnet dictionary.

        :param session: database session
        :param base_model: subnet model data
        :param result: subnet dictionary to extend

        Called inside transaction context on session to add any
        extended attributes defined by this driver to a subnet
        dictionary to be used for mechanism driver calls and/or
        returned as the result of a subnet operation.
        """
        pass

    def extend_port_dict(self, session, base_model, result):
        """Add extended attributes to port dictionary.

        :param session: database session
        :param base_model: port model data
        :param result: port dictionary to extend

        Called inside transaction context on session to add any
        extended attributes defined by this driver to a port
        dictionary to be used for mechanism driver calls
        and/or returned as the result of a port operation.
        """
        pass
