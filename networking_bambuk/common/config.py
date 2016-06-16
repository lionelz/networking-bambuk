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

from oslo_config import cfg


bambuk_opts = [
    cfg.StrOpt('agent',
               default='networking_bambuk.agent.controller.ovs_agent.BambukHandler',
               help=_('The agent class implementation')),
    cfg.StrOpt('rpc',
               default='networking_bambuk.rpc.zeromq.zeromq_rpc.ZeroMQReceiver',
               help=_('The rpc receiver class implementation')),
]

cfg.CONF.register_opts(bambuk_opts, group='bambuk')


def list_opts():
    return [
        ('bambuk', bambuk_opts),
    ]
