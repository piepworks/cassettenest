# Cassette Nest

[![codecov](https://codecov.io/gh/trey/cassettenest/branch/main/graph/badge.svg?token=jRevCZkCfH)](https://codecov.io/gh/trey/cassettenest)

A way for analog photographers to track their film use from box to binder.

[cassettenest.com](http://cassettenest.com)

Copyright &copy; 2016-2021 Trey Labs LLC. All rights reserved.

## Local Setup

1. Create a new a `.env` file based on [the example](example-local.env).
    - Adjust as needed, but you shouldn't need to do anything.
2. `dev/build`
3. `dev/run python manage.py migrate`
4. Import a database dump if you want.
    - If not, run `dev/run python manage.py createsuperuser`.

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

```shell
dev/server
```

If you want to use [Browsersync](https://www.browsersync.io)…

- `npm i -g browser-sync`

Then you can just run…

```shell
dev/browsersync
```

…or just…

```shell
dev/start
```

… to start the server as well as Browsersync.
