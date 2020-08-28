#!/bin/bash

### Use only after reinstall of image

BOOT_DIR="$1"

[ -z "$BOOT_DIR" ] && echo "usage: $0 <boot_dir> : Eg $0 /Volumes/boot " >&2 && exit 1

cd $BOOT_DIR
touch ssh

echo "dtoverlay=dwc2" >>  config.txt
sed -i '.bak' 's/rootwait/rootwait modules-load=dwc2,g_ether/' cmdline.txt
