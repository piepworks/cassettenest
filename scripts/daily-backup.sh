#!/bin/bash

# Set variables
now=$(date +"%F_%H-%M-%s")
backup_file="$HOME/backups/cassettenest_$now.json"

# Backup the database.
cd $HOME/apps/cassettenest
docker-compose exec -T web python manage.py dumpdata > $backup_file

# Send backup file to DigitalOcean Space.
s3cmd put $backup_file s3://cassettenest/backups-daily/
