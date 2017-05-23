#!/bin/bash
. ./vm_scripts_common.sh

TMP_PATH=$SCRIPTS_PATH/tmp


VM=$1
SERVER_NUM=$2
IP_SUFFIX=$3

if [ -z "$VM" -o -z "$IP_SUFFIX" -o "$VM" == "-h" ]; then
  echo Please supply name, server number and IP suffix for the new VM >&2
  echo   e.g. new_vm100 2 100 >&2
  exit 1
fi

# Remove any leading zeros
IP_SUFFIX=$((10#$IP_SUFFIX))

echo -- Creating configuration script
cp $TEMPLATES_PATH/configure.sh $TMP_PATH/configure.sh.$VM
SCRIPT="s/VM_NAME_GOES_HERE/$VM/g"
SCRIPT="$SCRIPT;s/EXT_ADDRESS_GOES_HERE/10\.10\.2${SERVER_NUM}\.${IP_SUFFIX}/g"
SCRIPT="$SCRIPT;s/IP_ADDRESS1_GOES_HERE/192\.168\.${SERVER_NUM}\.${IP_SUFFIX}/g"
SCRIPT="$SCRIPT;s/IP_ADDRESS2_GOES_HERE/192\.168\.2${SERVER_NUM}\.${IP_SUFFIX}/g"
sed -i -e "$SCRIPT" $TMP_PATH/configure.sh.$VM
chmod a+x $TMP_PATH/configure.sh.$VM

echo -- Creating VM disk file
qemu-img create -q -f qcow2 \
  -o backing_file=$TEMPLATE_DISK $IMAGES_PATH/$VM.qcow2

echo -- Creating VM XML file
python $SCRIPTS_PATH/modify-domain.py --name $VM \
  --new-uuid \
  --disk-path=$IMAGES_PATH/$VM.qcow2 \
  --modify-mac < $TEMPLATE_FILE > $TMP_PATH/$VM.xml

echo -- Creating VM
virsh define $TMP_PATH/$VM.xml
rm $TMP_PATH/$VM.xml

echo -- Modifying VM
#DEBUG_FLAGS='--verbose --x'
virt-sysprep -d $VM \
  --enable customize,udev-persistent-net,bash-history,net-hostname,net-hwaddr,logfiles,utmp,script \
  --hostname $VM \
  --script $TMP_PATH/configure.sh.$VM \
  --quiet \
  $DEBUG_FLAGS

echo -- Removing temp files
rm $TMP_PATH/configure.sh.$VM


