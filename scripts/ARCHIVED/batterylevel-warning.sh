#!/bin/bash

CRITICAL_PERCENTAGE=`cat /sys/class/power_supply/BAT0/capacity`
STATUS=`cat /sys/class/power_supply/BAT0/status`
ICON="/usr/share/icons/Paper/512x512/status/battery-low.png"

if [ $STATUS == "Discharging" ]; then
	if [ $CRITICAL_PERCENTAGE -eq 42 ]; then
		notify-send -u critical -t 2000 -i $ICON "You need to charge your battery now!!! It is at $CRITICAL_PERCENTAGE%!!!"
		for play_beep in {1..2}; do $(aplay /home/enchance/Dropbox/Restore/air-horn.wav > /dev/null 2>&1); done
	elif [ $CRITICAL_PERCENTAGE -eq 40 ]; then
		notify-send -u critical -t 2000 -i $ICON "You need to charge your battery now!!! It is at $CRITICAL_PERCENTAGE%!!!"
		for play_beep in {1..2}; do $(aplay /home/enchance/Dropbox/Restore/air-horn.wav > /dev/null 2>&1); done
	elif [ $CRITICAL_PERCENTAGE -eq 38 ]; then
		notify-send -u critical -t 2000 -i $ICON "You need to charge your battery now!!! It is at $CRITICAL_PERCENTAGE%!!!"
		for play_beep in {1..2}; do $(aplay /home/enchance/Dropbox/Restore/air-horn.wav > /dev/null 2>&1); done
	fi
fi
