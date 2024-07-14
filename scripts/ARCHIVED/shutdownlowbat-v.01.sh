#!/bin/bash
BATTINFO=`acpi -b`
CRITICAL_PERCENTAGE=10
FILE_LOCATION="~/LOW_BATTERY"

if [[ `echo $BATTINFO | grep Discharging` && `echo $BATTINFO | cut -c 25-26 ` -lt $CRITICAL_PERCENTAGE ]]
then
echo `date` >> $FILE_LOCATION
echo "Was forced to shutdown due to low battery status" >> $FILE_LOCATION
echo $BATTINFO >> $FILE_LOCATION
sudo shutdown -h now
fi