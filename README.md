# Cassette Nest

A way for analog photographers to track their film use from box to binder.

[cassettenest.com](http://cassettenest.com)

Copyright &copy; 2018-2020 Trey Labs LLC. All rights reserved.

## Local Setup

1. Create a new a `.env` file based on [the example](example-local.env).
    - Adjust as needed, but you shouldn't need to do anything.
2. `docker-compose up -d --build`
3. `docker-compose exec web python manage.py migrate`
4. Import a database dump if you want.
    - If not, run `docker-compose exec web python manage.py createsuperuser`.

## Development

- Get [stylelint](https://stylelint.io/) setup (only in your editor for now).
    1. `nvm use`
    2. `npm i`.
- Running Python tests
    1. …

Once everything's set up, the next time you want to run it:

1. `cd` into the project folder.
2. `docker-compose up -d`
