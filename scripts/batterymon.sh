#!/bin/bash

# After modifying this script always run:
#   sudo systemctl daemon-reload && sudo systemctl restart batterymon.service

# Configuration
NOTIFY_METHOD="libnotify"  # Can be "libnotify" or "zenity"
CUTOFF=50

# Function to get battery percentage
get_battery_percentage() {
    local percentage=$(upower -i $(upower -e | grep BAT) | grep percentage | awk '{print $2}' | tr -d '%')
    if [[ -z "$percentage" ]]; then
        echo "Error: Couldn't determine battery percentage" >&2
        echo "-1"
    else
        echo "$percentage"
    fi
}

# Function to check if battery is charging
is_battery_charging() {
    local state=$(upower -i $(upower -e | grep BAT) | grep state | awk '{print $2}')
    if [[ -z "$state" ]]; then
        echo "Error: Couldn't determine battery state" >&2
        echo "-1"  # Return a special value to indicate an error
    elif [[ "$state" == "charging" ]]; then
        echo "1"
    else
        echo "0"
    fi
}

log_message() {
    echo "$(date): $1" >> ~/Dev/repos/scripts/scripts/logs/batterymon_logs.log
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
for key in 5 8 10 14 16 18 20 22 25 80 83 85 87 88 90 100; do
    notified[$key]=false
done

# Initialize previous battery level
previous_level=-1

while true; do
    battery_level=$(get_battery_percentage)
    charging=$(is_battery_charging)
    check_interval=$(get_check_interval "$battery_level")

    if [[ $battery_level -eq -1 ]]; then
        log_message "Error occurred while checking battery level. Skipping this iteration."
        continue
    fi

    if [[ $charging -eq -1 ]]; then
        log_message "Error occurred while checking battery status. Skipping this iteration."
        continue
    fi

    for threshold in 5 8 10 14 16 18 20 22 25 80 83 85 87 88 90 100; do
        if [[ $battery_level -eq $threshold && ${notified[$threshold]} == false ]]; then
            should_notify=false

            if [[ $charging -eq 1 && $threshold -ge $CUTOFF && $previous_level -lt $battery_level ]]; then
                should_notify=true
                charging='charging'
            elif [[ $charging -eq 0 && $threshold -lt $CUTOFF && $previous_level -gt $battery_level ]]; then
                should_notify=true
                charging='discharging'
            fi

#            if [[ ($charging -eq 1 && $threshold -ge $CUTOFF && $previous_level -lt $battery_level) ||
#                  ($charging -eq 0 && $threshold -lt $CUTOFF && $previous_level -gt $battery_level) ]]; then
#                should_notify=true
#            fi

            if [[ $should_notify == true ]]; then
                if [[ $threshold -eq 80 || $threshold -eq 85 ]]; then
                    message="Time to stop charging. Stopping at 80% will extend your battery life."
                elif [[ $threshold -eq 90 || $threshold -eq 100 ]]; then
                    message="STOP charging now! Your battery will thank you for it."
                else
                    message="Battery level at ${threshold}%"
                fi

                send_notification "$threshold" "$message"
                notified[$threshold]=true
                log_message "Status: $charging, Now: $battery_level, Prev: $previous_level"
            fi
        elif [[ $battery_level -ne $threshold ]]; then
            notified[$threshold]=false
        fi
    done

    previous_level=$battery_level
    sleep $check_interval
done