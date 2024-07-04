#!/bin/bash

# Configuration
NOTIFY_METHOD="libnotify"  # Can be "libnotify" or "zenity"

# Function to get battery percentage
get_battery_percentage() {
    upower -i $(upower -e | grep BAT) | grep percentage | awk '{print $2}' | tr -d '%'
}

# Function to check if battery is charging
is_battery_charging() {
    local state=$(upower -i $(upower -e | grep BAT) | grep state | awk '{print $2}')
    [[ "$state" == "charging" ]]
}

# Function to send notification
send_notification() {
    local level=$1
    local message=$2

    if [[ "$NOTIFY_METHOD" == "libnotify" ]]; then
        notify-send -u critical "Battery Alert" "$message"
    elif [[ "$NOTIFY_METHOD" == "zenity" ]]; then
        zenity --warning --text="$message" --no-wrap
    fi
}

# Function to determine check interval
get_check_interval() {
    local level=$1
    if (( level >= 31 && level <= 69 )); then
        echo 300  # 5 minutes
    else
        echo 60   # 1 minute
    fi
}

# Initialize variables to track if notifications have been sent
declare -A notified
notified[10]=false
notified[12]=false
notified[15]=false
notified[20]=false
notified[25]=false
notified[80]=false
notified[85]=false
notified[90]=false
notified[100]=false

# Initialize previous battery level
previous_level=-1

while true; do
    battery_level=$(get_battery_percentage)
    charging=$(is_battery_charging)
    check_interval=$(get_check_interval "$battery_level")

    for threshold in 10 12 15 20 25 80 85 90 100; do
        if [[ $battery_level -eq $threshold ]]; then
            should_notify=false

#            if [[ $charging == true && $threshold -ge 50 && $previous_level -lt $battery_level ]]; then
            if [[ $threshold -ge 50 && $previous_level -lt $battery_level ]]; then
                should_notify=true
#            elif [[ $charging == false && $threshold -lt 50 && $previous_level -gt $battery_level ]]; then
            elif [[ $threshold -lt 50 && $previous_level -gt $battery_level ]]; then
                should_notify=true
            fi

            if [[ $should_notify == true && ${notified[$threshold]} == false ]]; then
                if [[ $threshold -eq 80 || $threshold -eq 85 ]]; then
                    message="Time to stop charging. Stopping at 80% will extend your battery life."
                elif [[ $threshold -eq 90 || $threshold -eq 100 ]]; then
                    message="STOP charging now! Your battery will thank you for it."
                else
                    message="Battery level at ${threshold}%"
                fi

                send_notification "$threshold" "$message"
                notified[$threshold]=true
            fi
        else
            notified[$threshold]=false
        fi
    done

    previous_level=$battery_level
    sleep $check_interval
done