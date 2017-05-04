import ConfigParser
import json
import md5
import os
import SocketServer
import subprocess
import threading
import time

from networking_bambuk.cmd import plug_vif


CONFIG_FILE = '/etc/neutron/bambuk.ini'
CONFIG_FILE_MD5 = '/etc/neutron/bambuk.ini.md5'


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


def start_df(port_id, mac, host, clean_db):
    pid = process_exist(['df-local-controller'])
    if pid:
        subprocess.call(['kill', str(pid)])

    if clean_db:
        subprocess.Popen('df-db clean'.split(' ')).wait()

    init_cmds = [
        'ovs-vsctl del-br br-int',
        'ovs-vsctl del-br br-ex',
        'ovs-vsctl del-manager',
        'ovs-vsctl add-br br-ex',
        'ovs-vsctl add-br br-int',
        'ovs-vsctl --no-wait set bridge br-int fail-mode=secure'
        ' other-config:disable-in-band=true',
        'ovs-vsctl set bridge br-int protocols=OpenFlow10,OpenFlow13',
        'ovs-vsctl set-manager ptcp:6640:0.0.0.0',
    ]
    for c in init_cmds:
        subprocess.Popen(c.split(' ')).wait()

    subprocess.Popen([
        '/usr/local/bin/df-local-controller',
        '--config-file', '/etc/neutron/neutron.conf',
        '--config-file', '/etc/neutron/dragonflow.ini',
        '--log-file', '/var/log/dragonflow.log']
    )
    tap = plug_vif.plug_vif(port_id, mac, host)
    time.sleep(10)
    subprocess.Popen(
        'ip', 'netns', 'exec', 'vm', 'dhclient', '-nw', '-v',
        '-pf', '/run/dhclient.%s.pid' % tap,
        '-lf', '/var/lib/dhcp/dhclient.%s.leases' % tap, tap
    )


class Startup(object):

    def _write_file(self, file_name, content):
        with open(file_name, 'w') as dest:
            if isinstance(content, str):
                dest.write(content)
            else:
                for line in content:
                    dest.write(line)

    def apply(self, params):
        # write the configuration
        with open(CONFIG_FILE, 'w') as cfgfile:
            c = ConfigParser.ConfigParser()
            c.add_section('bambuk')
            for k, v in params.iteritems():
                c.set('bambuk', k, v)
            c.write(cfgfile)

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
        start_df(params['port_id'], params['mac'], params['host'], True)


class StartupTCPHandler(SocketServer.StreamRequestHandler):

    def handle(self):
        config = Startup()
        cfg = self.rfile.readline().strip()
        print('received %s from %s' % (cfg, self.client_address[0]))
        new_md5 = md5.new(cfg).hexdigest()
        old_md5 = None
        # read current  md5
        if os.path.exists(CONFIG_FILE_MD5):
            with open(CONFIG_FILE_MD5, 'r') as cfgfile_md5:
                old_md5 = cfgfile_md5.read()
        if old_md5 != new_md5 or not process_exist(['df-local-controller']):
            with open(CONFIG_FILE_MD5, 'w') as cfgfile_md5:
                old_md5 = cfgfile_md5.write(new_md5)
            data = json.decoder.JSONDecoder().decode(cfg)
            config.apply(data)
        self.wfile.write("OK")


def main():
    HOST = '0.0.0.0'
    PORT = 8080

    SocketServer.TCPServer.allow_reuse_address = True
    server = SocketServer.TCPServer((HOST, PORT), StartupTCPHandler)
    print('Started config tcp server on %s:%s ' % (HOST, PORT))


    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.start()
    time.sleep(1)

    if os.path.exists(CONFIG_FILE):
        c = ConfigParser.ConfigParser()
        c.read(CONFIG_FILE)
        start_df(
            c.get('bambuk', 'port_id'),
            c.get('bambuk', 'mac'),
            c.get('bambuk', 'host'),
            False
        )


if __name__ == "__main__":
    main()