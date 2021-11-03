# Pull base image
FROM python:3.8

# Allow this image to get pg_dump v12.
RUN echo "deb http://apt.postgresql.org/pub/repos/apt/ stretch-pgdg main" > /etc/apt/sources.list.d/pgdg.list \
  && curl -sSL https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add -

# Install `pg_dump` so we can use Django Database Backup.
RUN apt-get update \
  && DEBIAN_FRONTEND=noninteractive \
    apt-get install --no-install-recommends --assume-yes \
      postgresql-client-12

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /code

# Install dependencies
COPY Pipfile Pipfile.lock /code/
RUN pip install pipenv && pipenv install --system

# Copy project
COPY . /code/
