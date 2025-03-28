# Cassette Nest

[![codecov](https://codecov.io/gh/piepworks/cassettenest/branch/main/graph/badge.svg?token=jRevCZkCfH)](https://codecov.io/gh/piepworks/cassettenest)

<a href="https://cottonbureau.com/people/piepworks"><img src="https://cottonbureau.com/mockup?vid=9982515&hash=fa91&w=1024" alt="Cassette Nest t-shirt" width="300" height="auto" /></a>

A way for analog photographers to track their film use from box to binder.

[cassettenest.com](http://cassettenest.com)

Copyright &copy; 2016-2025 Piepworks LLC. All rights reserved.

## Local Setup

1. Create a new a `.env` file based on [the example](example-local.env).
2. `just bootstrap`

## Development

- Running Python tests
    - `just pytest`
        - Run all the tests as fast as possible.
    - `just coverage`
        - Run tests and generate a coverage report.
    - `just playwright`
        - Run [Playwright](https://playwright.dev) UI tests.

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

Then set your secrets in one go:

```shell
fly secrets import < fly.env
```

Then you're ready to go live:

```shell
fly deploy --ha=false
```
