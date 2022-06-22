# Cassette Nest

[![codecov](https://codecov.io/gh/trey/cassettenest/branch/main/graph/badge.svg?token=jRevCZkCfH)](https://codecov.io/gh/trey/cassettenest)

A way for analog photographers to track their film use from box to binder.

[cassettenest.com](http://cassettenest.com)

Copyright &copy; 2016-2021 Trey Labs LLC. All rights reserved.

## Local Setup

1. Create a new a `.env` file based on [the example](example-local.env).
    - Adjust as needed, but you shouldn't need to do anything.
2. `dev/bootstrap`
3. `python manage.py migrate`
4. Import a database dump if you want.

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
- In different Terminal tabs:
    - One tab:
        - `dev/start` (to run Django)
    - Another tab:
        - `dev/tw` (to compile [Tailwind CSS](https://tailwindcss.com/))
