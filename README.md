# Cassette Nest

[![codecov](https://codecov.io/gh/piepworks/cassettenest/branch/main/graph/badge.svg?token=jRevCZkCfH)](https://codecov.io/gh/piepworks/cassettenest)

A way for analog photographers to track their film use from box to binder.

[cassettenest.com](http://cassettenest.com)

Copyright &copy; 2016-2023 Piepworks LLC. All rights reserved.

## Local Setup

1. Create a new a `.env` file based on [the example](example-local.env).
2. `dev/bootstrap`
3. `python manage.py migrate`
4. `pre-commit install`

## Development

- Get [stylelint](https://stylelint.io/) setup (only in your editor for now).
    - `npm i`
- Running Python tests
    - `pytest`
        - Just run tests.
    - `dev/coverage`
        - Run tests and generate a coverage report.
    - `pytest inventory/tests --runplaywright`
        - Run all tests, including [Playwright](https://playwright.dev) UI tests.

---

Once everything's set up, the next time you want to run it:

- Make sure the virtual environment is activated (usually happens automatically in VS Code).
    - `source venv/bin/activate`
- To run the Django server:
    - `./manage.py runserver`
- To run both the Django server and compile Tailwind on demand:
    - `npm run start`
- [Update Workbox](https://developer.chrome.com/docs/workbox/modules/workbox-sw/#using-local-workbox-files-instead-of-cdn) ([More info on workbox-cli](https://developer.chrome.com/docs/workbox/modules/workbox-cli/#copylibraries))
    - `npx workbox-cli copyLibraries static/js/vendor/`
    - Update paths in `inventory/templates/sw.js` as needed.

## Deployment

```shell
fly deploy --ha=false
```
