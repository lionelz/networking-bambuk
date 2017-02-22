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
    cfg.StrOpt('provider', default='null',
               help=_("Provider: aws|openstack|null.")),
    cfg.StrOpt('aws_access_key_id',
               help=_("AWS Access Key Id.")),
    cfg.StrOpt('aws_secret_access_key',
               help=_("AWS Secret Access Key.")),
    cfg.StrOpt('aws_region_name',
               help=_("AWS Region Name.")),
    cfg.StrOpt('aws_vpc',
               help=_("AWS VPC id.")),
    cfg.StrOpt('os_username',
               help=_("The Openstack username.")),
    cfg.StrOpt('os_password',
               help=_("The Openstack Password.")),
    cfg.StrOpt('os_tenant_id',
               help=_("The Openstack Tenant Id.")),
    cfg.StrOpt('os_auth_url',
               help=_("The Openstack Auth Url (keystone).")),
    cfg.StrOpt('os_availability_zone',
               default='nova',
               help=_("The Openstack Availability zone.")),
]

cfg.CONF.register_opts(bambuk_opts, group='bambuk')


def init(args, **kwargs):
    product_name = 'bambuk-dispatcher-agent'
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


def sender_pool():
    return cfg.CONF.bambuk.sender_pool


def receiver():
    return cfg.CONF.bambuk.receiver


def json_db_cache():
    return cfg.CONF.bambuk.json_db_cache


def listener_ip():
    return cfg.CONF.bambuk.listener_ip


def listener_port():
    return cfg.CONF.bambuk.listener_port


def l2_population():
    return cfg.CONF.bambuk.l2_population


def host():
    return cfg.CONF.host


def provider():
    return cfg.CONF.bambuk.provider


def aws_access_key_id():
    return cfg.CONF.bambuk.aws_access_key_id


def aws_secret_access_key():
    return cfg.CONF.bambuk.aws_secret_access_key


def aws_region_name():
    return cfg.CONF.bambuk.aws_region_name


def aws_vpc():
    return cfg.CONF.bambuk.aws_vpc


def os_username():
    return cfg.CONF.bambuk.os_username


def os_password():
    return cfg.CONF.bambuk.os_password


def os_tenant_id():
    return cfg.CONF.bambuk.os_tenant_id


def os_auth_url():
    return cfg.CONF.bambuk.os_auth_url


def os_availability_zone():
    return cfg.CONF.bambuk.os_availability_zone
