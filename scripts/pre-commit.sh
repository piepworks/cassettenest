#!/bin/sh

# I live in your local `.git/hooks/post-receive`.

docker-compose exec -T web python manage.py makemigrations --check --dry-run
