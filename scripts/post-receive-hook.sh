#!/bin/bash
# https://blog.pythonanywhere.com/87/
# I live in ~/bare-repos/cassettenest.git/hooks/post-receive

# Update the live code. The `-f` is to force git to blow away any differences in
# that codebase to what just came in from the git push.
GIT_WORK_TREE=/home/treypiepmeier/film git checkout -f

# Set variables
now=$(date +"%F_%H-%M-%s")
backup_file="../backups/cassettenest_$now.json"

# BACKUP THE DATABASE AND UPDATE THINGS
# -------------------------------------
# Go to the live code folder.
cd $HOME/film
# Start up virtualenvwrapper
export WORKON_HOME=$HOME/.virtualenvs
source /usr/local/bin/virtualenvwrapper.sh
# Activate the `film` virtualenv.
workon film
# Install any new Python dependencies .
pip install -r requirements.txt
# Run a database migration if it's needed
./manage.py migrate --noinput
# Actually backup the database.
./manage.py dumpdata > $backup_file
# Process static files like Sass
./manage.py collectstatic --noinput
# Deactivate the `film` virtualenv
deactivate
# -------------------------------------

# Send backup file to DigitalOcean.
s3cmd put $backup_file s3://cassettenest/backups-code-push/

# Make sure daily backup script is executable.
chmod +x scripts/daily-backup.sh

# Reboot the app
touch /var/www/app_cassettenest_com_wsgi.py
