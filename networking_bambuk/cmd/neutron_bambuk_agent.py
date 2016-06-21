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

import sys

from networking_bambuk._i18n import _LE

from oslo_log import log as logging

from networking_bambuk.common import config

from oslo_utils import importutils


LOG = logging.getLogger(__name__)


def main():

    try:
        bambuk_agent = importutils.import_object(config.get_bambuk_agent())
        bambuk_rpc = importutils.import_object(
            cfg.CONF.bambuk.rpc)
    except (RuntimeError, ValueError) as e:
        LOG.error(_LE("%s Agent terminated!"), e)
        sys.exit(1)

    # launch rpc
    bambuk_rpc.start(bambuk_agent)
