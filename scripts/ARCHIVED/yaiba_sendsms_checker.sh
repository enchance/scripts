#!/bin/bash

# Credentials
user="ascend23_yaiba"
password="=XMHS^502Z,HZF:qTX$%"
host="localhost"
db_name="ascend23_yaiba"

# Array of dbs to back up
dblist=('ascend23_goku' 'ascend23_yaiba')

# Set default file permissions
umask 177

# SCAN FOR OLD SMS AND MARK IT AS SENT AUTOMATICALLY (even if not)
# --------------------------------------------------------

mysql --user=$user --password=$password --host=$host --database=$db_name --execute="DELETE FROM agi_sendsms WHERE created < DATE_SUB(NOW(), INTERVAL 3 DAY) AND agi_sendsms.is_complete = 1;"

# --------------------------------------------------------
# All done! :)



