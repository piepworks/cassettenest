#!/bin/bash
# https://blog.pythonanywhere.com/87/
# I live in ~/repos/cassettenest.git/hooks/post-receive

# Update the live code. The `-f` is to force git to blow away any differences in
# that codebase to what just came in from the git push.
GIT_WORK_TREE=/home/trey/apps/cassettenest git checkout -f

# Set variables
backup_path="${HOME}/apps/cassettenest/backups"

# BACKUP THE DATABASE AND UPDATE THINGS
# -------------------------------------
# Go to the live code folder.
cd $HOME/apps/cassettenest
# Install any new Python dependencies.
docker-compose exec -T web pipenv install --system
# Run a database migration if it's needed.
docker-compose exec -T web python manage.py migrate --noinput
# Actually backup the database.
docker-compose exec -T web python manage.py dbbackup -z
# Process static files (including Sass).
mkdir -p staticfiles
docker-compose exec -T web python manage.py collectstatic --noinput
docker-compose exec -T web python manage.py compress --force
# -------------------------------------

# Find the backup file we just created.
unset -v latest
for file in "$backup_path"/*; do
  [[ $file -nt $latest ]] && latest=$file
done
backup_file=$latest
file_without_path="$(basename ${backup_file})"

# Send backup file to DigitalOcean Space.
s3cmd put $backup_file s3://cassettenest/backups-code-push/${file_without_path}.enc -e
# Delete the backup file from the server when we’re done.
rm $backup_file

# Make sure daily backup script is executable.
chmod +x scripts/daily-backup.sh

# Update and run.
docker-compose down && PADDLE_PUBLIC_KEY=$(cat paddle_public_key.txt) docker-compose up -d --build
