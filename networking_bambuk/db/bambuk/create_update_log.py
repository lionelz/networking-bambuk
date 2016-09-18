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


import datetime

from networking_bambuk.common import log_cursor
from networking_bambuk.db.bambuk import bambuk_db

from oslo_log import log

from oslo_utils import uuidutils


LOG = log.getLogger(__name__)
LOG_CURSOR = log_cursor.LogCursor(5)


def create_bambuk_update_log(context,
                             obj,
                             obj_type,
                             action=bambuk_db.ACTION_UPDATE):
    row = bambuk_db.BambukUpdateLog(
        id=uuidutils.generate_uuid(),
        tenant_id=obj['tenant_id'],
        obj_id=obj['id'],
        obj_type=obj_type,
        action_type=action,
        created_at=datetime.datetime.utcnow(),
        nb_retry=0,
    )
    context.session.add(row)


def awake():
    LOG_CURSOR.awake()
