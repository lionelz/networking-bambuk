# Copyright (c) 2013 OpenStack Foundation.
# All Rights Reserved.
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

from neutron.db import models_v2
from neutron.db import securitygroups_db


def get_ports_by_secgroup(ctx, security_group_id):
    with ctx.session.begin(subtransactions=True):
        sg_id = securitygroups_db.SecurityGroupPortBinding.security_group_id
        port_id = securitygroups_db.SecurityGroupPortBinding.port_id
        query = ctx.session.query(models_v2.Port)
        query = query.join(securitygroups_db.SecurityGroupPortBinding,
                           port_id == models_v2.Port.id)
        query = query.filter(sg_id == security_group_id)
        return query.all()


