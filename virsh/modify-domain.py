#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# modify-domain.py -- modify a KVM domain
#
# Copyright (C) 2013 Martijn Koster
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation files
# (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:  The above copyright notice and
# this permission notice shall be included in all copies or
# substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import re, sys, uuid
from lxml import etree
from optparse import OptionParser
import random

def randomMAC():
    mac = [ 0x00, 0x16, 0x3e,
        random.randint(0x00, 0x7f),
        random.randint(0x00, 0xff),
        random.randint(0x00, 0xff) ]
    return ':'.join(map(lambda x: "%02x" % x, mac))

parser = OptionParser()
parser.add_option("--name")
parser.add_option("--new-uuid", action="store_true")
parser.add_option("--disk-path")
parser.add_option("--modify-mac", action="store_true", default=False)
(options, args) = parser.parse_args()

tree = etree.parse(sys.stdin)

if options.name:
    name_el = tree.xpath("/domain/name")[0]
    name_el.text = options.name

if options.new_uuid:
    uuid_el = tree.xpath("/domain/uuid")[0]
    uuid_el.text = str(uuid.uuid1())

if options.disk_path is not None:
    if options.disk_path[0] is not '/':
        sys.exit("disk_path is not an absolute path")
    source_el = tree.xpath("/domain/devices/disk[@device='disk']/source")[0]
    source_el.set('file', options.disk_path)
    if re.match('.*\.qcow2$', options.disk_path):
        driver = 'qcow2'
    else:
        driver = 'raw'
    driver_el = tree.xpath("/domain/devices/disk[@device='disk']/driver")[0]
    driver_el.set('type', driver)

if options.modify_mac:
    ifaces_macs = tree.xpath("/domain/devices/interface[@type='direct']/mac")
    for iface_mac in ifaces_macs:
        new_mac = randomMAC()
        iface_mac.set('address', new_mac)

print(etree.tostring(tree, pretty_print=True))



