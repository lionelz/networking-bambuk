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
SUBNET_ID=99273601-7119-4f7c-b380-68b2d6b09c08
NB=200
PREFIXES="10.0.21./10.10.21./vma 10.0.22./10.10.22./vmb"

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

for prefix in ${PREFIXES}; do
  PREFIX_H=`echo ${prefix} | cut -d '/' -f 1`
  PREFIX_P=`echo ${prefix} | cut -d '/' -f 2`
  PREFIX_VM=`echo ${prefix} | cut -d '/' -f 3`
  # create NB neutron port
  II=1
  while [ $II -le $((NB)) ]; do
    ip=${PREFIX_H}${II}
    neutron port-create --device-owner="compute:nova" --device-id=${PREFIX_VM}${II} --binding:host_id=${PREFIX_VM}${II} --fixed-ip subnet_id=${SUBNET_ID},ip_address=${ip} ${NET_ID}
    II=$(($II+1))
  done

  # create NB provider port
  II=1
  while [ $II -le $((NB)) ]; do
    ip=${PREFIX_H}${II}
    ipp=${PREFIX_P}${II}
    p=`neutron port-list --fixed-ips ip_address=${ip} -F id -f value`
    neutron providerport-create --name=${PREFIX_VM}${II} --provider-ip ${ipp} --provider-mgnt-ip ${ipp} ${p}
    II=$(($II+1))
  done
done