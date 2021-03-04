#!/bin/bash
# https://blog.pythonanywhere.com/87/
# I live in ~/repos/cassettenest.git/hooks/post-receive

# Update the live code. The `-f` is to force git to blow away any differences in
# that codebase to what just came in from the git push.
GIT_WORK_TREE=/home/trey/apps/cassettenest git checkout -f

# Set variables
now=$(date +"%F_%H-%M-%s")
backup_path="${HOME}/backups"
backup_file="cassettenest_${now}.dump"
file_w_path="${backup_path}/${backup_file}"

# BACKUP THE DATABASE AND UPDATE THINGS
# -------------------------------------
# Go to the live code folder.
cd $HOME/apps/cassettenest
# Install any new Python dependencies.
docker-compose exec -T web pipenv install --system
# Run a database migration if it's needed.
docker-compose exec -T web python manage.py migrate --noinput
# Actually backup the database.
docker-compose exec -T db pg_dump --format=custom -U cassette_nest cassette_nest > $file_w_path
# Process static files (including Sass).
mkdir -p staticfiles
docker-compose exec -T web python manage.py collectstatic --noinput
docker-compose exec -T web python manage.py compress --force
# -------------------------------------

# Send backup file to DigitalOcean Space.
s3cmd put $file_w_path s3://cassettenest/backups-code-push/${backup_file}.enc -e
# Delete the backup file from the server when we’re done.
rm $file_w_path

# Make sure daily backup script is executable.
chmod +x scripts/daily-backup.sh

# Update and run.
docker-compose down && PADDLE_PUBLIC_KEY=$(cat paddle_public_key.txt) docker-compose up -d --build
