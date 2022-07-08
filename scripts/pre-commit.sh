#!/bin/sh

# I live in your local `.git/hooks/post-receive`.

venv/bin/python manage.py makemigrations --check --dry-run
