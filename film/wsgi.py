"""
WSGI config for film project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/howto/deployment/wsgi/

I live here: https://www.pythonanywhere.com/web_app_setup/
"""

import os
import sys
from django.core.wsgi import get_wsgi_application
from dotenv import load_dotenv

# https://help.pythonanywhere.com/pages/environment-variables-for-web-apps/
project_folder = os.path.expanduser('~/film/film')
load_dotenv(os.path.join(project_folder, '.env'))

path = '/home/treypiepmeier/film'
if path not in sys.path:
    sys.path.append(path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'film.settings'

application = get_wsgi_application()
