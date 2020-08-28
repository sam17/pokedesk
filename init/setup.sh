#!/bin/bash

## Use after `init.sh` once only

ssh-copy-id pi@raspberrypi.local





scp conf/wpa_supplicant.conf pi@squirtle.local:/tmp/wpa_supplicant.conf
ssh pi@squirtle.local "sudo cp /tmp/wpa_supplicant.conf /etc/wpa_supplicant/wpa_supplicant.conf"




