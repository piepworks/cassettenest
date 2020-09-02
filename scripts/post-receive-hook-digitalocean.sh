#!/bin/bash
# https://blog.pythonanywhere.com/87/
# https://www.digitalocean.com/community/tutorials/how-to-set-up-automatic-deployment-with-git-with-a-vps
# I live in ~/repos/cassettenest.git/hooks/post-receive

# Update the live code. The `-f` is to force git to blow away any differences in
# that codebase to what just came in from the git push.
GIT_WORK_TREE=/home/trey/apps/cassettenest git checkout -f

# Go to the live code folder.
cd /home/trey/apps/cassettenest

# Update and run.
docker-compose up -d --build
mkdir -p staticfiles
docker-compose exec -T web python manage.py collectstatic --noinput
docker-compose restart
