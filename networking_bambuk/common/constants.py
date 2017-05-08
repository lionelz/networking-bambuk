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

import six
import time

from neutron.extensions import portbindings

from oslo_log import log as o_log


LOG = o_log.getLogger(__name__)


BAMBUK_PORT_BINDING_PROFILE = portbindings.PROFILE
BAMBUK_PORT_BINDING_PROFILE_PARAMS = [{'provider_ip': six.string_types}]

ML2_SUPPORTED_API_EXTENSIONS_BAMBUK_L3 = [
    "dvr", "router", "ext-gw-mode",
    "extraroute", "l3_agent_scheduler",
    "l3-ha", "router_availability_zone",
    "dns-integration",
]

def timefunc(method):

    def timed(*args, **kw):
        ts = time.time()
        result = method(*args, **kw)
        te = time.time()

        LOG.info('%r %2.2f seconds' % (method.__name__, te-ts))
        return result

    return timed
