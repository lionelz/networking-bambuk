from neutronclient._i18n import _
from neutronclient.common import extension
from neutronclient.neutron.v2_0 import NeutronCommand


class Providerport(extension.NeutronClientExtension):
    resource = 'providerport'
    resource_plural = '%ss' % resource
    object_path = '/%s' % resource_plural
    resource_path = '/%s/%%s' % resource_plural
    versions = ['2.0']


class ProviderportCreate(extension.ClientExtensionCreate, Providerport):
    """Create an provider port information."""

    shell_command = 'providerport-create'

    def get_parser(self, prog_name):
        parser = NeutronCommand.get_parser(self, prog_name)
        self.add_known_arguments(parser)
        return parser

    def add_known_arguments(self, parser):
        parser.add_argument(
            '--name', dest='name',
            help=_('Optional port name.'))
        parser.add_argument(
            '--provider-ip', dest='provider_ip',
            help=_('Optional Provider IP for Null provider.'))
        parser.add_argument(
            '--provider-mgnt-ip', dest='provider_mgnt_ip',
            help=_('Optional Provider management IP for Null provider.'))
        parser.add_argument(
            'port_id', metavar='<NEUTRON_PORT_ID>',
            help=_('Neutron Port ID.'))

    def args2body(self, parsed_args):
        body = {'providerport':
            {
                'port_id': parsed_args.port_id,
            }
        }
        p = body['providerport']
        if parsed_args.name:
            p['name'] = parsed_args.name
        if parsed_args.provider_ip:
            p['provider_ip'] = parsed_args.provider_ip
        if parsed_args.provider_mgnt_ip:
            p['provider_mgnt_ip'] = parsed_args.provider_mgnt_ip
        return body


class ProviderportList(extension.ClientExtensionList, Providerport):
    """List provider ports that belongs to a given tenant."""

    shell_command = 'providerport-list'
    list_columns = ['id', 'name', 'tenant_id', 'provider_ip',
                    'provider_mgnt_ip']
    pagination_support = True
    sorting_support = True


class ProviderportShow(extension.ClientExtensionShow, Providerport):
    """Show information of a given provider port."""

    shell_command = 'providerport-show'


class ProviderportDelete(extension.ClientExtensionDelete, Providerport):
    """Delete a given provider port."""

    shell_command = 'providerport-delete'


class ProviderportUpdate(extension.ClientExtensionUpdate, Providerport):
    """Update a given provider port."""

    shell_command = 'providerport-update'
