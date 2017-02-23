from neutron.db import model_base

from oslo_log import log as o_log

import sqlalchemy as sa


LOG = o_log.getLogger(__name__)

ACTION_CREATE = 'create'
ACTION_UPDATE = 'update'
ACTION_DELETE = 'delete'
ACTION_ATTACH = 'attach'
ACTION_DETACH = 'detach'

OBJ_TYPE_PORT = 'port'
OBJ_TYPE_SINGLE_PORT = 'single_port'
OBJ_TYPE_SECURITY_GROUP = 'security_group'
OBJ_TYPE_ROUTER = 'router'
OBJ_TYPE_ROUTER_IFACE = 'router_iface'


class BambukUpdateLog(model_base.BASEV2,
                      model_base.HasId,
                      model_base.HasTenant):
    """Define an update log."""

    obj_id = sa.Column(sa.String(length=36))
    obj_type = sa.Column(sa.String(length=36))
    action_type = sa.Column(sa.String(length=36))
    created_at = sa.Column(sa.DateTime)
    nb_retry = sa.Column(sa.SmallInteger)
    last_retry = sa.Column(sa.DateTime)
    next_retry = sa.Column(sa.DateTime)
    extra_id = sa.Column(sa.String(length=36))
    extra_data = sa.Column(sa.String(length=255))


class ProviderPort(model_base.BASEV2,
                   model_base.HasId,
                   model_base.HasTenant):
    """Define an provider port."""

    name = sa.Column(sa.String(length=255), nullable=True)
    port_id = sa.Column(sa.String(length=36), nullable=False)
    provider_ip = sa.Column(sa.String(length=64), nullable=False)
    provider_mgnt_ip = sa.Column(sa.String(length=64), nullable=False)


def get_one_bambuk_update_log(context):
    query = context.session.query(BambukUpdateLog)
    b_log = query.first()
    if not b_log:
        return None
    context.session.delete(b_log)
    context.session.flush()
    return b_log


def delete_bambuk_update_log(context, bambuk_update_log):
    context.session.delete(bambuk_update_log)
