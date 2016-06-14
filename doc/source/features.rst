========
Features
========

Bambuk offers the following virtual network services:

* Layer-2 (switching)

  Native implementation. Replaces the conventional Open vSwitch (OVS)
  agent.

* Layer-3 (routing)

  Native implementation or conventional layer-3 agent. The native
  implementation supports distributed routing, centralized floating IP
  addresses and NAT.

* DHCP

  Currently uses conventional DHCP agent which supports availability zones.

* Metadata

  Currently uses conventional metadata agent.


The following Neutron API extensions will be supported (To review/define):

+----------------------------------+---------------------------+------------+
| Extension Name                   | Extension Alias           | TODO       |
+==================================+===========================+============+
| agent                            | agent                     | In Process |
+----------------------------------+---------------------------+------------+
| Allowed Address Pairs            | allowed-address-pairs     | In Process |
+----------------------------------+---------------------------+------------+
| Auto Allocated Topology Services | auto-allocated-topology   | In Process |
+----------------------------------+---------------------------+------------+
| Availability Zone                | availability_zone         | In Process |
+----------------------------------+---------------------------+------------+
| DHCP Agent Scheduler             | dhcp_agent_scheduler      | In Process |
+----------------------------------+---------------------------+------------+
| Neutron external network         | external-net              | In Process |
+----------------------------------+---------------------------+------------+
| Neutron Extra DHCP opts          | extra_dhcp_opt            | In Process |
+----------------------------------+---------------------------+------------+
| Neutron Extra Route              | extraroute                | In Process |
+----------------------------------+---------------------------+------------+
| Neutron L3 Router                | router                    | In Process |
+----------------------------------+---------------------------+------------+
| Network MTU                      | net-mtu                   | In Process |
+----------------------------------+---------------------------+------------+
| Network Availability Zone        | network_availability_zone | In Process |
+----------------------------------+---------------------------+------------+
| Port Binding                     | binding                   | In Process |
+----------------------------------+---------------------------+------------+
| Provider Network                 | provider                  | In Process |
+----------------------------------+---------------------------+------------+
| Quality of Service               | qos                       | In Process |
+----------------------------------+---------------------------+------------+
| Quota management support         | quotas                    | In Process |
+----------------------------------+---------------------------+------------+
| RBAC Policies                    | rbac-policies             | In Process |
+----------------------------------+---------------------------+------------+
| Security Group                   | security-group            | In Process |
+----------------------------------+---------------------------+------------+
| Port Security                    | port-security             | In Process |
+----------------------------------+---------------------------+------------+
| Subnet Allocation                | subnet_allocation         | In Process |
+----------------------------------+---------------------------+------------+
| Default Subnetpools              | default-subnetpools       | In Process |
+----------------------------------+---------------------------+------------+
| RBAC Policies                    | rbac-policies             | In Process |
+----------------------------------+---------------------------+------------+
| standard-attr-description        | standard-attr-description | In Process |
+----------------------------------+---------------------------+------------+
| Subnet Allocation                | subnet_allocation         | In Process |
+----------------------------------+---------------------------+------------+
| Tag support                      | tag                       | In Process |
+----------------------------------+---------------------------+------------+
| Time Stamp Fields                | timestamp_core            | In Process |
+----------------------------------+---------------------------+------------+

