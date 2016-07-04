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
import zmq
from zmq import error
from networking_bambuk.rpc import bambuk_rpc
from networking_bambuk.common import config


LOG = log.getLogger(__name__)


class ZeroMQReceiver(bambuk_rpc.BambukRpcReceiver):
    
    def __init__(self, bambuk_agent):
        self._port = config.get_listener_port()
        self._ip = config.get_listener_ip()
        super(ZeroMQReceiver, self).__init__(bambuk_agent)

    def receive(self):
        context = zmq.Context()
        self._socket = context.socket(zmq.REP)
        self._socket.bind("tcp://%s:%d" % (self._ip, self._port))
        self._socket.RCVTIMEO = 5000
        while self._running:
            #  Wait for next request from client
            try:
                response = self.call_agent(self._socket.recv())
                self._socket.send(response)
            except error.Again:
                pass


class ZeroMQSenderPool(bambuk_rpc.BambukSenderPool):

    senders = {}

    def get_sender(self, vm):
        key = "tcp://%s:%d" % (vm, config.get_listener_port())
        sender = ZeroMQSenderPool.senders.get(key)
        if not sender:
            sender = ZeroMQSender(vm, config.get_listener_port())
            ZeroMQSenderPool.senders[key] = sender
        return sender


class ZeroMQSender(bambuk_rpc.BambukRpcSender):

    def __init__(self, host_or_ip, port=config.get_listener_port()):
        super(ZeroMQSender, self).__init__()
        context = zmq.Context()
        self._socket = context.socket(zmq.REQ)
        self._socket.connect("tcp://%s:%d" % (host_or_ip, port))

    def send(self, message):
        self._socket.send(message)
        return self._socket.recv()
        
