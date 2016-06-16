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


from networking_bambuk.rpc import bambuk_rpc


class ClientBambukRpc(bambuk_rpc.BambukRpc):

    def agent_state(self, server_conf):
        pass

    def cleanup(self):
        pass

    def apply(self, vm_connectivity):
        pass

    def update(self, vm_connectivity_update):
        pass

    def obj_version(self):
        pass

class AgentBambukRpc(bambuk_rpc.BambukRpc):

    def agent_state(self, server_conf):
        pass

    def cleanup(self):
        pass

    def apply(self, vm_connectivity):
        pass

    def update(self, vm_connectivity_update):
        pass

    def obj_version(self):
        pass
