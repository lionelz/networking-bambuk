#
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
#


from neutron.db import model_base

from oslo_log import log

import sqlalchemy as sa


LOG = log.getLogger(__name__)

ACTION_UPDATE = 'update'
ACTION_DELETE = 'delete'

OBJ_TYPE_PORT = 'port'
OBJ_TYPE_SINGLE_PORT = 'single_port'
OBJ_TYPE_SECURITY_GROUP = 'security_group'
OBJ_TYPE_ROUTER = 'router'


class BambukUpdateLog(model_base.BASEV2,
                      model_base.HasId,
                      model_base.HasTenant):
    """Define an update port log."""

    obj_id = sa.Column(sa.String(length=36))
    obj_type = sa.Column(sa.String(length=36))
    action_type = sa.Column(sa.String(length=36))
    created_at = sa.Column(sa.DateTime)
    nb_retry = sa.Column(sa.SmallInteger)
    last_retry = sa.Column(sa.DateTime)
    next_retry = sa.Column(sa.DateTime)


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
