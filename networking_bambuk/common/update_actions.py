from neutron import context as n_context
from neutron import manager
from neutron.api.v2 import attributes
from neutron.common import topics
from neutron.db import db_base_plugin_v2
from neutron.db import models_v2
from neutron.db import securitygroups_db
from neutron.extensions import l3
from neutron.extensions import securitygroup as ext_sg
from neutron.plugins.common import constants as p_const
from neutron.plugins.ml2 import managers
from neutron.plugins.ml2 import rpc

from networking_bambuk._i18n import _LE
from networking_bambuk.common import config
from networking_bambuk.common import port_infos
from networking_bambuk.db.bambuk import bambuk_db

from oslo_log import log as o_log

from oslo_serialization import jsonutils

# Defined in neutron_lib.constants
ROUTER_INTERFACE_OWNERS = {
    'network:router_gateway',                # External net port
    'network:router_interface_distributed',  # Internal net port distributed
}

LOG = o_log.getLogger(__name__)


def _extend_dict_std_attr_id(self, res, db_obj):
    res['standard_attr_id'] = db_obj['standard_attr_id']


def _port_model_hook(ctx, original_model, query):
    port_id_col = securitygroups_db.SecurityGroupPortBinding.port_id
    query = query.outerjoin(
        securitygroups_db.SecurityGroupPortBinding,
        original_model.id == port_id_col)
    return query


def _port_result_filter_hook(query, filters):
    val = filters and filters.get('security_group_id')
    if not val:
        return query
    sgpb_sg_id = securitygroups_db.SecurityGroupPortBinding.security_group_id
    return query.filter(sgpb_sg_id == val)


class Action(object):
    """Base class for Action handlers."""

    def __init__(self, log, bambuk_client):
        """Constructor.

        :param log: the bambuk log
        :type log: BambukUpdateLog
        :param bambuk_client: bambuk client used to dispatch messages
        :type bambuk_client: BambukAgentClient
        """
        super(Action, self).__init__()
        self._log = log
        self._bambuk_client = bambuk_client
        # Register dict extend port attributes
        db_base_plugin_v2.NeutronDbPluginV2.register_dict_extend_funcs(
            attributes.PORTS, [_extend_dict_std_attr_id])
        db_base_plugin_v2.NeutronDbPluginV2.register_dict_extend_funcs(
            attributes.NETWORKS, [_extend_dict_std_attr_id])
        db_base_plugin_v2.NeutronDbPluginV2.register_dict_extend_funcs(
            ext_sg.SECURITYGROUPS, [_extend_dict_std_attr_id])
        db_base_plugin_v2.NeutronDbPluginV2.register_model_query_hook(
            models_v2.Port,
            'add_std_attr_id',
            _port_model_hook,
            None,
            _port_result_filter_hook)
        db_base_plugin_v2.NeutronDbPluginV2.register_dict_extend_funcs(
            l3.ROUTERS, [_extend_dict_std_attr_id])
        self._notifier = rpc.AgentNotifierApi(topics.AGENT)
        self._type_manager = managers.TypeManager()

    @property
    def _plugin(self):
        if not hasattr(self, '_plugin_property'):
            pp = manager.NeutronManager.get_plugin()
            pp._extend_dict_std_attr_id = _extend_dict_std_attr_id
            pp._port_model_hook = _port_model_hook
            pp._port_result_filter_hook = _port_result_filter_hook
            self._plugin_property = pp
        return self._plugin_property

    @property
    def _bambuk_plugin(self):
        if not hasattr(self, '_bambuk_plugin_property'):
            pp = manager.NeutronManager.get_service_plugins().get(
                    'bambuk')
            self._bambuk_plugin_property = pp
        return self._bambuk_plugin_property

    @property
    def _l3_plugin(self):
        if not hasattr(self, '_l3_plugin_property'):
            pp = manager.NeutronManager.get_service_plugins().get(
                    p_const.L3_ROUTER_NAT)
            pp._extend_dict_std_attr_id = _extend_dict_std_attr_id
            self._l3_plugin_property = pp
        return self._l3_plugin_property

    @staticmethod
    def _get_vms(ports, exclude_ids=None):
        """
        Get all the vms holding the ports.

        it is possible to specify optional port_ids to exclude
        :param ports: the ports to check if bambuk port
        :param exclude_ids: neutron port ids to exclude
        :type ports: list
        :type exclude_ids: list
        :return: the list of mgnt ips objects associated with the ports
        :rtype: set
        """
        vms = set()
        for port in ports:
            if exclude_ids and port['id'] in exclude_ids:
                continue
            binding_profile = port['binding:profile']
            if 'provider_mgnt_ip' in binding_profile:
                vms.add(binding_profile['provider_mgnt_ip'])
        return vms

    def process(self):
        """Actual worker method."""
        pass

    def _get_provider_port(self, ctx, port):
        """Get the port provider port for a given port."""

        LOG.debug('%s', port)
        binding_profile = port['binding:profile']
        if ('provider_mgnt_ip' in binding_profile and
                'provider_ip' in binding_profile):
            provider_port = {
                'provider_ip': binding_profile['provider_ip'],
                'provider_mgnt_ip': binding_profile['provider_mgnt_ip'],
                'host_id': port.get('binding:host_id', None)
            }
            return provider_port

    def _get_endpoints(self, ctx, ports, port=None):
        """
        Get all the chassis holding the ports.

        it is possible to mark optional port as a special one

        :param ports: the ports to look for
        :param port: 'special' port
        :type ports: list of dict
        :type port: dict
        :return: the chassis objects associated with the ports and the
                 DB representation of the special port
        :rtype: list of dict, dict
        """
        endpoints = []
        port_db = None
#         LOG.debug('ports %s' % ports)
        for _port in ports:
#             LOG.debug('port %s' % _port)
            if port and port['id'] == _port['id']:
                # This is our port
                port_db = _port
            provider_port = self._get_provider_port(ctx, _port)
            if provider_port:
                tunnel = {
                    'ip_address': provider_port['provider_ip'],
                    'host': provider_port['host_id'],
                    'udp_port': p_const.VXLAN_UDP_PORT,
                }
                # TODO(lionelz): support other types from port data profile
                tunnel_type = 'vxlan'
                tunnels = None
                for endpoint in endpoints:  # type: dict
                    if endpoint['tunnel_type'] == tunnel_type:
                        tunnels = endpoint['tunnels']
                if tunnels:
                    tunnels.append(tunnel)
                else:
                    endpoints.append({
                        'tunnels': [tunnel],
                        'tunnel_type': tunnel_type
                    })
        return endpoints, port_db

    def _get_router_and_ports_from_net(self, ctx, network_id):
        """Get rotuer attached to a network and the reachable ports.

        Get the router for the specified network, along with it,
        get the router ports and the reachable ports from the router.
        :param ctx: ctx
        :param network_id: ID of the network to work on
        :type ctx: dict
        :type network_id: str
        :return: rotuer, router ports and reachable ports
        :rtype: dict, list of dict, dict
        """
        router = None
        _router_ports = []
        # Get the routers connected to this network
        routers = self._get_routers_for_net(ctx, network_id)
        if routers and len(routers) > 0:
            # We support only one router per network at the moment
            _router = routers[0]
            if _router['admin_state_up'] and _router['distributed']:
                router = _router
                _router_ports = self._get_ports_from_router(ctx, router)

        router_ports = []
        networks = [network_id, ]
        for port in _router_ports:  # type: dict
            router_ports.append(port)
            networks.append(port['network_id'])
        # Remove duplicates
        networks = list(set(networks))

        # Retrieve all the networks ports
        ports = []
        for network in networks:
            ports += self._get_network_ports(ctx, network)

        return router, router_ports, ports

    def _get_routers_for_net(self, ctx, network_id):
        """Get all the routers connected to the specified network.

        :param ctx: ctx
        :param network_id: ID of the network to work on
        :type ctx: dict
        :type network_id: str
        :return: rotuers connected to the network
        :rtype: list of dict
        """
        routers = []
        if self._l3_plugin is None:
            return routers
        network = self._plugin.get_network(ctx, network_id)
        if not network:
            return routers
        net_ports = self._get_network_ports(ctx, network_id)
        for port in net_ports:
            if port['device_owner'] in ROUTER_INTERFACE_OWNERS:
                routers.append(
                    self._l3_plugin.get_router(ctx, port['device_id']))
        return routers

    def _get_ports_from_router(self, ctx, router):
        """Get all the ports associated with a specific distributed router.

        :param ctx: ctx
        :param router: router object to query
        :type router: dict
        :return: a list of the ports associated with the router
        :rtype: list of dict
        """
        router_ports = []
        if router['distributed']:
            _r_ports = self._plugin.get_ports(
                ctx, filters={'device_id': [router['id']]})
            for port in _r_ports:
                router_ports.append(port)
        return router_ports

    def _get_network_ports(self, ctx, network_id):
        return self._plugin.get_ports(
            ctx, filters={'network_id': [network_id]})


TUNNEL_TYPES = {'vxlan': 'bambuk_vxlan'}


class PortUpdateAction(Action):
    """This is the handler for the Port-update action.

    It informs all the networks that the disconnected
    subnet is not reachable any more, and vice-versa.
    """

    def process(self):
        """Actual worker for informing the relevant network nodes."""
        LOG.debug('PortUpdateAction %s' % self._log)
        ctx = n_context.get_admin_context()

        try:
            # retrieve the port
            port = self._plugin.get_port(ctx, self._log['obj_id'])
        except Exception as e:
            LOG.exception(_LE('Unable to update port for %(log)s: %(ex)s') %
                {'log': self._log['obj_id'], 'ex': e})
            return

        provider_port = self._get_provider_port(ctx, port)
        if not provider_port:
            return

        server_conf = {
            'device_id': provider_port['host_id'],
            'local_ip': provider_port['provider_ip']
        }

        # get agent state
        agent_state = self._bambuk_client.state(
            server_conf, provider_port['provider_mgnt_ip'])
        if not agent_state:
            return

        # TODO(lionelz): add tunnel_types to the port data profile
        #                to support other than vxlan
        if config.l2_population():
            # create or update the agent
            agent = self._plugin.create_or_update_agent(
                ctx, agent_state)
            LOG.debug(agent)
            agents = self._plugin.get_agents(
                ctx,
                filters={
                    'agent_type': [agent_state['agent_type']],
                    'host': [provider_port['host_id']]
                }
            )
            LOG.debug(agents)
            if not agents or len(agents) == 0:
                return

        # TODO(snapiri): At the moment we assume a network is connected
        #                to a single router at most.

        # Read all the reachable networks and the router
        router, router_ports, other_ports = (
            self._get_router_and_ports_from_net(ctx, port['network_id']))

#         LOG.debug(port['network_id'])

        endpoints, port_db = self._get_endpoints(ctx, other_ports, port)
        if port_db:
            other_ports.remove(port_db)
#         LOG.debug("endpoints %s" % endpoints)

        for tunnel_type in agent_state['configurations']['tunnel_types']:
            if tunnel_type in TUNNEL_TYPES:
                driver = self._type_manager.drivers.get(
                    TUNNEL_TYPES[tunnel_type])
#                 LOG.debug("driver: %s" % driver)
                if driver:
                    tunnel = driver.obj.add_endpoint(
                        provider_port['provider_ip'], provider_port['host_id'])
                    # Notify all other listening agents
                    self._notifier.tunnel_update(
                        ctx, tunnel.ip_address, tunnel_type)
                    # get the relevant tunnels entry
                    entry = {'tunnels': driver.obj.get_endpoints()}
#                     LOG.debug('entry: %s' % entry)
                    entry['tunnel_type'] = tunnel_type
#                     LOG.info('entry %s' % entry)
                    endpoints.append(entry)
#         LOG.debug('endpoints %s' % endpoints)
        port_info = port_infos.BambukPortInfo(
            port_db, other_ports, endpoints, router, router_ports)

        self._bambuk_client.apply(
            port_info.to_db(), provider_port['provider_mgnt_ip'])

        # update all other ports for the possible new endpoint
        vms = self._get_vms(other_ports, [port['id']])
        update_connect_db = port_info.chassis_db()
        port_info.port_db(update_connect_db)
        self._bambuk_client.update(update_connect_db, vms)

    def _get_router_and_ports_from_net(self, ctx, network_id):
        # Get all routable networks
        router = None
        # Get the routers connected to this network
        routers = self._get_routers_for_net(ctx, network_id)
        networks = []
        router_ports = []
        if routers:
            if len(routers) > 0:
                # We support only one router per network at the moment
                router = routers[0]
                networks, router_ports = (
                    self._get_ports_from_router(ctx, router)
                )

        networks.append(network_id)
        # Remove duplicates
        networks = list(set(networks))

        # Retrieve all the networks ports
        ports = []
        for network in networks:
            ports += self._get_network_ports(ctx, network)

        return router, router_ports, ports

    def _get_routers_for_net(self, ctx, network_id):
        routers = []
        if self._l3_plugin is None:
            return routers
        network = self._plugin.get_network(ctx, network_id)
        if not network:
            return routers
        net_ports = self._get_network_ports(ctx, network_id)
        for port in net_ports:
            if port['device_owner'] in ROUTER_INTERFACE_OWNERS:
                routers.append(
                    self._l3_plugin.get_router(ctx, port['device_id']))
        return routers

    def _get_ports_from_router(self, ctx, router):
        networks = []
        router_ports = []
        LOG.debug('%s' % router)
        if router['distributed']:
            router_ports = self._plugin.get_ports(
                ctx, filters={'device_id': [router['id']]})
            for port in router_ports:
                networks.append(port['network_id'])
        return networks, router_ports

    def _get_network_ports(self, ctx, network_id):
        return self._plugin.get_ports(
            ctx, filters={'network_id': [network_id]})


class SecurityGroupUpdateAction(Action):
    """Handles SecurityGroup update logs."""

    def _get_ports_by_sg_id(self, ctx, sg_id):
        with ctx.session.begin(subtransactions=True):
            # retrieve the security group
            sg = self._plugin.get_security_group(ctx, sg_id)

            # retrieve the ports
            ports = self._plugin.get_ports(
                ctx, filters={'security_group_id': sg_id})
            return sg, ports

    def process(self):
        """Actual worker for informing the relevant network nodes."""
        LOG.debug('SecurityGroupUpdateAction %s' % self._log)
        # get all the ports connected to the sg
        ctx = n_context.get_admin_context()
        sg, ports = self._get_ports_by_sg_id(ctx, self._log['obj_id'])
        vms = self._get_vms(ports)

        self._bambuk_client.update({
                'table': 'secgroup',
                'key': sg['id'],
                'value': jsonutils.dumps(port_infos.lsecgroup(sg))
        }, vms)


class RouterUpdateAction(Action):
    """This is the handler for the Router-Update log.

    We expect to get called in case the router is enabled/disabled, and
    in each of the cases we inform the nodes on the networks that they
    are all reachable or not from each other.
    """

    @staticmethod
    def _get_port_subnet_id(port):
        f_ips = port.get('fixed_ips', [])
        if len(f_ips) > 0:
            return f_ips[0]['subnet_id']
        return None

    def process(self):
        """Actual worker for informing the relevant network nodes."""
        LOG.debug('RouterUpdateAction %s' % self._log)
        ctx = n_context.get_admin_context()
        router = self._l3_plugin.get_router(ctx, self._log['obj_id'])
        if not router['distributed']:
            return
        # If the router is enabled, just update all the ports
        if router['admin_state_up']:
            ac = RouterIfaceAttachAction(self._log, self._bambuk_client)
            ac.process()
            return

        # So the router is disabled...
        _router_ports = self._get_ports_from_router(ctx, router)
        router_ports = []
        for port in _router_ports:
            router_ports.append(
                (port,
                 self._get_network_ports(ctx, port['network_id'])))

        # Disconnect all networks from each other
        for (port, conneted_ports) in router_ports:
            subnet_id = self._get_port_subnet_id(port)
            if not subnet_id:
                continue
            for (port_2, detached_ports) in router_ports:
                subnet_id_2 = self._get_port_subnet_id(port_2)
                if subnet_id == subnet_id_2:
                    continue
                # Send delete message to the connected ports for
                #  the detached ports
                vms = self._get_vms(conneted_ports)
                endpoints, _ = self._get_endpoints(detached_ports)
                port_info = port_infos.BambukPortInfo(None, detached_ports,
                                                      endpoints,
                                                      router, [port_2])
                self._bambuk_client.delete(port_info.to_db(), vms)


class RouterIfaceAttachAction(Action):
    """This is the handler for the Router-Interface-Attach log.

    It informs all the networks that the newly connected network
    subnet is now reachable from the other networks, and vice-versa.
    """

    def process(self):
        """Actual worker for informing the relevant network nodes."""
        LOG.debug('RouterIfaceAttachAction %s' % self._log)
        ctx = n_context.get_admin_context()

        # Retrieve the router
        router = self._l3_plugin.get_router(ctx, self._log['obj_id'])
        if not router['distributed']:
            return
        # In case the router is not interesting, just return
        if not router['admin_state_up']:
            return

        _router_ports = self._get_ports_from_router(ctx, router)

        # Retrieve all the networks ports
        router_ports = []
        ports = []
        for port in _router_ports:
            router_ports.append(port)
            network_id = port['network_id']
            ports += self._get_network_ports(ctx, network_id)

        LOG.debug(ports)

        endpoints, _ = self._get_endpoints(ctx, ports)
        LOG.debug('endpoints %s' % endpoints)
        port_info = port_infos.BambukPortInfo(None, ports,
                                              endpoints,
                                              router, router_ports)

        # Update all other ports on the possibly new endpoint
        vms = self._get_vms(ports)
        self._bambuk_client.update(port_info.to_db(), vms)


class RouterIfaceDetachAction(Action):
    """This is the handler for the Router-Interface-Detach log.

    It informs all the networks that the disconnected
    subnet is not reachable any more, and vice-versa.
    """

    def process(self):
        """Actual worker for informing the relevant network nodes."""
        LOG.debug('RouterIfaceDetachAction %s' % self._log)
        ctx = n_context.get_admin_context()
        try:
            router = self._l3_plugin.get_router(ctx, self._log['obj_id'])
        except Exception as ex:
            # In case the router does not exist any more, just log and return
            LOG.error('Error occurred: %s', ex)
            return
        if not router['admin_state_up'] or not router['distributed']:
            LOG.debug('Router is not relevant %s' % router['id'])
            return
        try:
            detached_network = self._plugin.get_network(ctx,
                                                        self._log['extra_id'])
        except Exception as ex:
            LOG.error('Error with network: %s', self._log['extra_id'])
            return

        detached_ports = self._get_network_ports(ctx, detached_network['id'])

        _router_ports = self._get_ports_from_router(ctx, router)
        connected_ports = []
        connected_router_ports = []
        detached_router_ports = []
        for port in _router_ports:
            if port['network_id'] == detached_network['id']:
                detached_router_ports.append(port)
                continue
            connected_router_ports.append(port)
            connected_ports += self._get_network_ports(ctx, port['network_id'])

        if len(connected_ports):
            # Disconnect 1
            vms = self._get_vms(connected_ports)
            endpoints, _ = self._get_endpoints(ctx, detached_ports)
            port_info = port_infos.BambukPortInfo(None, detached_ports,
                                                  endpoints,
                                                  None, None)
            # TODO(snapiri): We should also send delete to the lswitch
            self._bambuk_client.delete(port_info.to_db(), vms)

        # Disconnect 2
        vms = self._get_vms(detached_ports)
        endpoints = []
        if len(connected_ports):
            endpoints, _ = self._get_endpoints(ctx, connected_ports)
        port_info = port_infos.BambukPortInfo(None, connected_ports,
                                              endpoints,
                                              router, connected_router_ports)
        self._bambuk_client.delete(port_info.to_db(), vms)


ACTIONS_CLASS = {
    (bambuk_db.OBJ_TYPE_PORT, bambuk_db.ACTION_CREATE):
        PortUpdateAction,
    (bambuk_db.OBJ_TYPE_PORT, bambuk_db.ACTION_UPDATE):
        PortUpdateAction,
    (bambuk_db.OBJ_TYPE_SECURITY_GROUP, bambuk_db.ACTION_CREATE):
        SecurityGroupUpdateAction,
    (bambuk_db.OBJ_TYPE_SECURITY_GROUP, bambuk_db.ACTION_UPDATE):
        SecurityGroupUpdateAction,
    (bambuk_db.OBJ_TYPE_SECURITY_GROUP, bambuk_db.ACTION_DELETE):
        SecurityGroupUpdateAction,
    (bambuk_db.OBJ_TYPE_ROUTER, bambuk_db.ACTION_UPDATE):
        RouterUpdateAction,
    (bambuk_db.OBJ_TYPE_ROUTER_IFACE, bambuk_db.ACTION_ATTACH):
        RouterIfaceAttachAction,
    (bambuk_db.OBJ_TYPE_ROUTER_IFACE, bambuk_db.ACTION_DETACH):
        RouterIfaceDetachAction,
}
