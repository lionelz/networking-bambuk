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

from networking_bambuk.rpc import zeromq_rpc
from networking_bambuk.rpc import bambuk_rpc


class FakeBambukAgent(bambuk_rpc.BambukRpc):
    
    def __init__(self):
        pass

    def state(self, server_conf):
        self.server_conf = server_conf
        self.agent_state = {'active': True,
                            'capabilities': {'l2': '0.1'}}
        return self.agent_state

    def apply(self, connect_db):
        self.connect_db = connect_db
        return True

    def update(self, connect_db_update):
        self.connect_db_update = connect_db_update
        return True

    def delete(self, connect_db_delete):
        self.connect_db_delete = connect_db_delete
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
        connect_db = {'port': 'xxx'}
        TestZeroMqRpc._sender.apply(connect_db)
        self.assertDictEqual(connect_db,
                             TestZeroMqRpc._receiver._bambuk_agent.connect_db)

    def test_update(self):
        connect_db_update = {'port': 'xxx'}
        TestZeroMqRpc._sender.update(connect_db_update)
        self.assertDictEqual(
            connect_db_update,
            TestZeroMqRpc._receiver._bambuk_agent.connect_db_update)
        TestZeroMqRpc._sender.delete(connect_db_update)
        self.assertDictEqual(
            connect_db_update,
            TestZeroMqRpc._receiver._bambuk_agent.connect_db_delete)


if __name__ == '__main__':
    unittest.main()

