FROM python:3.11.4-slim-bullseye AS prod

ENV PYTHONPATH=/app/buildbot

# Installing curl for healthcheck
RUN apt-get update && apt-get install -y curl

RUN pip install poetry==1.8.2

# Configuring poetry
RUN poetry config virtualenvs.create false
RUN poetry config cache-dir /tmp/poetry_cache

# Copying requirements of a project
COPY README.md pyproject.toml poetry.lock /app/
WORKDIR /app/

# Installing requirements
RUN --mount=type=cache,target=/tmp/poetry_cache poetry install --only main

# Copying actuall application
COPY /buildbot/ /app/buildbot/
RUN --mount=type=cache,target=/tmp/poetry_cache poetry install --only main

CMD ["/usr/local/bin/python", "-m", "buildbot"]

FROM prod AS dev

RUN --mount=type=cache,target=/tmp/poetry_cache poetry install
