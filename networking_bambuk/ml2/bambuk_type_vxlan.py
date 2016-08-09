# Copyright (c) 2013 OpenStack Foundation
# All Rights Reserved.
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

from oslo_config import cfg
from oslo_log import log
import sqlalchemy as sa

from neutron.common import exceptions as n_exc
from neutron.db import model_base
from neutron.db import api as db_api
from neutron.plugins.common import constants as p_const
from neutron.plugins.ml2.drivers import type_tunnel
from neutron.plugins.ml2.drivers import type_vxlan

from networking_bambuk._i18n import _LE

LOG = log.getLogger(__name__)


class BambukVxlanEndpoints(model_base.BASEV2):
    """Represents tunnel endpoint in RPC mode."""

    __tablename__ = 'ml2_vxlan_endpoints'
    __table_args__ = {'extend_existing': True}
    zone = sa.Column(sa.String(length=50), nullable=True)

    def __repr__(self):
        return "<VxlanTunnelEndpoint(%s)>" % self.ip_address


class BambukVxlanTypeDriver(type_tunnel.EndpointTunnelTypeDriver):

    def __init__(self):
        super(BambukVxlanTypeDriver, self).__init__(
            type_vxlan.VxlanAllocation, BambukVxlanEndpoints)

    def get_type(self):
        return 'bambuk_vxlan'

    def initialize(self):
        try:
            self._initialize(cfg.CONF.ml2_type_vxlan.vni_ranges)
        except n_exc.NetworkTunnelRangeError:
            LOG.exception(_LE("Failed to parse vni_ranges. "
                              "Service terminated!"))
            raise SystemExit()

    def _get_endpoints(self, zone):
        LOG.debug("_get_endpoints() called")
        session = db_api.get_session()
        query = session.query(self.endpoint_model)
        query = query.filter(BambukVxlanEndpoints.zone == zone)
        return query

    def get_endpoints(self, zone=None):
        """Get every vxlan endpoints from database."""
        vxlan_endpoints = self._get_endpoints(zone)
        return [{'ip_address': vxlan_endpoint.ip_address,
                 'udp_port': vxlan_endpoint.udp_port,
                 'host': vxlan_endpoint.host}
                for vxlan_endpoint in vxlan_endpoints]

    def add_endpoint(self, ip, host,
                     udp_port=p_const.VXLAN_UDP_PORT,
                     zone='hypervm'):
        return self._add_endpoint(ip, host, udp_port=udp_port, zone=zone)

    def get_mtu(self, physical_network=None):
        mtu = super(BambukVxlanTypeDriver, self).get_mtu()
        return mtu - p_const.VXLAN_ENCAP_OVERHEAD if mtu else 0
