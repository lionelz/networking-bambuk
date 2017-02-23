import json
import os
import SocketServer
import subprocess
import time
from networking_bambuk.cmd import plug_vif


MGNT_IP_FILE = '/etc/bambuk/mgnt_ip'


def process_exist(words):
    s = subprocess.Popen(["ps", "ax"], stdout=subprocess.PIPE)
    for x in s.stdout:
        fi = True
        for word in words:
            if word not in x:
                fi = False
                break
        if fi:
            return x.split()[0]
    return False


class Startup(object):

    def _write_file(self, file_name, content):
        with open(file_name, 'w') as dest:
            if isinstance(content, str):
                dest.write(content)
            else:
                for line in content:
                    dest.write(line)

    def apply(self, params):
        proc = subprocess.Popen(
            ['find', '/etc', '-name', '*.tmpl'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, _ = proc.communicate()
        for file_conf in stdout.split():
            print('file configuration %s' % file_conf)
            with open(file_conf, 'r') as source:
                lines = source.readlines()                
            for i in range(len(lines)):
                for key, value in params.iteritems():
                    if value:
                        lines[i] = lines[i].replace('##%s##' % key, value)
            self._write_file(
                file_conf[0:file_conf.rfind('.')], lines)
        if 'host' in params:
            subprocess.call(['hostname', params['host']]) 
            self._write_file('/etc/hostname', params['host'])
        if 'mgnt_ip' in params:
            self._write_file(MNGT_IP_FILE, params['mgnt_ip'])

        # TODO:
        #  - clean-up ovs

        pid = process_exist(['df-local-controller'])
        if pid:
            subprocess.call(['kill', str(pid)])
        subprocess.call([
            '/usr/local/bin/df-local-controller',
            '--config-file /etc/neutron/neutron.conf',
            '--config-file /etc/neutron/dragonflow.ini',
            '--log-file /var/logs/dragonflow.log'
        ])
        time.sleep(10)
        plug_vif.plug_vif(
            params['port_id'],
            params['mac'],
            params['host']
        )


class StartupTCPHandler(SocketServer.StreamRequestHandler):

    def handle(self):
        config = Startup()
        data = json.decoder.JSONDecoder().decode(self.rfile.readline().strip())
        print('received %s from %s' % (data, self.client_address[0]))
        config.apply(data)
        self.wfile.write("OK")


def main():
    HOST = '0.0.0.0'
    PORT = 8080
    if os.path.exists(MNGT_IP_FILE):
        with open(MNGT_IP_FILE, 'r') as source:
            HOST = source.readline()                
    server = SocketServer.TCPServer((HOST, PORT), StartupTCPHandler)
    print('Started config tcp server on %s:%s ' % (HOST, PORT))

    server.serve_forever()


if __name__ == "__main__":
    main()