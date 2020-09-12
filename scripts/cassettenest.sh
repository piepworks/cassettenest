#!/bin/bash
#
# I live in /usr/local/bin/cassettenest.sh
# Don't forget to `chmod +x` this file!
#
# My counterpart lives in /etc/supervisor/conf.d/cassettenest.conf

cd /home/trey/apps/cassettenest
docker-compose up
