# Cassette Nest

A way for analog photographers to track their film use from box to binder.

http://cassettenest.com

Copyright &copy; 2019 Trey Labs LLC. All rights reserved.

## Local Setup

1. `git clone` as `film` and `cd` into it.
    - Why `film`? I just started out building it this way and kind of like it.
2. `mkvirtualenv film`
    - Make sure it's activated before running the next command.
3. `pip install -r requirements.txt`
4. Symlink SQLite database from Dropbox.
    - Something like `ln -s [Dropbox path]/db.sqlite3 .`
5. Symlink `local_settings.py` from Dropbox.
    1. If the file isn't already in Dropbox, create it there based on the code block beneath this list.
    2. `cd film` (the project folder inside the project, so `film/film`)
    3. `ln -s [Dropbox path]/local_settings.py .`
6. `cd ..` back to the base project folder.
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

### `film/local_settings.py`:

```python
import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Database
# https://docs.djangoproject.com/en/2.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

ALLOWED_HOSTS = ['*']
```
