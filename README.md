# Cassette Nest

Manage your inventory of photographic film and keep track of how you use it.

http://cassettenest.com

Copyright &copy; 2018-2019 Arthur L. Piepmeier III. All rights reserved.

## Local Setup

1. `git clone` as `film` and `cd` into it.
    - Why? I just started out building it this way and kind of like it.
2. `mkvirtualenv film`
    - Make sure it's activated before running the next command.
3. `pip install -r requirements.txt`
4. Symlink SQLite database from Dropbox.
    - Something like `ln -s [Dropbox path]/db.sqlite3 .`
5. Symlink `local_settings.py`.
    1. `cd film` (the project folder inside the project, so `film/film`)
    2. `ln -s [Dropbox path]/local_settings.py .`
6. Add `127.0.0.1 film.local` to `/etc/hosts`.
6. Run with the command `./manage.py runserver 0:8000`
    - Then you can look at it with your phone on the local network (`http://[local IP address]:8000`) after you add the IP address to your `ALLOWED_HOSTS` in `film/local_settings.py`.
    - View on your local machine at `http://film.local:8000`.
