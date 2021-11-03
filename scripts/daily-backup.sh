#!/bin/bash

# Set variables
backup_path="${HOME}/apps/cassettenest/backups"

# Delete any older backups.
rm ${backup_path}/*.dump 2> /dev/null

# Backup the database.
cd $HOME/apps/cassettenest
/usr/local/bin/docker-compose exec -T web python manage.py dbbackup -z

# Find the backup file we just created.
unset -v latest
for file in "$backup_path"/*; do
  [[ $file -nt $latest ]] && latest=$file
done
backup_file=$latest
file_w_path="${backup_path}/${backup_file}"

# Send backup file to DigitalOcean Space.
s3cmd put $file_w_path s3://cassettenest/backups-daily/${backup_file}.enc -e
