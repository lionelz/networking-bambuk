=============
Requierements
=============

Agent solution for Hybrid cloud connectivity  which takes security into account.

*******
General
*******

1. Simple integration/separation with NOVA

2. Performance (throughput) / scalability
 
3. Minimal Resource utilization

 - In the Hyper VMs (memory/cpu): iptables/ovs, vxlan/...
 - In the AZ resource: allow the cascaded run on premises for small AZs
    - Maybe need DHCP/METADATA/... decentralized services

4. Reduce the openstack version dependencies:

 - Why we need an agent on the Hyper VM that depends on the openstack version?

**success merit**

 - Code, ideas or design re-use in "hybrid cloud product"?
 - open source?

********
Security
********

To understand the security requirements, the simple way is to consider an VM running a local agent without container.

1. Management Network
=====================

The Hyper VM should have **read-only** access to the **neutron data** belonging to the next hop of the topological neighbors:
 - The VMs connected to one of its subnets,
 - The routers connected to its subnets,
 - The VMs of the subnets connected to other legs of the routers.

2. Data Network
===============

The Hyper VM should have only network access to the following **network neighbors**:
 - The VMs connected to one of its subnets,
 - The routers connected to its subnets,
 - The VMs of the subnets connected to other legs of the routers (including SNAT access external network).

3. Security Groups
==================

By default, the VMs can not access any other VMs.

To allow communication between network neighbors, security groups rules should be defined:
 - Egress allow rules
 - Ingress allow rules

Issue:
 - When an agent enforces these security groups rules on the Hyper VM, the user may allow all egress and ingress communication.

Firewall As A Service
=====================

**To be defined**

************************
Cross cloud connectivity
************************

Full Mesh
=========

 - Consider ports marked as "remote" for vtep (virtual tunnel end point)
 - Add a route to the VPN servers per providers networks for the remotes AZ

Solution based on BGW
=====================

**Must be discussed** when the BGW designs more elaborated:
 - How to handle the ports marked as "remote"?
 - How to interconnect to the BGW?

=================
Proposed Solution
=================

The proposed solution to cover the requirements includes:
 - a specific neutron agent implementation dedicated for the hybrid cloud (**bambuk agent***): L2, Distributed L3 and may include other local services like DHCP/METADATA (G1, G2, G3, G4)
 - Add a simple RPC communication between Neutron Server and the Hyper VM (S1, G1, G4)
 - ML2 mechanism driver to communicate to the bambuk agent for the L2 Hyper VM connectivity
 - l2 population call back implementation for vxlan termination updates

.. image:: https://raw.githubusercontent.com/lionelz/networking-bambuk/master/doc/source/img/components.png


****************************
Integration with Nova Driver
****************************

- spawn_vm: i.e. set the binding information in the ports to trigger the connectivity


.. image:: https://raw.githubusercontent.com/lionelz/networking-bambuk/master/doc/source/img/spawn_vm.png


- attach_interface: **to be defined**
- power_on: **to be defined** (get agent status)

************
Bambuk Agent
************

- RPC receiver
- Can be based on Dragon Flow for the pipeline and applications. **To be defined**.

***************************************
Provider Security Groups / Firewall Use
***************************************

A solution for HEC/FusionSphere/AWS to ensure the routing domain is to create a provider security group per router or per subnet if not connected to a router.  Each VM that belongs to one of the router network interface belong to this SG. This SG allow only communication from this SG.

******************************************
Simple RPC (push or passive communication)
******************************************

.. image:: https://raw.githubusercontent.com/lionelz/networking-bambuk/master/doc/source/img/bambuk_rpc.png


Bambuk mechanism driver
=======================

Should handle the binding profile on update_network_postcommit method.

l2 population call back
=======================

Should handle all fdb changes: **To be defined**.

L3 core plugin
==============

Support multi-layer router?

Should handle all router changes (**to be defined**):
 - create SG for each router creation
 - add all VMs to this SG when an interface is added
 - ...

Security Groups
===============

Should handle all security group / rule changes.

============
Alternatives
============


**********
Dragonflow
**********

Solution:

 - Based on the container sandbox security.
 - implement DB with ACL based on provider IP (the identification element):

    - Choose a DB implementation that supports ACL and implement it
    - Need to add a list of provider IPs to all DB object.

Why not:

 - Depends on integration of dragonflow in Fusion Sphere
 - The agent depends on Openstack/FS version

**************
Keep DVR as is
**************

Solution:

 - Based on the container sandbox security.

Why not:

 - The agent depends on Openstack/FS version
