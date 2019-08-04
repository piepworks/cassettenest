#!/bin/bash
# https://blog.pythonanywhere.com/87/
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

touch /var/www/app_cassettenest_com_wsgi.py
