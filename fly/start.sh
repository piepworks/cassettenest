#!/usr/bin/env bash

# Terminate the script on a first error, disallow unbound variables.
set -eu

# Load cron configuration.
crontab /code/crontab
echo "Cron has been configured." >> /var/log/cron.log

# Start cron as a daemon.
cron
echo "Cron has been started." >> /var/log/cron.log

# For the sake of cron having access to AWS credentials
printf "AWS_ACCESS_KEY_ID=%s\n" $AWS_ACCESS_KEY_ID >> /etc/environment
printf "AWS_SECRET_ACCESS_KEY=%s\n" $AWS_SECRET_ACCESS_KEY >> /etc/environment

# Define storage lifecycle for daily backup bucket
aws s3api put-bucket-lifecycle-configuration \
    --bucket cassettenest \
    --lifecycle-configuration file:///code/fly/spaces-lifecycle.json \
    --endpoint=https://nyc3.digitaloceanspaces.com

if [[ -z "$DB_DIR" ]]; then
    echo "DB_DIR env var not specified - this should be a path of the directory where the database file should be stored"
    exit 1
fi
if [[ -z "$S3_DB_URL" ]]; then
    echo "S3_DB_URL env var not specified - this should be an S3-style URL to the location of the replicated database file"
    exit 1
fi

mkdir -p "$DB_DIR"

litestream restore -if-db-not-exists -if-replica-exists -o "$DB_DIR/db.sqlite" "$S3_DB_URL"

./manage.py collectstatic --noinput
./manage.py migrate --noinput
./manage.py createcachetable

chmod -R a+rwX /db

# Copy our Litestream config to the default location so we don't have to add a
# `-config` argument to every command.
mv /etc/litestream.yml /etc/litestream.yml-example
cp /code/litestream.yml /etc/litestream.yml

exec litestream replicate
