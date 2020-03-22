# Cassette Nest

A way for analog photographers to track their film use from box to binder.

[cassettenest.com](http://cassettenest.com)

Copyright &copy; 2018-2020 Trey Labs LLC. All rights reserved.

## Local Setup

1. `git clone` as `film` and `cd` into it.
    - Why `film`? I just started out building it this way and kind of like it.
2. `mkvirtualenv film`
    - Make sure it's activated before running the next command.
3. `pip install -r requirements.txt`
4. Symlink SQLite database from Dropbox.
    - Something like `ln -s [Dropbox path]/db.sqlite3 .`
5. Create a new a `film/film/.env` file based on `film/film/env-example-local.sh`.
    - Adjust as needed, but you shouldn't need to do anything.
6. Add the contents of `film/scripts/postactivate.sh` your virtualenv's `postactivate` script.
    - It should be somewhere like `~/.virtualenvs/film/bin/postactivate`.
    - Adjust the path to point to your new `.env` file.
7. Run the app with the command `./manage.py runserver 0:8000`
    - View on your local machine at `http://localhost:8000`.
    - View on your phone or other computers on the local network at `http://[local IP address]:8000`.

## Development

- Get [stylelint](https://stylelint.io/) setup (only in your editor for now).
    1. `nvm use`
    2. `npm i`.
- Running Python tests
    1. …

Once everything's set up, the next time you want to run it:

1. `cd` into the project folder.
2. `workon film`
3. `./manage.py runserver 0:8000`
