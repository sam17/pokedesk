#!/bin/bash

## Use after `init.sh` once only
hostname=$1

ssh-copy-id pi@$hostname.local
scp conf/wpa_supplicant.conf pi@$hostname.local:/tmp/wpa_supplicant.conf
ssh pi@$hostname.local "sudo cp /tmp/wpa_supplicant.conf /etc/wpa_supplicant/wpa_supplicant.conf"
ssh pi@$hostname.local "sudo reboot now"




