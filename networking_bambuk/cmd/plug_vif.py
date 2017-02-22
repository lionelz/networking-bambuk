# All Rights Reserved.
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

import os
import subprocess
import time
import sys


NIC_NAME_LEN = 14


def device_exists(device):
    """Check if ethernet device exists."""
    return os.path.exists('/sys/class/net/%s' % device)


def execute(*cmd):
    print(cmd)
    try:
        subprocess.call(list(cmd))
    except OSError as err:
        print('Got an OSError\ncommand: %(cmd)r\n'
              'errno: %(errno)r' % {"cmd": cmd, "errno": err.errno})
    finally:
        time.sleep(0)


def get_tap_name(iface_id):
    return ("tap%s" % iface_id)[:NIC_NAME_LEN]


def ovs_vsctl(args):
    full_args = ['ovs-vsctl', '--timeout=30'] + args
    return execute(*full_args)


def create_ovs_vif_port(bridge, dev, iface_id, mac, instance_id):
    ovs_vsctl(['--', '--if-exists', 'del-port', dev, '--',
               'add-port', bridge, dev,
               '--', 'set', 'Interface', dev,
               'type=internal',
               'external-ids:iface-id=%s' % iface_id,
               'external-ids:iface-status=active',
               'external-ids:attached-mac=%s' % mac,
               'external-ids:vm-uuid=%s' % instance_id])

def plug_vif(iface_id, mac, instance_id):
    tap = get_tap_name(iface_id)
    ovs_vsctl(['del-port', 'br-int', tap])
    create_ovs_vif_port('br-int',
                        tap,
                        iface_id,
                        mac,
                        instance_id)
    execute('ip', 'link', 'set', tap, 'address', mac)
    execute('ip', 'link', 'set', tap, 'up')


def main():
    plug_vif(sys.argv[1], sys.argv[2], sys.argv[3])

if __name__ == '__main__':
    main()
