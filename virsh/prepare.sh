#!/bin/bash
. ./vm_scripts_common.sh

cd $SCRIPTS_PATH

if [ "$1" == "-h" ]; then
  echo Supply name of the VM to be used as a template
  exit 1
fi

BASE_VM=${1:-ubuntu16.04-clone}

if [ ! -d tmp ]; then
  if [ -e tmp ]; then
    echo Error: path `pwd`/tmp exists but is not a directory >&2
    exit -1
  fi
  mkdir tmp
fi
echo -n '-- Copying '
cp -v $IMAGES_PATH/$BASE_VM.qcow2 $TEMPLATE_DISK
echo -- Running virt-sysprep on $TEMPLATE_DISK
virt-sysprep --quiet -a $TEMPLATE_DISK
echo -- Sparsifying $TEMPLATE_DISK
virt-sparsify --quiet --in-place $TEMPLATE_DISK
#echo -n '-- Copying '
#cp -v $TEMPLATE_DISK $SCRIPTS_PATH/images/
echo -- Creating VM template XML at: $TEMPLATE_FILE
virsh dumpxml $BASE_VM > $TEMPLATE_FILE

