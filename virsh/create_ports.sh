#!/bin/bash

# short_source prints out the current location of the caller in a way
# that strips redundant directories. This is useful for PS4 usage.
function short_source {
    saveIFS=$IFS
    IFS=" "
    called=($(caller 0))
    IFS=$saveIFS
    file=${called[2]}
    file=${file#$RC_DIR/}
    printf "%-40s " "$file:${called[1]}:${called[0]}"
}


NET_ID=861ed60d-2d5d-42e5-99d9-c5f0becdb4ed
SUBNET_ID=7e959d2d-e5a5-4cc8-bbe9-4a0c43bdee3f
NB=150

# delete all existing provider ports
PORT_LIST=`neutron providerport-list -F id -f value`
for p in ${PORT_LIST}; do
  neutron providerport-delete ${p}
done

# delete all existing neutron ports
PORT_LIST=`neutron port-list -F id -f value --device-owner="compute:nova"`
for p in ${PORT_LIST}; do
  neutron port-delete ${p}
done

# create NB neutron port
II=101
while [ $II -le $((NB+100)) ]; do
  neutron port-create --device-owner="compute:nova" --fixed-ip subnet_id=${SUBNET_ID},ip_address=10.0.0.${II} ${NET_ID}
  II=$(($II+1))
done

# create NB provider port
PORT_LIST=`neutron port-list --device-owner="compute:nova" -F id -f value`
II=1
for p in ${PORT_LIST}; do
  ip=10.10.21.${II}
  neutron port-update --device-id=vm${II}  --binding:host_id=vm${II} ${p}
  neutron providerport-create --name=vm${II} --provider-ip ${ip} --provider-mgnt-ip ${ip} ${p}
  II=$(($II+1))
done
