
from neutron import context as n_context
from neutron import manager
from neutron.api.v2 import attributes
from neutron.common import topics
from neutron.db import db_base_plugin_v2, securitygroups_db, models_v2
from neutron.plugins.common import constants as p_const
from neutron.plugins.ml2 import managers
from neutron.plugins.ml2 import rpc

from networking_bambuk.common import config
from networking_bambuk.common import port_infos
from networking_bambuk.db.bambuk import bambuk_db

from oslo_log import log
  
from oslo_serialization import jsonutils


LOG = log.getLogger(__name__)


def _extend_port_dict_std_attr_id(res, port):
    res['standard_attr_id'] = port['standard_attr_id']
    return res


def _port_model_hook(context, original_model, query):
    query = query.outerjoin(
        securitygroups_db.SecurityGroupPortBinding,
        (original_model.id ==
        securitygroups_db.SecurityGroupPortBinding.port_id))
    return query


def _port_result_filter_hook(query, filters):
    val = filters and filters.get('security_group_id')
    if not val:
        return query
    sgpb_sg_id = securitygroups_db.SecurityGroupPortBinding.security_group_id
    return query.filter(sgpb_sg_id == val)


class Action(object):

    def __init__(self, log, bambuk_client):
        self._log = log
        self._bambuk_client = bambuk_client
        # Register dict extend port attributes
        db_base_plugin_v2.NeutronDbPluginV2.register_dict_extend_funcs(
            attributes.PORTS, ['_extend_port_dict_std_attr_id'])
        db_base_plugin_v2.NeutronDbPluginV2.register_model_query_hook(
            models_v2.Port,
            'security_group_binding_port',
            '_port_model_hook',
            None,
            '_port_result_filter_hook')
        self._plugin_property = None
        self._notifier = rpc.AgentNotifierApi(topics.AGENT)
        self._type_manager = managers.TypeManager()

    @property
    def _plugin(self):
        if self._plugin_property is None:
            pp = manager.NeutronManager.get_plugin()
            pp._extend_port_dict_std_attr_id = _extend_port_dict_std_attr_id
            pp._port_model_hook = _port_model_hook
            pp._port_result_filter_hook = _port_result_filter_hook
            self._plugin_property = pp
        return self._plugin_property

    def _update(self, table, key, value, vms):
        self._bambuk_client.update({
            'table': table,
            'key': key,
            'value': value,
            }, vms)

    def _delete(self, table, key):
        self._bambuk_client.delete({
            'table': table,
            'key': key
        })

    def _get_vms(self, ports, exclude_ids=None):
        vms = set()
        for port in ports:
            if exclude_ids and port['id'] in exclude_ids:
                continue 
            binding_profile = port['binding:profile']
            if 'provider_mgnt_ip' in binding_profile:
                vms.add(binding_profile['provider_mgnt_ip'])
        return vms

    def process(self):
        pass


TUNNEL_TYPES = {'vxlan': 'bambuk_vxlan'}


def get_port_binding(port):
    binding_profile = port['binding:profile']
    if 'provider_mgnt_ip' not in binding_profile:
        return None, None, None

    host_id = port['binding:host_id']
    provider_mgnt_ip = binding_profile['provider_mgnt_ip']
    if 'provider_data_ip' in binding_profile:
        provider_data_ip = binding_profile['provider_data_ip']
    else:
        provider_data_ip = provider_mgnt_ip

    return host_id, provider_mgnt_ip, provider_data_ip


class PortUpdateAction(Action):

    def process(self):
        LOG.debug('PortUpdateAction %s' % self._log)
        ctx = n_context.get_admin_context()

        # retrieve the port
        port = self._plugin.get_port(ctx, self._log['obj_id'])

        host_id, provider_mgnt_ip, provider_data_ip = get_port_binding(port)
        if not provider_mgnt_ip:
            return
 
        server_conf = {
            'device_id': host_id,
            'local_ip': provider_data_ip
        }
 
        # get agent state
        agent_state =  self._bambuk_client.state(server_conf, provider_mgnt_ip)
        if not agent_state:
            return
 
        # TODO: add tunnel_types to the port data profile
        # to support other than vxlan
        if config.get_l2_population():
            # create or update the agent
            agent = self._plugin.create_or_update_agent(
                ctx, agent_state)
            LOG.debug(agent)
            agents = self._plugin.get_agents(
                ctx,
                filters={
                    'agent_type': [agent_state['agent_type']],
                    'host': [host_id]
                }
            )
            LOG.debug(agents)
            if not agents or len(agents) == 0:
                return
     
        #the other port of the network
        other_ports = self._plugin.get_ports(
            ctx,
            filters={'network_id': [port['network_id']]}
        )
        LOG.debug(port['network_id'])
        LOG.debug(other_ports)
        endpoints = []
        for op in other_ports:
            if port['id'] == op['id']:
                port_db = op
            else:
                op_h, op_mgnt_ip, op_data_ip = get_port_binding(
                    port)
                tunnel = {
                    'ip_address': op_data_ip,
                    'host': op_h,
                    'udp_port': p_const.VXLAN_UDP_PORT,
                }
                # TODO: support other types from port data profile
                tunnel_type = 'vxlan'
                tunnels = None
                for endpoint in endpoints:
                    if endpoint['tunnel_type'] == tunnel_type:
                        tunnels = endpoint['tunnels']
                if tunnels:
                    tunnels.append(tunnel)
                else:
                    endpoints.append({
                        'tunnels': [tunnel],
                        'tunnel_type': tunnel_type
                    })

        for tunnel_type in agent_state['configurations']['tunnel_types']:
            if tunnel_type in TUNNEL_TYPES:
                driver = self._type_manager.drivers.get(
                    TUNNEL_TYPES[tunnel_type])
                LOG.debug("driver: %s" % driver)
                if driver:
                    tunnel = driver.obj.add_endpoint(provider_data_ip,
                                                     host_id)
                    # Notify all other listening agents
                    self._notifier.tunnel_update(ctx,
                                                 tunnel.ip_address,
                                                 tunnel_type)
                    # get the relevant tunnels entry
                    entry = {'tunnels': driver.obj.get_endpoints()}
                    LOG.debug("entry: %s" % entry)
                    entry['tunnel_type'] = tunnel_type
                    LOG.info('entry %s' % entry)
                    endpoints.append(entry)
        port_info = port_infos.BambukPortInfo(port_db, other_ports, endpoints)
     
        self._bambuk_client.apply(port_info.to_db(), provider_mgnt_ip)
     
        # update all other ports for the maybe new endpoint
        vms = self._get_vms(other_ports, [port['id']])
        update_connect_db = port_info.chassis_db()
        port_info.port_db(update_connect_db)
        self._bambuk_client.update(update_connect_db, vms)


class SecurityGroupUpdateAction(Action):

    def _get_ports_by_sg_id(self, ctx, sg_id):
        with ctx.session.begin(subtransactions=True):
            # retrieve the security group
            sg = self._plugin.get_security_group(ctx, sg_id)
             
            # retrieve the ports
            ports = self._plugin.get_ports(
                ctx, filters={'security_group_id': sg_id})
            return sg, ports

    def process(self):
        LOG.debug('SecurityGroupUpdateAction %s' % self._log)
        # get all the ports connected to the sg
        ctx = n_context.get_admin_context()
        sg, ports  = self._get_ports_by_sg_id(ctx, self._log['obj_id'])
        vms = self._get_vms(ports)
             
        self._bambuk_client.update(
            {
                'table': 'secgroup',
                'key': sg['id'],
                'value': jsonutils.dumps(sg)
            }, vms)


ACTIONS_CLASS = {
    bambuk_db.OBJ_TYPE_PORT: PortUpdateAction,
    bambuk_db.OBJ_TYPE_SECURITY_GROUP: SecurityGroupUpdateAction,
}