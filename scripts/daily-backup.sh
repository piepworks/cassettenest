#!/bin/bash

# Set variables
now=$(date +"%F")
backup_path="${HOME}/backups"
backup_file="cassettenest_${now}.dump"
file_w_path="${backup_path}/${backup_file}"

# Delete any older backups.
rm ${backup_path}/*.dump 2> /dev/null

# Backup the database.
cd $HOME/apps/cassettenest
/usr/local/bin/docker-compose exec -T db pg_dump --format=custom -U cassette_nest cassette_nest > $file_w_path

# Send backup file to DigitalOcean Space.
s3cmd put $file_w_path s3://cassettenest/backups-daily/${backup_file}.enc -e
