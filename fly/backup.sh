#!/bin/bash -x

# Ensure script stops when commands fail
set -e

mkdir -p /tmp

# Backup & compress our database to the tmp directory
sqlite3 /db/db.sqlite '.backup /tmp/backup.sqlite'
gzip /tmp/backup.sqlite

/usr/local/bin/aws s3 cp /tmp/backup.sqlite.gz s3://cassettenest/sqlite-backups/`date +%F`.sqlite.gz --endpoint=https://nyc3.digitaloceanspaces.com

# Delete the backup so it doesn't get in the way next time
rm /tmp/backup.sqlite.gz
