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


import abc
import json
import six
import threading

from networking_bambuk.common import  config
from oslo_log import log
from oslo_utils import importutils


LOG = log.getLogger(__name__)


@six.add_metaclass(abc.ABCMeta)
class BambukSenderPool(object):
    
    @abc.abstractmethod
    def get_sender(self, vm):
        pass


class BambukAgentClient(object):

    def __init__(self):
        self._sender_pool = importutils.import_object(config.get_client_pool())

    def agent_state(self, server_conf, vm):
        return self._sender_pool.get_sender(vm).agent_state(self, server_conf)

    def apply(self, vm_connectivity, vms):
        for vm in vms:
            self._sender_pool.get_sender(vm).apply(vm_connectivity)

    def update(self, vm_connectivity_update, vms):
        for vm in vms:
            self._sender_pool.get_sender(vm).update(vm_connectivity_update)

    def version(self, vm):
        return self._sender_pool.get_sender(vm).version(self)


@six.add_metaclass(abc.ABCMeta)
class BambukRpc(object):
    
    @abc.abstractmethod
    def agent_state(self, server_conf):
        pass

    @abc.abstractmethod
    def apply(self, vm_connectivity):
        pass

    @abc.abstractmethod
    def update(self, vm_connectivity_update):
        pass

    @abc.abstractmethod
    def version(self):
        pass

@six.add_metaclass(abc.ABCMeta)
class BambukRpcReceiver(BambukRpc):

    def __init__(self, bambuk_agent):
        self._bambuk_agent = bambuk_agent
        self._running = True
        thread = threading.Thread(target=self.receive)
        thread.start()

    @abc.abstractmethod
    def receive(self):
        pass

    def call_agent(self, message_json):        
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
            return response_json

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




@six.add_metaclass(abc.ABCMeta)
class BambukRpcSender(BambukRpc):

    def __init__(self):
        pass

    @abc.abstractmethod
    def send(self, message):
        pass

    def call_method(self, method, **kwargs):
        message = {'method': method}
        for name, value in kwargs.items():
            message[name] = value
        message_json = json.dumps(message)
        LOG.debug("Sending message: %s" % message_json)
        response_json = self.send(message_json)
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


@six.add_metaclass(abc.ABCMeta)
class BambukAgent(BambukRpc):
    pass