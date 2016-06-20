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

import json
from oslo_log import log
import threading
import zmq
from zmq import error


LOG = log.getLogger(__name__)


DEFAULT_PORT = 5555


class ZeroMQReceiver(object):
    
    def __init__(self, bambuk_agent, port=DEFAULT_PORT, ip='*'):
        self._bambuk_agent = bambuk_agent
        self._running = True
        self._port = port
        self._ip = ip
        thread = threading.Thread(target=self.receive)
        thread.start()

    def receive(self):
        context = zmq.Context()
        self._socket = context.socket(zmq.REP)
        self._socket.bind("tcp://%s:%d" % (self._ip, self._port))
        self._socket.RCVTIMEO = 5000
        while self._running:
            #  Wait for next request from client
            try:
                message_json = self._socket.recv()
                LOG.debug("Received message: %s" % message_json)
                # call bambuk_agent
                message = json.loads(message_json)
                method = message['method']
                handler = getattr(self, method, None)
                if handler is not None:
                    del message['method']
                    response = handler(**message)
                    #  Send reply back to client
                    response_json = json.dumps(response)
                    LOG.debug("Sending response: %s" % response_json)
                    self._socket.send(response_json)
            except error.Again:
                pass

    def agent_state(self, **kwargs):
        server_conf = kwargs.get('server_conf')
        return self._bambuk_agent.agent_state(server_conf=server_conf)

    def apply(self, **kwargs):
        vm_connectivity = kwargs.get('vm_connectivity')
        return self._bambuk_agent.apply(vm_connectivity=vm_connectivity)

    def update(self, **kwargs):
        vm_connectivity_update = kwargs.get('vm_connectivity_update')
        return self._bambuk_agent.update(vm_connectivity_update=vm_connectivity_update)

    def version(self, **kwargs):
        return self._bambuk_agent.version()

    def close(self):
        self._running = False


class ZeroMQSender(object):

    def __init__(self, host_or_ip, port=DEFAULT_PORT):
        context = zmq.Context()
        self._socket = context.socket(zmq.REQ)
        self._socket.connect("tcp://%s:%d" % (host_or_ip, port))

    def call_method(self, method, **kwargs):
        message = {'method': method}
        for name, value in kwargs.items():
            message[name] = value
        message_json = json.dumps(message)
        LOG.debug("Sending message: %s" % message_json)
        self._socket.send(message_json)
        response_json = self._socket.recv()
        LOG.debug("Received response: %s" % response_json)
        return json.loads(response_json)

    def agent_state(self, server_conf):
        return self.call_method('agent_state', server_conf=server_conf)

    def apply(self, vm_connectivity):
        return self.call_method('apply', vm_connectivity=vm_connectivity)

    def update(self, vm_connectivity_update):
        return self.call_method('update',
                                vm_connectivity_update=vm_connectivity_update)

    def version(self):
        return self.call_method('version')
