# Cassette Nest

[![codecov](https://codecov.io/gh/piepworks/cassettenest/branch/main/graph/badge.svg?token=jRevCZkCfH)](https://codecov.io/gh/piepworks/cassettenest)

A way for analog photographers to track their film use from box to binder.

[cassettenest.com](http://cassettenest.com)

Copyright &copy; 2016-2023 Piepworks LLC. All rights reserved.

## Local Setup

0. Install [Postgres.app](https://postgresapp.com) and set up a new database and user.
    - [Adjust your path for the Postgres app goodies.](https://postgresapp.com/documentation/cli-tools.html)
    - Run the following commands to set up the database and user.
    ```shell
    createuser cassette_nest
    psql
    create database cassette_nest;
    grant postgres to cassette_nest;
    alter user cassette_nest createdb;
    ```
1. Create a new a `.env` file based on [the example](example-local.env).
2. `dev/bootstrap`
3. `python manage.py migrate`
4. `pre-commit install`

## Development

- Get [stylelint](https://stylelint.io/) setup (only in your editor for now).
    - `npm i`
- Running Python tests
    - `dev/test`
        - Just run tests.
    - `dev/coverage`
        - Run tests and generate a coverage report.

---

Once everything's set up, the next time you want to run it:

- Open the Postgres macOS app and start the appropriate database.
- Make sure the virtual environment is activated (usually happens automatically in VS Code).
    `source venv/bin/activate`
- To run the Django server:
    - `dev/start`
- To run both the Django server and compile Tailwind on demand:
    - `npm run start`
- [Update Workbox](https://developer.chrome.com/docs/workbox/modules/workbox-sw/#using-local-workbox-files-instead-of-cdn) ([More info on workbox-cli](https://developer.chrome.com/docs/workbox/modules/workbox-cli/#copylibraries))
    - `npx workbox-cli copyLibraries static/js/vendor/`
    - Update paths in `inventory/templates/sw.js` as needed.

## Deployment

In DigitalOcean settings for the app itself (not the project which includes the database), configure these commands:

"Build Command":

```
npm run build
```

"Run Command":

```
python manage.py collectstatic --noinput
python manage.py migrate --noinput
gunicorn --worker-tmp-dir /dev/shm film.wsgi
```
