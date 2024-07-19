#!/bin/bash
# Wait for the X server to start
sleep 10

# Set the DISPLAY environment variable
export DISPLAY=:0

# Rotate the display
xrandr --output DSI-1 --rotate left 

