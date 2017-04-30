from eventlet.green import asyncore
import socket
import uuid

from oslo_log import log
from networking_bambuk.rpc import bambuk_rpc
from networking_bambuk.common import config


LOG = log.getLogger(__name__)


SEP = '\n.\n'
BUFF_SIZE = 8192

class ReceiverHandler(asyncore.dispatcher):

    def __init__(self, bambuk_agent, s=None, m=None):
        asyncore.dispatcher.__init__(self, sock=s, map=m)
        self.bambuk_agent = bambuk_agent
        self.out_buffer = ''
        self.in_buffer = ''

    def handle_read(self):
        self.in_buffer = self.in_buffer + self.recv(BUFF_SIZE)
        if self.in_buffer:
            LOG.debug('ReceiverHandler received %s' % repr(self.in_buffer))
            if self.in_buffer.endswith(SEP):
                self.out_buffer = self.bambuk_agent.call_agent(
                    self.in_buffer[0:len(self.in_buffer) - len(SEP)]) + SEP
                self.in_buffer = ''
            

    def handle_close(self):
        self.close()

    def initiate_send(self):
        num_sent = asyncore.dispatcher.send(self, self.out_buffer[:BUFF_SIZE])
        self.out_buffer = self.out_buffer[num_sent:]

    def handle_write(self):
        self.initiate_send()

    def writable(self):
        return (not self.connected) or len(self.out_buffer)

    def send(self, data):
        LOG.debug('ReceiverHandler sending %d' % repr(data))
        self.out_buffer = self.out_buffer + data
        self.initiate_send()


class TCPServer(asyncore.dispatcher):

    def __init__(self, address, bambuk_agent, m):
        asyncore.dispatcher.__init__(self, map=m)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind(address)
        self.listen(5)
        self.bambuk_agent = bambuk_agent
        self.m = m

    def handle_accept(self):
        pair = self.accept()
        if pair is not None:
            sock, addr = pair
            LOG.debug('Incoming connection from %s' % repr(addr))
            _ = ReceiverHandler(self.bambuk_agent, sock, self.m)


class AsyncTCPReceiver(bambuk_rpc.BambukRpcReceiver):

    def __init__(self, bambuk_agent):
        self._port = config.listener_port()
        self._ip = config.listener_ip()
        super(AsyncTCPReceiver, self).__init__(bambuk_agent)

    def receive(self):
        while self._running:
            m = {}
            _ = TCPServer((self._ip, self._port), self, m)
            asyncore.loop(map=m)


class TCPClient(asyncore.dispatcher):

    def __init__(self, address, message, m):
        asyncore.dispatcher.__init__(self, map=m)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect(address)
        self.out_buffer = message + SEP
        self.in_buffer = ''
        self.result = ''

    def handle_connect(self):
        LOG.debug('handle_connect')

    def handle_close(self):
        LOG.debug('handle_close')
        self.result = self.in_buffer[0:len(self.in_buffer) - len(SEP)]
        self.close()

    def handle_read(self):
        self.in_buffer = self.in_buffer + self.recv(BUFF_SIZE)
        if self.in_buffer:
            LOG.debug('ReceiverHandler received %s' % repr(self.in_buffer))
            if self.in_buffer.endswith(SEP):
                self.handle_close()

    def writable(self):
        return (len(self.out_buffer) > 0)

    def handle_write(self):
        sent = self.send(self.out_buffer)
        LOG.debug('TCPClient sent %d' % sent)
        self.out_buffer = self.out_buffer[sent:]


class AsyncTCPSenderPool(bambuk_rpc.BambukSenderPool):

    maps = {}

    def get_sender(self, vm, send_id=None):
        if send_id:
            return AsyncTCPSender(vm, AsyncTCPSenderPool.maps[send_id])
        return AsyncTCPSender(vm, {})
        
    def start_bulk_send(self):
        send_id = uuid.uuid4()
        AsyncTCPSenderPool.maps[send_id] = {}
        return send_id

    def loop(self, send_id):
        asyncore.loop(map=AsyncTCPSenderPool.maps[send_id])
        del AsyncTCPSenderPool.maps[send_id]


class AsyncTCPSender(bambuk_rpc.BambukRpcSender):

    def __init__(self, host_or_ip, m, port=config.listener_port()):
        super(AsyncTCPSender, self).__init__()
        LOG.debug("tcp://%s:%d" % (host_or_ip, port))
        self.address = (host_or_ip, port)
        self._map = m

    def send(self, message, send_id=None):
        c = TCPClient(self.address, message, self._map)
        if not send_id:
            asyncore.loop(map=self._map)
            return c.result
