import datetime
import oslo_messaging

from networking_bambuk.db.bambuk import bambuk_db

from neutron.common import rpc as n_rpc

from oslo_log import log as o_log

from oslo_utils import uuidutils


LOG = o_log.getLogger(__name__)


target = oslo_messaging.Target(topic='bambuk', version='1.0', exchange='bambuk')
client = n_rpc.get_client(target)

def create_bambuk_update_log(context, obj, obj_type,
                             action=bambuk_db.ACTION_UPDATE,
                             extra_id=None, extra_data=None):
    row = bambuk_db.BambukUpdateLog(
        id=uuidutils.generate_uuid(),
        tenant_id=obj['tenant_id'],
        obj_id=obj['id'],
        obj_type=obj_type,
        action_type=action,
        created_at=datetime.datetime.utcnow(),
        nb_retry=0,
        extra_id=extra_id,
        extra_data=extra_data
    )
    context.session.add(row)
    # send to the queue
    cctxt = client.prepare()
    cctxt.cast(context, 'process_log', log=row)

