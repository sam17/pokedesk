#!/bin/bash
# Log file
LOGFILE="/home/pi/kiosk.log"

# Function to log messages
log() {
    echo "$(date +'%Y-%m-%d %H:%M:%S') - $1" >> "$LOGFILE"
}

# Wait for the page to load
sleep 10

log "Script started"

# Function to scroll down slowly
scroll_down() {
    for ((i = 0; i < 150; i++)); do
        xdotool key --clearmodifiers Down
        sleep 0.4
    done
    log "Scrolled down"
}

# Function to scroll up slowly
scroll_up() {
    for ((i = 0; i < 150; i++)); do
        xdotool key --clearmodifiers Up
        sleep 0.4
    done
    log "Scrolled up"
}

# Ensure Chromium is the active window
while true; do
    # Get the window ID of Chromium
    WINDOW_ID=$(xdotool search --onlyvisible --class "Chromium" | head -1)
    if [ -n "$WINDOW_ID" ]; then
        # Activate the Chromium window
        xdotool windowactivate $WINDOW_ID
        log "Activated Chromium window ID $WINDOW_ID"

        # Scroll the page slowly down and up
        scroll_down
        sleep 5
        scroll_up
        sleep 5
    else
        log "Chromium window not found!"
        sleep 5
    fi
done

