#!/bin/bash

# Download a file specified on the command line.
# https://www.digitalocean.com/docs/spaces/resources/s3cmd-usage/#get-one-file
# It should be decrypted automatically.
# https://www.digitalocean.com/docs/spaces/resources/s3cmd-usage/#encrypt-files
# Something like:
# s3cmd get s3://[space]/[folder]/backup.sql.gz

# Unzip and restore the database.
# Something like:
# gunzip -c backup.sql.gz | psql -U [username] [dbname]
