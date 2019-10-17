#!/bin/bash
# This hook is sourced after this virtualenv is activated.

# This file lives in [virtualenvs]/[app]/bin/postactivate

# https://help.pythonanywhere.com/pages/environment-variables-for-web-apps/
set -a; source /home/treypiepmeier/film/film/.env; set +a
