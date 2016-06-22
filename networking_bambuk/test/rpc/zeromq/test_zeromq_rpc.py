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
        self.agent_state = None
        self.server_conf = None
        self.vm_connectivity = None
        self.vm_connectivity_update = None

    def state(self, server_conf):
        self.server_conf = server_conf
        self.agent_state = {'active': True,
                            'capabilities': {'l2': '0.1'}}
        return self.agent_state

    def apply(self, vm_connectivity):
        self.vm_connectivity = vm_connectivity
        return True

    def update(self, vm_connectivity_update):
        self.vm_connectivity_update = vm_connectivity_update
        return True


class TestZeroMqRpc(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        bambuk_agent = FakeBambukAgent()
        TestZeroMqRpc._receiver = zeromq_rpc.ZeroMQReceiver(bambuk_agent)
        TestZeroMqRpc._sender = zeromq_rpc.ZeroMQSender('localhost')

    @classmethod
    def tearDownClass(cls):
        TestZeroMqRpc._receiver.close()

    def test_state(self):
        server_conf = {'server_ip': '10.10.10.10'}
        state = TestZeroMqRpc._sender.state(server_conf)
        self.assertDictEqual(state,
                             TestZeroMqRpc._receiver._bambuk_agent.agent_state)
        self.assertDictEqual(server_conf,
                             TestZeroMqRpc._receiver._bambuk_agent.server_conf)

    def test_apply(self):
        vm_connectivity = {'port': 'xxx'}
        TestZeroMqRpc._sender.apply(vm_connectivity)
        self.assertDictEqual(vm_connectivity,
                             TestZeroMqRpc._receiver._bambuk_agent.vm_connectivity)

    def test_update(self):
        vm_connectivity_update = {'port': 'xxx'}
        TestZeroMqRpc._sender.update(vm_connectivity_update)
        self.assertDictEqual(
            vm_connectivity_update,
            TestZeroMqRpc._receiver._bambuk_agent.vm_connectivity_update)


if __name__ == '__main__':
    unittest.main()

