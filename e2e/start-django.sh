#!/usr/bin/env bash

if [[ $CREATE_USER && $CREATE_USER -eq "True" ]]; then
    if [[ $PLAYWRIGHT_USERNAME && $PLAYWRIGHT_PASSWORD && $PLAYWRIGHT_EMAIL ]]; then
        DJANGO_SUPERUSER_USERNAME=$PLAYWRIGHT_USERNAME \
        DJANGO_SUPERUSER_PASSWORD=$PLAYWRIGHT_PASSWORD \
        DJANGO_SUPERUSER_EMAIL=$PLAYWRIGHT_EMAIL \
        venv/bin/python manage.py createsuperuser --noinput
    fi
fi

npm run build
venv/bin/python manage.py collectstatic --noinput
venv/bin/python manage.py color_preference --user $PLAYWRIGHT_USERNAME
DEBUG=False venv/bin/python manage.py runserver
