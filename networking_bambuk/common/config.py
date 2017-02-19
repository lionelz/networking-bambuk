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
from oslo_log import log

from networking_bambuk._i18n import _
from networking_bambuk import version

from neutron.common import rpc


bambuk_opts = [
    cfg.StrOpt('sender_pool',
               default='networking_bambuk.rpc.zeromq_rpc.ZeroMQSenderPool',
               help=_('The client agent pool class implementation')),
    cfg.StrOpt('receiver',
               default='networking_bambuk.rpc.zeromq_rpc.ZeroMQReceiver',
               help=_('The client agent pool class implementation')),
    cfg.StrOpt('json_db_cache',
               default='/tmp/connect_db.json',
               help=_('The JSON DB file cache')),
    cfg.StrOpt('listener_ip',
               default='0.0.0.0',
               help=_('The ip to listen')),
    cfg.IntOpt('listener_port',
               default=5555,
               help=_('The port to listen')),
    cfg.BoolOpt('l2_population', default=False,
                help=_("Extension to use alongside ml2 plugin's l2population "
                       "mechanism driver.")),
    cfg.StrOpt('bambuk_host',
               help=_('The NIC IP for rpc that needs to listen')),
]

cfg.CONF.register_opts(bambuk_opts, group='bambuk')


def init(args, **kwargs):
    product_name = "bambuk-dispatcher-agent"
    log.register_options(cfg.CONF)
    log.setup(cfg.CONF, product_name)
    cfg.CONF(args=args, project=product_name,
             version='%%(prog)s %s' % version.version_info.release_string(),
             **kwargs)
    rpc.init(cfg.CONF)

def list_opts():
    return [
        ('bambuk', bambuk_opts),
    ]


def get_sender_pool():
    return cfg.CONF.bambuk.sender_pool


def get_receiver():
    return cfg.CONF.bambuk.receiver


def get_json_db_cache():
    return cfg.CONF.bambuk.json_db_cache


def get_bambuk_host():
    return cfg.CONF.bambuk.bambuk_host


def get_listener_ip():
    return cfg.CONF.bambuk.listener_ip


def get_listener_port():
    return cfg.CONF.bambuk.listener_port


def get_l2_population():
    return cfg.CONF.bambuk.l2_population
