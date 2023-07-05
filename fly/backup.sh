#!/bin/bash -x

# Ensure script stops when commands fail.
set -e

mkdir -p /tmp

# Backup & compress our database to the temp directory.
sqlite3 /db/db.sqlite '.backup /tmp/backup.sqlite'
gzip /tmp/backup.sqlite

# Upload backup to S3 using a rolling daily naming scheme.
/usr/local/bin/aws s3 cp /tmp/backup.sqlite.gz s3://litestream-cassettenest/daily/backup-`date +%d`.sqlite.gz --endpoint=https://nyc3.digitaloceanspaces.com

rm /tmp/backup.sqlite.gz
