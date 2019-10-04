#!/bin/bash
# https://blog.pythonanywhere.com/87/
# I live in ~/bare-repos/cassettenest.git/hooks/post-receive
GIT_WORK_TREE=/home/treypiepmeier/film git checkout -f

now=$(date +"%F_%H-%M-%s")
backup_file="../backups/cassettenest_$now.json"

cd $HOME/film
export WORKON_HOME=$HOME/.virtualenvs
source /usr/local/bin/virtualenvwrapper.sh
workon film
pip install -r requirements.txt
./manage.py dumpdata > $backup_file
./manage.py collectstatic --noinput
./manage.py migrate --noinput
deactivate

s3cmd put $backup_file s3://cassettenest/backups-code-push/

touch /var/www/app_cassettenest_com_wsgi.py
