#!/bin/bash

. ./vm_scripts_common.sh

VM=$1
if [ -z "$VM" -o "$VM" == "-h" ]; then
  echo Please supply name for the new VM >&2
  exit 1
fi

virsh domstate $VM > /dev/null
if [ $? -ne 0 ]; then
  exit -1
fi
echo -- Stopping VM $VM
virsh destroy $VM >& /dev/null
echo -- Removing VM $VM
virsh undefine --nvram --managed-save $VM
echo -- Removing VM disk file
rm -f $IMAGES_PATH/${VM}.qcow2

