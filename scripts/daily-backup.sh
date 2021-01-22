#!/bin/bash

# Set variables
now=$(date +"%F_%H-%M-%s")
backup_file="$HOME/backups/cassettenest_$now.sql.gz"

# Backup the database.
cd $HOME/apps/cassettenest
/usr/local/bin/docker-compose exec -T db pg_dump -U cassette_nest cassette_nest | gzip > $backup_file

# Send backup file to DigitalOcean Space.
s3cmd put $backup_file s3://cassettenest/backups-daily/ -e
# Delete the backup file from the server when we’re done.
rm $backup_file
