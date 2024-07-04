#!/bin/bash

# Configuration
CHECK_INTERVAL=60  # Check interval in seconds
NOTIFY_METHOD="libnotify"  # Can be "libnotify" or "zenity"

# Function to get battery percentage
get_battery_percentage() {
    upower -i $(upower -e | grep BAT) | grep percentage | awk '{print $2}' | tr -d '%'
}

# Function to send notification
send_notification() {
    local level=$1
    local message="Battery level is at ${level}%"
    
    if [[ "$NOTIFY_METHOD" == "libnotify" ]]; then
        notify-send -u critical "Battery Alert" "$message"
    elif [[ "$NOTIFY_METHOD" == "zenity" ]]; then
        zenity --warning --text="$message" --no-wrap
    fi
}

# Initialize variables to track if notifications have been sent
declare -A notified
notified[15]=false
notified[20]=false
notified[25]=false
notified[32]=false
notified[34]=false
notified[36]=false
notified[38]=false
notified[40]=false
notified[75]=false
notified[80]=false
notified[90]=false
notified[100]=false

while true; do
    battery_level=$(get_battery_percentage)
    
    for threshold in 15 20 25 32 34 36 38 40 75 80 90 100; do
        if [[ $battery_level -eq $threshold && ${notified[$threshold]} == false ]]; then
            send_notification $threshold
            notified[$threshold]=true
        elif [[ $battery_level -ne $threshold ]]; then
            notified[$threshold]=false
        fi
    done
    
    sleep $CHECK_INTERVAL
done