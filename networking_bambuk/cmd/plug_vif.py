# Copyright 2011 OpenStack Foundation.
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


def execute(*cmd, **kwargs):
    try:
        subprocess.Popen(list(cmd))
    except OSError as err:
        print('Got an OSError\ncommand: %(cmd)r\n'
              'errno: %(errno)r' % {"cmd": cmd, "errno": err.errno})
    finally:
        time.sleep(0)


def delete_net_dev(dev):
    """Delete a network device only if it exists."""
    if device_exists(dev):
        execute('ip', 'link', 'delete', dev, run_as_root=True,
                check_exit_code=False)


def create_veth_pair(dev1_name, dev2_name):
    """Create a pair of veth devices with the specified names,
    deleting any previous devices with those names.
    """
    for dev in [dev1_name, dev2_name]:
        delete_net_dev(dev)

    execute('ip', 'link', 'add', dev1_name, 'type', 'veth', 'peer',
            'name', dev2_name, run_as_root=True)
    for dev in [dev1_name, dev2_name]:
        execute('ip', 'link', 'set', dev, 'up', run_as_root=True)
        execute('ip', 'link', 'set', dev, 'promisc', 'on',
                      run_as_root=True)


def get_veth_pair_names2(iface_id):
    return (("qvm%s" % iface_id)[:NIC_NAME_LEN],
            ("qvo%s" % iface_id)[:NIC_NAME_LEN])


def ovs_vsctl(args):
    full_args = ['ovs-vsctl', '--timeout=30'] + args
    return execute(*full_args)


def create_ovs_vif_port(bridge, dev, iface_id, mac, instance_id):
    ovs_vsctl(['--', '--if-exists', 'del-port', dev, '--',
               'add-port', bridge, dev,
               '--', 'set', 'Interface', dev,
               'external-ids:iface-id=%s' % iface_id,
               'external-ids:iface-status=active',
               'external-ids:attached-mac=%s' % mac,
               'external-ids:vm-uuid=%s' % instance_id])


def main():
    iface_id = sys.argv[1]
    mac = sys.argv[2]
    instance_id = sys.argv[3]
    veths = get_veth_pair_names2(iface_id)
    create_veth_pair(veths[0], veths[1])
    create_ovs_vif_port('br-int',
                        veths[0],
                        iface_id,
                        mac,
                        instance_id)

if __name__ == '__main__':
    main()
