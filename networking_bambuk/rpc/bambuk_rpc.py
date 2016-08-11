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
import eventlet

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
        self._sender_pool = importutils.import_object(config.get_sender_pool())

    def state(self, server_conf, vm):
        try:
            return self._sender_pool.get_sender(vm).state(server_conf)
        except Exception as ex:
            LOG.error('an error occurs: %s', ex)
            return None

    def apply(self, connect_db, vm):
        try:
            self._sender_pool.get_sender(vm).apply(connect_db)
        except Exception as ex:
            LOG.error('an error occurs: %s', ex)

    def update(self, connect_db_update, vms):
        for vm in vms:
            try:
                self._sender_pool.get_sender(vm).update(connect_db_update)
            except Exception as ex:
                LOG.error('an error occurs: %s', ex)

    def delete(self, connect_db_delete, vms):
        for vm in vms:
            try:
                self._sender_pool.get_sender(vm).delete(connect_db_delete)
            except Exception as ex:
                LOG.error('an error occurs: %s', ex)


@six.add_metaclass(abc.ABCMeta)
class BambukRpc(object):
    
    @abc.abstractmethod
    def state(self, server_conf):
        pass

    @abc.abstractmethod
    def apply(self, connect_db):
        pass

    @abc.abstractmethod
    def update(self, connect_db_delete):
        '''
        connect_db_delete: {
            'table': 'xxx',
            'key': 'xxx',
            'value': 'xxx',
        '''
        pass

    @abc.abstractmethod
    def delete(self, connect_db_update):
        '''
        connect_db_update: {
            'table': 'xxx',
            'key': 'xxx',
        '''
        pass


@six.add_metaclass(abc.ABCMeta)
class BambukRpcReceiver(BambukRpc):

    def __init__(self, bambuk_agent):
        self._bambuk_agent = bambuk_agent
        self._running = True
        eventlet.spawn_n(self.receive)

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

    def state(self, **kwargs):
        server_conf = kwargs.get('server_conf')
        return self._bambuk_agent.state(server_conf=server_conf)

    def apply(self, **kwargs):
        connect_db = kwargs.get('connect_db')
        return self._bambuk_agent.apply(connect_db=connect_db)

    def update(self, **kwargs):
        connect_db_update = kwargs.get('connect_db_update')
        return self._bambuk_agent.update(
            connect_db_update=connect_db_update)

    def delete(self, **kwargs):
        connect_db_delete = kwargs.get('connect_db_delete')
        return self._bambuk_agent.delete(
            connect_db_delete=connect_db_delete)

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

    def state(self, server_conf):
        return self.call_method('state', server_conf=server_conf)

    def apply(self, connect_db):
        return self.call_method('apply', connect_db=connect_db)

    def update(self, connect_db_update):
        return self.call_method('update',
                                connect_db_update=connect_db_update)

    def delete(self, connect_db_delete):
        return self.call_method('delete',
                                connect_db_delete=connect_db_delete)


@six.add_metaclass(abc.ABCMeta)
class BambukAgent(BambukRpc):
    pass