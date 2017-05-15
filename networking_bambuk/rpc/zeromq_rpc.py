import eventlet
import socket
import threading
import uuid

from oslo_log import log

from eventlet.green import zmq

from zmq import error

from networking_bambuk.rpc import bambuk_rpc
from networking_bambuk.common import config


LOG = log.getLogger(__name__)


class ZeroMQReceiver(bambuk_rpc.BambukRpcReceiver):

    def __init__(self, bambuk_agent):
        self._port = config.listener_port()
        self._ip = config.listener_ip()
        super(ZeroMQReceiver, self).__init__(bambuk_agent)

    def receive(self):
        context = zmq.Context()
        self._socket = context.socket(zmq.REP)
        self._socket.bind("tcp://%s:%d" % (self._ip, self._port))
        while self._running:
            #  Wait for next request from client
            try:
                LOG.info('waiting for message')
                message = self._socket.recv()
                LOG.info('received %s' % message)
                response = self.call_agent(message)
                LOG.info('sending %s' % response)
                self._socket.send(response)
                LOG.info('%s sent' % response)
            except error.Again:
                pass


class ZeroMQSenderPool(bambuk_rpc.BambukSenderPool):

    senders = {}
    pools = {}

    def get_sender(self, vm, send_id=None):
        key = "tcp://%s:%d" % (vm, config.listener_port())
        sender = ZeroMQSenderPool.senders.get(key)
        if not sender:
            sender = ZeroMQSender(vm, config.listener_port())
            ZeroMQSenderPool.senders[key] = sender
        return sender

    def start_bulk_send(self):
        send_id = uuid.uuid4()
        ZeroMQSenderPool.senders[send_id] = eventlet.GreenPool()
        return send_id
    
    def loop(self, send_id):
        ZeroMQSenderPool.senders[send_id].waitall()
        del ZeroMQSenderPool.senders[send_id]


class ZeroMQSender(bambuk_rpc.BambukRpcSender):

    def init(self):
        LOG.info('init')
        context = zmq.Context()
        context.setsockopt(socket.SO_REUSEADDR, 1)
        self._socket = context.socket(zmq.REQ)
        self._socket.connect(self._conn)

    def __init__(self, host_or_ip, port=config.listener_port()):
        super(ZeroMQSender, self).__init__()
        self._lock = threading.Lock()
        self._conn = 'tcp://%s:%d' % (host_or_ip, port)
        self.init()

    def _send(self, message):
        self._lock.acquire()
        self._socket.send(message)
        res = self._socket.recv()
        self._lock.release()
        return res

    def send(self, message, send_id=None):
        LOG.debug('sending to %s' % self._conn)
        if send_id:
            ZeroMQSenderPool.senders[send_id].spawn_n(self._send, message)
            LOG.debug('sent to %s in bilk mode' % self._conn)
            return
        else:
            res = self._send(message)
            LOG.debug('sent to %s (%s)' % (self._conn, res))
            return res
