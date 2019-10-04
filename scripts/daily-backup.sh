#!/bin/bash
now=$(date +"%F_%H-%M-%s")
backup_file="../backups/cassettenest_$now.json"

cd $HOME/film
export WORKON_HOME=$HOME/.virtualenvs
source /usr/local/bin/virtualenvwrapper.sh
workon film
./manage.py dumpdata > $backup_file
deactivate

s3cmd put $backup_file s3://cassettenest/backups-daily/
