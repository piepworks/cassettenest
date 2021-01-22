#!/bin/bash

# Download a file specified on the command line.
# https://www.digitalocean.com/docs/spaces/resources/s3cmd-usage/#get-one-file
# It should be decrypted automatically.
# https://www.digitalocean.com/docs/spaces/resources/s3cmd-usage/#encrypt-files
# Something like:
# s3cmd get s3://cassettenest/[folder]/backup.dump.enc backup.dump

# Unzip and restore the database.
# Something like:
# docker-compose exec -T db pg_restore -d [dbname] --clean --create backup.dump
