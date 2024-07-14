#!/bin/bash

# Credentials
user="backer_upper"
password='d]4jqCq}|36v1/s$Rh=Dvg~9sfx*@93kDDd!0zG4~b=,xkbUZ@/3Nt%E+dlFmV-:'
backup_path="/home/mushroom/.backups"
# date=$(date +%Y-%m-%d -d "yesterday")
date=$(date +%Y-%m-%d)

# Array of dbs to back up
dblist=('pinfigco_ryu' 'pinfigco_taiga' 'pinfigco_astroboy')

# Set default file permissions
umask 177

# START DUMPING DATABASES
# --------------------------------------------------------
# 

for db_name in ${dblist[@]}
do
	start_time=$(date +%s)
	echo "Backing up $db_name now..."
	sudo mysqldump -u $user --password=$password $db_name | gzip -q > $backup_path/$db_name/$db_name-$date.sql.gz
	end_time=$(date +%s)
	elapsed_time=$(expr $end_time - $start_time)
	echo "COMPLETED! $(date -d 00:00:$elapsed_time +%Hh:%Mm:%Ss)"
	echo ""
done

# --------------------------------------------------------
# All done! :)

# Delete files older than 60 days
find $backup_path/*/* -mtime +59 -type f -delete


