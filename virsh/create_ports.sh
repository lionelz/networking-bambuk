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
NB=3
PREFIX_HYBRID_1="10.0.2"
PREFIX_HYBRID_2="10.0.3"
PREFIX_MGNT="10.10.2"
PREFIX_DATA1="192.168."
PREFIX_DATA2="192.168.2"
#LIST_VMS="1/vma 2/vmb 3/vmc"
LIST_VMS="1/vma"

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

for vm in ${LIST_VMS}; do
  NB=`echo ${vm} | cut -d '/' -f 1`
  NAME=`echo ${vm} | cut -d '/' -f 2`
  # create the neutron ports
  II=1
  while [ $II -le $((NB)) ]; do
    ip_hybrid_1="${PREFIX_HYBRID_1}${NB}\.${II}"
    ip_hybrid_2="${PREFIX_HYBRID_2}${NB}\.${II}"
    neutron port-create --device-owner="compute:nova" --device-id=${PREFIX_VM}${II} --binding:host_id=${PREFIX_VM}${II} --fixed-ip subnet_id=${SUBNET_ID},ip_address=${ip_hybrid_1} ${NET_ID}
    neutron port-create --device-owner="compute:nova" --device-id=${PREFIX_VM}${II} --binding:host_id=${PREFIX_VM}${II} --fixed-ip subnet_id=${SUBNET_ID},ip_address=${ip_hybrid_2} ${NET_ID}
    II=$(($II+1))
  done

  # create NB provider port
  II=1
  while [ $II -le $((NB)) ]; do
    ip_mgnt="${PREFIX_MGNT}${NB}\.${II}"

    ip_hybrid_1="${PREFIX_HYBRID_1}${NB}\.${II}"
    ip_data1="${PREFIX_DATA1}${NB}\.${II}"
    p=`neutron port-list --fixed-ips ip_address=${ip_hybrid_1} -F id -f value`
    neutron providerport-create --name=${PREFIX_VM}${II} --provider-ip ${ip_data1} --provider-mgnt-ip ${ip_mgnt} ${p}

    ip_hybrid_2="${PREFIX_HYBRID_2}${NB}\.${II}"
    ip_data2="${PREFIX_DATA2}${NB}\.${II}"
    p=`neutron port-list --fixed-ips ip_address=${ip_hybrid_2} -F id -f value`
    neutron providerport-create --name=${PREFIX_VM}${II} --provider-ip ${ip_data2} --provider-mgnt-ip ${ip_mgnt} ${p}
    II=$(($II+1))
  done
done