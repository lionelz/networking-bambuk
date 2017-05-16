import abc
import eventlet
import json
import six
import traceback

from networking_bambuk.common import config

from oslo_log import log

from oslo_utils import importutils


LOG = log.getLogger(__name__)


@six.add_metaclass(abc.ABCMeta)
class BambukSenderPool(object):

    @abc.abstractmethod
    def get_sender(self, vm):
        pass

    @abc.abstractmethod
    def start_bulk_send(self):
        pass
    
    @abc.abstractmethod
    def loop(self, send_id):
        pass


class BambukAgentClient(object):

    def __init__(self):
        self._sender_pool = importutils.import_object(config.sender_pool())

    def state(self, server_conf, vm):
#         LOG.debug('state to %s' % vm)
        return self._sender_pool.get_sender(vm).state(server_conf)

    def apply(self, connect_db, vm):
        self._sender_pool.get_sender(vm).apply(connect_db)

    def update(self, connect_db_update, vms):
        send_id = self._sender_pool.start_bulk_send()
        for vm in vms:
            self._sender_pool.get_sender(vm).update(
                connect_db_update, send_id)
        self._sender_pool.loop(send_id)

    def delete(self, connect_db_delete, vms):
        send_id = self._sender_pool.start_bulk_send()
        for vm in vms:
            self._sender_pool.get_sender(vm).delete(
                connect_db_delete, send_id)
        self._sender_pool.loop(send_id)


@six.add_metaclass(abc.ABCMeta)
class BambukRpc(object):

    @abc.abstractmethod
    def state(self, server_conf):
        pass

    @abc.abstractmethod
    def apply(self, connect_db, send_id):
        pass

    @abc.abstractmethod
    def update(self, connect_db_delete, send_id):
        '''
        connect_db_delete: {
            'table': 'xxx',
            'key': 'xxx',
            'value': 'xxx',
        '''
        pass

    @abc.abstractmethod
    def delete(self, connect_db_update, send_id):
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
        eventlet.sleep(0)

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
        res = self._bambuk_agent.state(server_conf=server_conf)
        LOG.debug('state: %s' % res)
        return res

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
    def send(self, message, send_id=None):
        pass

    def call_method(self, method, send_id=None, **kwargs):
        message = {'method': method}
        for name, value in kwargs.items():
            message[name] = value
        message_json = json.dumps(message)
#         LOG.debug("Sending message: %s" % message_json)
        nr = 0
        sent = False
        while (not sent):
            try:
                response_json = self.send(message_json, send_id)
                sent = True
            except Exception as e:
                nr = nr + 1
                if nr == 10:
                    LOG.error(
                        'retried 10 times to send %s', traceback.format_exc())
                    raise e
                LOG.error(
                    'retry number %d, %s', (nr, traceback.format_exc()))
                eventlet.sleep(2)
#         LOG.debug("Received response: %s" % response_json)
        if not send_id:
            return json.loads(response_json)

    def state(self, server_conf, send_id=None):
        return self.call_method(
            'state', send_id, server_conf=server_conf)

    def apply(self, connect_db, send_id=None):
        return self.call_method(
            'apply', send_id, connect_db=connect_db)

    def update(self, connect_db_update, send_id=None):
        return self.call_method(
            'update', send_id, connect_db_update=connect_db_update)

    def delete(self, connect_db_delete, send_id=None):
        return self.call_method(
            'delete', send_id, connect_db_delete=connect_db_delete)


@six.add_metaclass(abc.ABCMeta)
class BambukAgent(BambukRpc):
    pass
