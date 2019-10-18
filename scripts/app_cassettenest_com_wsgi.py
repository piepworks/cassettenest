# TODO: Try something like this from PythonAnywhere and use the actual wsgi.py
# file in this project.
#
# I don't know what the `my_wsgi_file` should actually be.


# +++++++++++ CUSTOM WSGI +++++++++++
# If you have a WSGI file that you want to serve using PythonAnywhere, perhaps
# in your home directory under version control, then use something like this:
#
# import sys
#
# path = '/home/treypiepmeier/path/to/my/app
# if path not in sys.path:
#     sys.path.append(path)
#
# from my_wsgi_file import application  # noqa
