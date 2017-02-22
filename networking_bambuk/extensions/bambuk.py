import abc

from neutron.api import extensions
from neutron.api.v2 import attributes
from neutron.api.v2 import resource_helper

from neutron_lib import exceptions

from oslo_log import log as logging

from neutron.services import service_base

from networking_bambuk import extensions as bambuk_extensions


extensions.append_api_extensions_path(bambuk_extensions.__path__)



LOG = logging.getLogger(__name__)


RESOURCE_ATTRIBUTE_MAP = {
    'providerports': {
        'id': {'allow_post': False, 'allow_put': False,
               'is_visible': True},
        'name': {'allow_post': True, 'allow_put': False,
                 'is_visible': True},
        'type': {'allow_post': True, 'allow_put': False,
                 'is_visible': True, 'default': 'bambuk'},
        'tenant_id': {'allow_post': True, 'allow_put': False,
                      'is_visible': True, 'default': None},
        'port_id': {'allow_post': True, 'allow_put': False,
                    'is_visible': True, 'required': True},
        'provider_ip': {'allow_post': True, 'allow_put': False,
                        'is_visible': True, 'default': None},
        'provider_mngt_ip': {'allow_post': True, 'allow_put': False,
                             'is_visible': True, 'default': None},
        'provider': {'allow_post': False, 'allow_put': False,
                     'is_visible': True},
    },
}


class Bambuk(extensions.ExtensionDescriptor):

    """API extension for bambuk."""

    @classmethod
    def get_name(cls):
        return 'bambuk'

    @classmethod
    def get_alias(cls):
        return 'bambuk'

    @classmethod
    def get_description(cls):
        return 'Bambuk Management.'

    @classmethod
    def get_namespace(cls):
        return 'https://wiki.openstack.org'

    @classmethod
    def get_updated(cls):
        return '2017-01-01T00:00:00-00:00'

    @classmethod
    def get_resources(cls):
        """Returns Ext Resources."""
        plural_mappings = resource_helper.build_plural_mappings(
            {}, RESOURCE_ATTRIBUTE_MAP)
        attributes.PLURALS.update(plural_mappings)
        resources = resource_helper.build_resource_info(
            plural_mappings,
            RESOURCE_ATTRIBUTE_MAP,
            'bambuk')
        return resources

    def get_extended_resources(self, version):
        if version == "2.0":
            return RESOURCE_ATTRIBUTE_MAP
        else:
            return {}


class BambukPluginBase(service_base.ServicePluginBase):

    def get_plugin_type(self):
        """Get type of the plugin."""
        return 'bambuk'

    def get_plugin_name(self):
        """Get name of the plugin."""
        return 'bambuk'

    def get_plugin_description(self):
        """Get description of the plugin."""
        return 'Bambuk Management Plugin'

    @abc.abstractmethod
    def create_providerport(self, context, providerport):
        pass

    @abc.abstractmethod
    def update_providerport(self,
                           context,
                           providerport_id,
                           providerport):
        pass

    @abc.abstractmethod
    def get_providerport(self, context, providerport_id, fields=None):
        pass

    @abc.abstractmethod
    def delete_providerport(self, context, providerport_id):
        pass

    @abc.abstractmethod
    def get_providerports(self, context, filters=None, fields=None,
                            sorts=None, limit=None, marker=None,
                            page_reverse=False):
        pass


class ProviderPortNotFound(exceptions.NotFound):
    message = _('Provider Port %(providerport_id)s could not be found.')


class ProviderPortNeutronPortNotFound(exceptions.NotFound):
    message = _('Neutron port not for Provider Port %(providerport_id)s.')


class ProviderPortNeutronPortMultipleFound(exceptions.Conflict):
    message = _('Multiple neutron ports found for Provider Port '
                '%(providerport_id)s.')

class ProviderPortProviderPortMultipleFound(exceptions.Conflict):
    message = _('Multiple provider ports for Provider Port '
                '%(providerport_id)s found.')


class ProviderPortBadDeviceId(exceptions.Conflict):
    message = _('Device id not match (received: %(device_id)s, '
                'neutron port: %(neutron_device_id)s).')