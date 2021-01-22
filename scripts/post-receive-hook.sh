#!/bin/bash
# https://blog.pythonanywhere.com/87/
# I live in ~/repos/cassettenest.git/hooks/post-receive

# Update the live code. The `-f` is to force git to blow away any differences in
# that codebase to what just came in from the git push.
GIT_WORK_TREE=/home/trey/apps/cassettenest git checkout -f

# Set variables
now=$(date +"%F_%H-%M-%s")
backup_file="$HOME/backups/cassettenest_$now.sql.gz"

# BACKUP THE DATABASE AND UPDATE THINGS
# -------------------------------------
# Go to the live code folder.
cd $HOME/apps/cassettenest
# Install any new Python dependencies.
docker-compose exec -T web pipenv install --system
# Run a database migration if it's needed.
docker-compose exec -T web python manage.py migrate --noinput
# Actually backup the database.
docker-compose exec -T db pg_dump -U cassette_nest cassette_nest | gzip > $backup_file
# Process static files (including Sass).
mkdir -p staticfiles
docker-compose exec -T web python manage.py collectstatic --noinput
docker-compose exec -T web python manage.py compress --force
# -------------------------------------

# Send backup file to DigitalOcean Space.
s3cmd put $backup_file s3://cassettenest/backups-code-push/ -e
# Delete the backup file from the server when we’re done.
rm $backup_file

# Make sure daily backup script is executable.
chmod +x scripts/daily-backup.sh

# Update and run.
docker-compose down && docker-compose up -d --build
