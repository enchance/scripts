#!/bin/bash

# Credentials
user="agipoint_backer"
password="cu!fp2Eb#l=,ZH6nZa#e"
# host="localhost"
backup_path="/home/agipoint/.backups"
# date=$(date +%Y-%m-%d -d "yesterday")
date=$(date +%Y-%m-%d)

# Array of dbs to back up
dblist=('agipoint_goku' 'agipoint_yaiba' 'agipoint_bmo')

# Set default file permissions
umask 177

# START DUMPING DATABASES
# --------------------------------------------------------
# 

for db_name in ${dblist[@]}
do
	start_time=$(date +%s)
	mkdir -p $backup_path/$db_name
	chmod 757 $backup_path/$db_name
	echo "Backing up $db_name now..."
	mysqldump -u $user --password=$password $db_name | gzip -q > $backup_path/$db_name/$db_name-$date.sql.gz
	end_time=$(date +%s)
	elapsed_time=$(expr $end_time - $start_time)
	echo "COMPLETED! $(date -d 00:00:$elapsed_time +%Hh:%Mm:%Ss)"
	echo ""
done

# --------------------------------------------------------
# All done! :)

# Delete files older than 60 days
find $backup_path/*/* -mtime +59 -type f -delete


