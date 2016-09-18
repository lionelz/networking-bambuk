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

from neutron.db import securitygroups_db
from neutron.db.portbindings_base import PortBindingBaseMixin
from neutron.callbacks import events
from neutron.callbacks import registry
from neutron.callbacks import resources
from neutron.extensions import portbindings
from neutron.plugins.ml2 import driver_api

from oslo_log import log

from networking_bambuk.db.bambuk import create_update_log
from networking_bambuk.db.bambuk import bambuk_db
from networking_bambuk.ml2 import bambuk_l2pop


LOG = log.getLogger(__name__)


class BambukMechanismDriver(driver_api.MechanismDriver, PortBindingBaseMixin):
    """Bambuk ML2 mechanism driver
    """

    def initialize(self):
        LOG.info(_LI("Starting BambukMechanismDriver"))

        self.supported_vnic_types = [portbindings.VNIC_NORMAL]
        self.vif_type = portbindings.VIF_TYPE_OVS,
        self.vif_details = {
            portbindings.CAP_PORT_FILTER: True,
            portbindings.OVS_HYBRID_PLUG: True
        }

        # Handle security group/rule notifications
        registry.subscribe(self.create_security_group_rule,
                           resources.SECURITY_GROUP_RULE,
                           events.PRECOMMIT_CREATE)
        registry.subscribe(self.after_create_security_group_rule,
                           resources.SECURITY_GROUP_RULE,
                           events.AFTER_CREATE)
        registry.subscribe(self.delete_security_group_rule,
                           resources.SECURITY_GROUP_RULE,
                           events.BEFORE_DELETE)
        registry.subscribe(self.after_delete_security_group_rule,
                           resources.SECURITY_GROUP_RULE,
                           events.AFTER_DELETE)
        self.bambuk_l2pop = bambuk_l2pop.BambukL2Pop()

    def _get_sg(self, ctx, sg_rule_id):
        with ctx.session.begin(subtransactions=True):
            # retrieve the SG
            sgr_sg_id = securitygroups_db.SecurityGroupRule.security_group_id
            sgr_id = securitygroups_db.SecurityGroupRule.id
            query = ctx.session.query(securitygroups_db.SecurityGroup)
            query = query.join(securitygroups_db.SecurityGroupRule,
                               sgr_sg_id == securitygroups_db.SecurityGroup.id)
            query = query.filter(sgr_id == sg_rule_id)
            return query.one()

    def create_security_group_rule(self, resource, event, trigger, **kwargs):
        sg_rule_id = kwargs['security_group_rule_id']
        context = kwargs['context']
        sg = self._get_sg(context, sg_rule_id)
        create_update_log.create_bambuk_update_log(
            context,
            sg,
            bambuk_db.OBJ_TYPE_SECURITY_GROUP,
            bambuk_db.ACTION_UPDATE,
        )

    def after_create_security_group_rule(self,
                                         resource,
                                         event,
                                         trigger,
                                         **kwargs):
        create_update_log.awake()

    def delete_security_group_rule(self, resource, event, trigger, **kwargs):
        sg_rule_id = kwargs['security_group_rule_id']
        context = kwargs['context']
        sg = self._get_sg(context, sg_rule_id)
        create_update_log.create_bambuk_update_log(
            context,
            sg,
            bambuk_db.OBJ_TYPE_SECURITY_GROUP,
            bambuk_db.ACTION_UPDATE,
        )

    def after_delete_security_group_rule(self,
                                         resource,
                                         event,
                                         trigger,
                                         **kwargs):
        create_update_log.awake()

    def create_port_precommit(self, context):
        port = context.current
        binding_profile = port['binding:profile']
        if 'provider_mgnt_ip' not in binding_profile:
            return

        create_update_log.create_bambuk_update_log(
            context._plugin_context,
            port,
            bambuk_db.OBJ_TYPE_PORT,
            bambuk_db.ACTION_UPDATE,
        )

    def create_port_postcommit(self, context):
        create_update_log.awake()

    def update_port_precommit(self, context):
        port = context.current
        binding_profile = port['binding:profile']
        if 'provider_mgnt_ip' not in binding_profile:
            return

        create_update_log.create_bambuk_update_log(
            context._plugin_context,
            port,
            bambuk_db.OBJ_TYPE_PORT,
            bambuk_db.ACTION_UPDATE,
        )

    def update_port_postcommit(self, context):
        create_update_log.awake()

    def delete_port_precommit(self, context):
        create_update_log.create_bambuk_update_log(
            context._plugin_context,
            context.current,
            bambuk_db.OBJ_TYPE_PORT,
            bambuk_db.ACTION_DELETE,
        )

    def delete_port_postcommit(self, context):
        create_update_log.awake()

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
