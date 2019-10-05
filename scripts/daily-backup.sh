#!/bin/bash

# Set variables
now=$(date +"%F_%H-%M-%s")
backup_file="../backups/cassettenest_$now.json"

# BACKUP THE DATABASE
# -------------------
# Go to the live code folder.
cd $HOME/film
# Start up virtualenvwrapper
export WORKON_HOME=$HOME/.virtualenvs
source /usr/local/bin/virtualenvwrapper.sh
# Activate the `film` virtualenv.
workon film
# Actually backup the database.
./manage.py dumpdata > $backup_file
# Deactivate the `film` virtualenv
deactivate
# -------------------

# Send backup file to DigitalOcean.
s3cmd put $backup_file s3://cassettenest/backups-daily/
