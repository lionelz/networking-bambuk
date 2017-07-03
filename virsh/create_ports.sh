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


NET_ID=3556d3a3-9210-42ec-b157-62b1f558749d
SUBNET_ID=491569c6-3278-49cb-bb4a-832d89935904
NB=200
PREFIX_HYBRID_1="10.0.2"
PREFIX_HYBRID_2="10.0.3"
PREFIX_MGNT="10.10.2"
PREFIX_DATA="10.10.2"
#PREFIX_DATA="192.168."
LIST_VMS="1/vma 2/vmb 3/vmc 4/vmd 5/vme"

#delete all existing provider ports
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
  SERVER_NUM=`echo ${vm} | cut -d '/' -f 1`
  SERVER_NAME=`echo ${vm} | cut -d '/' -f 2`
  # create the neutron ports
  II=1
  while [ $II -le $((NB)) ]; do
    ip_hybrid_1="${PREFIX_HYBRID_1}${SERVER_NUM}.${II}"
    neutron port-create --device-owner="compute:nova" --device-id=${SERVER_NAME}${II} --binding:host_id=${SERVER_NAME}${II} --fixed-ip subnet_id=${SUBNET_ID},ip_address=${ip_hybrid_1} ${NET_ID}
#     ip_hybrid_2="${PREFIX_HYBRID_2}${SERVER_NUM}.${II}"
#     neutron port-create --device-owner="compute:nova" --device-id=${SERVER_NAME}${II} --binding:host_id=${SERVER_NAME}${II} --fixed-ip subnet_id=${SUBNET_ID},ip_address=${ip_hybrid_2} ${NET_ID}
    II=$(($II+1))
  done

  # create NB provider port
  II=1
  while [ $II -le $((NB)) ]; do
    ip_mgnt="${PREFIX_MGNT}${SERVER_NUM}.${II}"
    ip_data="${PREFIX_DATA}${SERVER_NUM}.${II}"

    ip_hybrid_1="${PREFIX_HYBRID_1}${SERVER_NUM}.${II}"
    p=`neutron port-list --fixed-ips ip_address=${ip_hybrid_1} -F id -f value`
    neutron providerport-create --name=${SERVER_NAME}${II} --provider-ip ${ip_data} --provider-mgnt-ip ${ip_mgnt} ${p}

#     ip_hybrid_2="${PREFIX_HYBRID_2}${SERVER_NUM}.${II}"
#     p=`neutron port-list --fixed-ips ip_address=${ip_hybrid_2} -F id -f value`
#     neutron providerport-create --name=${SERVER_NAME}-${SERVER_NUM}-${II} --provider-ip ${ip_data} --provider-mgnt-ip ${ip_mgnt} ${p}
    II=$(($II+1))
  done
done