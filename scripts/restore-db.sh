#!/bin/bash

# Download a file specified on the command line.
# s3cmd get s3://cassettenest/[folder]/$1.dump.enc $1.dump

# Restore the database.
# Something like:
# docker-compose exec -T db pg_restore -U [username] -d [dbname] --clean < $1.dump
