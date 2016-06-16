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

import unittest

from networking_bambuk.rpc.zeromq import zeromq_rpc
from networking_bambuk.rpc import bambuk_rpc


class FakeBambukAgent(bambuk_rpc.BambukRpc):
    
    def __init__(self):
        self.state = None
        self.server_conf = None
        self.vm_connectivity = None
        self.vm_connectivity_update = None
        self.obj_version = None

    def agent_state(self, server_conf):
        self.server_conf = server_conf.copy()
        self.state = {'state': True}
        return self.state

    def apply(self, vm_connectivity):
        self.vm_connectivity = vm_connectivity
        return

    def update(self, vm_connectivity_update):
        self.vm_connectivity_update = vm_connectivity_update
        return

    def version(self):
        self.obj_version = '1.2'
        return self.obj_version

class TestZeroMqRpc(unittest.TestCase):

    def setUp(self):
        self._bambuk_agent = FakeBambukAgent()
        self._receiver = zeromq_rpc.ZeroMQReceiver(self._bambuk_agent)
        self._sender = zeromq_rpc.ZeroMQSender('localhost')

    def test_agent_state(self):
        server_conf = {'server_ip': '10.10.10.10'}
        state = self._sender.agent_state(server_conf)
        self.assertEqual(state, self._bambuk_agent.state)
        self.assertEqual(server_conf, self._bambuk_agent.server_conf)

    def test_apply(self):
        vm_connectivity = {'port': 'xxx'}
        self._sender.apply(vm_connectivity)
        self.assertEqual(vm_connectivity, self._bambuk_agent.vm_connectivity)

    def test_update(self):
        vm_connectivity_update = {'port': 'xxx'}
        self._sender.update(vm_connectivity_update)
        self.assertEqual(vm_connectivity_update,
                         self._bambuk_agent.vm_connectivity_update)

    def test_version(self):
        version = self._sender.version()
        self.assertEqual(version, self._bambuk_agent.obj_version)


if __name__ == '__main__':
    unittest.main()

