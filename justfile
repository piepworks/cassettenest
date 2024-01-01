setup-venv:
  python3 -m venv --prompt cn venv
  venv/bin/pip install -U pip setuptools wheel
  venv/bin/python -m pip install -r requirements.txt

bootstrap: setup-venv
  venv/bin/python manage.py migrate
  venv/bin/python manage.py createsuperuser
  pre-commit install

update-venv:
  pip-compile --resolver=backtracking
  venv/bin/python -m pip install -r requirements.txt

shell:
  venv/bin/python manage.py shell

# Run all the tests as fast as possible (other than the standalone Playwright ones: `just playwright`)
pytest:
  pytest -n auto inventory/tests --runplaywright

playwright:
  npx playwright test

# Update all Python packages
update-packages:
  pip-compile --upgrade --resolver=backtracking
  venv/bin/python -m pip install -r requirements.txt

# Update a single package
update-a-package package:
  pip-compile -P {{ package }} --resolver=backtracking
  venv/bin/python -m pip install -r requirements.txt

build-statick-files:
  venv/bin/python manage.py tailwind build
  venv/bin/python manage.py collectstatic --noinput

generate-django-key:
  #!./venv/bin/python
  from django.core.management.utils import get_random_secret_key
  print(get_random_secret_key())

# Run the coverage report
coverage:
  venv/bin/pytest -n auto --cov=inventory --cov-report=html

# Open the coverage report in Firefox
coverage-html:
  open -a firefox -g `pwd`/htmlcov/index.html
