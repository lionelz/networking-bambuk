*************
Requierements
*************

The GOAL is to improve the agent solution for Hybrid cloud connectivity.

-------
General
-------

1. Simple integration/separation with NOVA
2. Performance
3. Minimal Resource utilization
    - In the Hyper VMs (memory/cpu): iptables/ovs, vxlan/...
    - In the AZ resource: maybe the cascaded can run from a on premises for small AZs
         - DHCP/METADATA/... decentralized services?
4. Reduce the openstack version dependencies:
     - Why we need an agent on the Hyper VM that depends on the openstack version?
5. success measurement: TOGA inside
    - Integrate some code
    - And/Or Integrate ideas/design re-use in "hybrid cloud product"

--------
Security
--------

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

To be defined

------------------------
Cross cloud connectivity
------------------------

Full Mesh
=========

 - Take in account for tunneling termination the ports marked as "remote"
 - Add a route to the VPN servers per providers networks for the remotes AZ

Solution based on BGW
=====================

**Must be discussed** when the BGW designs more elaborated:
 - How to handle the ports marked as "remote"?
 - How to interconnect to the BGW?

*****************
Proposed Solution
*****************

The proposed solution to cover the requirements includes:
 - a specific neutron agent implementation dedicated for the hybrid cloud (**bambuk agent***): L2, Distributed L3 and may include other local services like DHCP/METADATA (G1, G2, G3, G4)
 - Add a simple RPC communication between Neutron Server and the Hyper VM (S1, G1, G4)
 - ML2 mechanism driver to communicate to the bambuk agent for the L2 Hyper VM connectivity
 - l2 population call back implementation for 


------------
Bambuk Agent
------------

Based on Dragon Flow: pipeline and application.

----------------------------
plug vif interface with NOVA
----------------------------

 - spawn vm interface
 - attach vif

---------------------------------------
Provider Security Groups / Firewall Use
---------------------------------------

------------------------------------------
Simple RPC (push or passive communication)
------------------------------------------

Bombuk mechanism driver
=======================

l2 population
=============

L3 core plugin
==============


Security Groups
===============


************
Alternatives
************

----------
Dragonflow
----------

Solution:
 - implement DB with ACL based on provider IP (the identification element):
    - Choose a DB implementation that supports ACL and implement it
    - Need to add a list of provider IPs to all DB object.

Why not:
 - Depends in integration of dragonflow in Fusion Sphere

--------------
Keep DVR as is
--------------


