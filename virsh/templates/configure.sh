#!/bin/bash
# Run in the host, with the cwd being the root of the guest

#set -x
cat > etc/network/interfaces <<NET
# This file describes the network interfaces available on your system
# and how to activate them. For more information, see interfaces(5).

# The loopback network interface
auto lo
iface lo inet loopback

auto ens3
iface ens3 inet static
    address EXT_ADDRESS_GOES_HERE
    network 10.10.0.0
    netmask 255.255.0.0
    broadcast 10.10.255.255
    gateway 10.10.0.1
    dns-nameservers 10.10.0.1 8.8.8.8
    dns-search cloud.toga.local

auto ens9
iface ens9 inet static
    address IP_ADDRESS1_GOES_HERE
    network 192.168.0.0
    netmask 255.255.240.0
    broadcast 192.168.15.255

auto ens10
iface ens10 inet static
    address IP_ADDRESS2_GOES_HERE
    network 192.168.16.0
    netmask 255.255.240.0
    broadcast 192.168.15.255

NET

cat > etc/hosts <<NET
127.0.0.1   localhost
IP_ADDRESS1_GOES_HERE IP_ADDRESS2_GOES_HERE IP_ADDRESS3_GOES_HERE IP_ADDRESS4_GOES_HERE IP_ADDRESS5_GOES_HERE IP_ADDRESS6_GOES_HERE   VM_NAME_GOES_HERE

# The following lines are desirable for IPv6 capable hosts
::1     ip6-localhost ip6-loopback
fe00::0 ip6-localnet
ff00::0 ip6-mcastprefix
ff02::1 ip6-allnodes
ff02::2 ip6-allrouters
NET

# re-generate the keys. Letting virt-sysprep remove the keys
# is insufficient, and they don't get automatically regenerated
# on boot by Ubuntu. A dpkg-reconfigure fails for some reason,
# and doing a boot-time script is overkill, so just do it now explicitly.
rm etc/ssh/ssh_host_rsa_key etc/ssh/ssh_host_rsa_key.pub >&/dev/null
rm etc/ssh/ssh_host_dsa_key etc/ssh/ssh_host_dsa_key.pub >&/dev/null
rm etc/ssh/ssh_host_ecdsa_key etc/ssh/ssh_host_ecdsa_key.pub >&/dev/null
ssh-keygen -h -N '' -t rsa -f etc/ssh/ssh_host_rsa_key >&/dev/null
ssh-keygen -h -N '' -t dsa -f etc/ssh/ssh_host_dsa_key >&/dev/null
ssh-keygen -h -N '' -t ecdsa -f etc/ssh/ssh_host_ecdsa_key >&/dev/null
