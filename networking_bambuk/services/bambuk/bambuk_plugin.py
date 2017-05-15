import json
import sys
import time
import traceback

from eventlet.green import zmq

from networking_bambuk.db.bambuk import bambuk_db
from networking_bambuk.extensions import bambuk

from neutron import manager
from neutron.db import common_db_mixin

from oslo_log import log as logging

from sqlalchemy.orm import exc
from networking_bambuk.common.config import timefunc


LOG = logging.getLogger(__name__)


class BambukPlugin(common_db_mixin.CommonDbMixin,
                   bambuk.BambukPluginBase):

    supported_extension_aliases = ['bambuk']
    
    @property
    def _core_plugin(self):
        return manager.NeutronManager.get_plugin()

    @timefunc
    def _send(self, host, port, data):
        retry = 0
        data = json.encoder.JSONEncoder().encode((data))
        received = None
        while not received:
            try:
#                 LOG.debug('%d: try to send to %s:%s (%s)' % (
#                     retry, host, port, data))
                context = zmq.Context()
                _socket = context.socket(zmq.REQ)
                _socket.connect("tcp://%s:%d" % (host, port))
                _socket.send(data)
                received = _socket.recv()
            except Exception as e:
                LOG.error(traceback.format_exc())
                LOG.error('%s' % sys.exc_info()[0])
                time.sleep(1)
                if retry == 9:
                    raise e
                retry = retry + 1
            finally:
                _socket.close()

    def _get_vm_conf(self,
                     instance_id,
                     port_id,
                     mgnt_ip,
                     data_ip,
                     mac):
        vm_conf = {
            'host': instance_id,
            'port_id': port_id,
            'mgnt_ip': mgnt_ip,
            'data_ip': data_ip,
            'mac': mac
        }
        return vm_conf

    def _make_providerport_dict(self,
                                providerport_db,
                                neutron_port=None,
                                fields=None):
#         LOG.debug('_make_providerport_dict %s, %s' % (
#             providerport_db, neutron_port))
        res = {
            'id': providerport_db.id,
            'tenant_id': providerport_db.tenant_id,
            'port_id': providerport_db.port_id,
            'name': providerport_db.name,
            'provider_ip': providerport_db.provider_ip,
            'provider_mgnt_ip': providerport_db.provider_mgnt_ip,
        }
        return self._fields(res, fields)

    def _get_neutron_port(self, context, port_id):
        # Get the neutron port
        neutron_ports = self._core_plugin.get_ports(context, 
            filters={'id':[port_id]})
        if not neutron_ports or len(neutron_ports) == 0:
            raise bambuk.ProviderPortNeutronPortNotFound(
                providerport_id=port_id)
        if len(neutron_ports) != 1:
            raise bambuk.ProviderPortNeutronPortMultipleFound(
                providerport_id=port_id)
        return neutron_ports[0]

    @timefunc
    def create_providerport(self, context, providerport):
        p_port = providerport['providerport']
        port_id = p_port.get('port_id')
        
        neutron_port = self._get_neutron_port(context, port_id)
#         LOG.debug('neutron_port %s' % neutron_port)

        tenant_id = neutron_port['tenant_id']

        with context.session.begin(subtransactions=True):
            # create in DB
            pp_db = bambuk_db.ProviderPort(
                id=port_id,
                tenant_id=tenant_id,
                port_id=port_id,
                name=p_port.get('name'),
                provider_ip=p_port.get('provider_ip'),
                provider_mgnt_ip=p_port.get('provider_mgnt_ip'),
            )
            context.session.add(pp_db)
            self._send(
                pp_db.provider_mgnt_ip,
                8080,
                self._get_vm_conf(
                    neutron_port['device_id'],
                    pp_db.port_id,
                    pp_db.provider_mgnt_ip,
                    pp_db.provider_ip,
                    neutron_port['mac_address']
                ))
            self._core_plugin.update_port(
                context,
                port_id,
                {
                    'port': {'binding:profile': {
                        'provider_ip': pp_db.provider_ip,
                        'provider_mgnt_ip': pp_db.provider_mgnt_ip,
                    }}
                }
            )
        return self._make_providerport_dict(pp_db, neutron_port)

    @timefunc
    def update_providerport(self,
                           context,
                           providerport_id,
                           providerport):
        LOG.debug('providerport %s (%s) to update.' % (
            providerport_id, providerport))

        pp_db = self._get_by_id(
            context, bambuk_db.ProviderPort, providerport_id)
        LOG.debug('pp_db %s' % pp_db)

        neutron_port = self._get_neutron_port(context, pp_db.port_id)

        LOG.debug('neutron_port %s' % neutron_port)
        pp = providerport['providerport']
        with context.session.begin(subtransactions=True):
            pp_db.update(pp)
            self._send(
                pp_db.provider_mgnt_ip,
                8080,
                self._get_vm_conf(
                    neutron_port['device_id'],
                    pp_db.port_id,
                    pp_db.provider_mgnt_ip,
                    pp_db.provider_ip,
                    neutron_port['mac_address']
                ))
            self._core_plugin.update_port(
                context,
                providerport_id,
                {
                    'port': {'binding:profile': {
                        'provider_ip': pp_db.provider_ip,
                        'provider_mgnt_ip': pp_db.provider_mgnt_ip
                    }}
                }
            )
        return self._make_providerport_dict(pp_db, neutron_port)

    def get_providerport(self, context, providerport_id, fields=None):
        LOG.debug('get provider port %s.' % providerport_id)
        # hypernet provider port
        try:
            pp_db = self._get_by_id(
                context, bambuk_db.ProviderPort, providerport_id)
        except exc.NoResultFound:
            raise bambuk.ProviderPortNotFound(
                providerport_id=providerport_id)

        # neutron port
        try:
            neutron_port = self._get_neutron_port(context, pp_db.port_id)
        except:
            neutron_port = None
        if not neutron_port:
            LOG.warn('no neutron port for %s.' % pp_db.port_id)

        return self._make_providerport_dict(pp_db, neutron_port, fields)

    def delete_providerport(self, context, providerport_id):
        LOG.debug('removing provider port %s.' % providerport_id)
        # remove from DB
        try:
            pp_db = self._get_by_id(
                context, bambuk_db.ProviderPort, providerport_id)
            with context.session.begin(subtransactions=True):
                context.session.delete(pp_db)
                self._core_plugin.update_port(
                    context,
                    providerport_id,
                    {'port': {'binding:profile': {}}}
                )
        except exc.NoResultFound:
            pass

    def get_providerports(self, context, filters=None, fields=None,
                           sorts=None, limit=None, marker=None,
                           page_reverse=False):
        LOG.debug('get provider ports %s.' % filters)
        # search id hypernet provider port DB
        pps_db = self._get_collection_query(
            context, bambuk_db.ProviderPort,
            filters=filters, sorts=sorts, limit=limit)
        res = []
        # add neutron and provider info
        for pp_db in pps_db:
            try:
                neutron_port = self._get_neutron_port(context, pp_db.port_id)
            except:
                neutron_port = None
            if not neutron_port:
                LOG.warn('no neutron port for %s.' % pp_db.port_id)
            res.append(self._make_providerport_dict(
                pp_db, neutron_port, fields))
        return res