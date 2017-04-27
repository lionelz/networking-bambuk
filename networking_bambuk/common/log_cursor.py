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

# TODO:
#   - thread that wait Event
#   - on event read the bambuk log update
#   - for each port update log:
#        - calculate the port connectivity
#        - call apply
#

# TODO:
#   - retry policy configuration
#   - max nb retry
#   - retry after 30s, 5mn, 1hours...

# TODO:
#   - thread that poll each 5 mns the retry
#   - read all bambuk log update that need to retry now
#   - for each port update log:
#        - calculate the port connectivity
#        - call apply

import eventlet

from neutron import context as n_context

from networking_bambuk.common import update_actions
from networking_bambuk.db.bambuk import bambuk_db
from networking_bambuk.rpc.bambuk_rpc import BambukAgentClient
from oslo_log import log as o_log


LOG = o_log.getLogger(__name__)


class LogCursor():

    def __init__(self, nb_threads=1):
        self._bambuk_client = BambukAgentClient()
        self._pool = eventlet.GreenPool(nb_threads)
        self.awake()

    def awake(self):
        LOG.debug('awake')
        self._pool.spawn_n(self.work)
        eventlet.greenthread.sleep(0)

    def work(self):
        n = 0
        ctx = n_context.get_admin_context()
        while True:
            with ctx.session.begin():
                b_log = bambuk_db.get_one_bambuk_update_log(ctx)
                if not b_log:
                    LOG.debug('No more bambuk update log, %d processed' % n)
                    return
            with ctx.session.begin():
                n = n + 1
                _action_touple = (b_log.obj_type, b_log.action_type)
                _cls_action = update_actions.ACTIONS_CLASS.get(_action_touple)
                if _cls_action:
                    _handler = _cls_action(b_log, self._bambuk_client)
                    _handler.process()
                    LOG.debug('Bambuk processed log: %s' % b_log)
                    return
                LOG.debug('Bambuk has no handler for log: %s' % b_log)
