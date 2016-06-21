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
from networking_bambuk._i18n import _


bambuk_opts = [
    cfg.StrOpt('bambuk_agent',
               default='networking_bambuk.agent.controller.ovs_agent.BambukHandler',
               help=_('The agent class implementation')),
    cfg.StrOpt('client_pool',
               default='networking_bambuk.rpc.zeromq.zeromq_rpc.ZeroMQSenderPool',
               help=_('The client agent pool class implementation')),
    cfg.StrOpt('listener_ip',
               default='*',
               help=_('The ip to listen')),
    cfg.IntOpt('listener_port',
               default=5555,
               help=_('The port to listen')),
    cfg.StrOpt('bambuk_host',
               help=_('The NIC IP for rpc that needs to listen')),
]

cfg.CONF.register_opts(bambuk_opts, group='bambuk')


def list_opts():
    return [
        ('bambuk', bambuk_opts),
    ]


def get_bambuk_agent():
    return cfg.CONF.bambuk.bambuk_agent


def get_client_pool():
    return cfg.CONF.bambuk.client_pool


def get_bambuk_host():
    return cfg.CONF.bambuk.bambuk_host


def get_listener_ip():
    return cfg.CONF.bambuk.listener_ip


def get_listener_port():
    return cfg.CONF.bambuk.listener_port


