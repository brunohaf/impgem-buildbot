# buildbot

## Poetry

This project uses poetry. It's a modern dependency management
tool.

To run the project use this set of commands:

```bash
poetry install
poetry run python -m buildbot
```

This will start the server on the configured host.

You can find swagger documentation at `/api/docs`.

You can read more about poetry here: https://python-poetry.org/

## Docker

You can start the project with docker using this command:

```bash
docker-compose up --build
```

## Configuration

This application can be configured with environment variables.

You can create `.env` file in the root directory and place all
environment variables here.

All environment variables should start with "BUILDBOT\_" prefix.

For example if you see in your "buildbot/settings.py" a variable named like
`random_parameter`, you should provide the "BUILDBOT_RANDOM_PARAMETER"
variable to configure the value. This behaviour can be changed by overriding `env_prefix` property
in `app.settings.Settings.Config`.

An example of .env file:

```bash
BUILDBOT_RELOAD="True"
BUILDBOT_PORT="8000"
BUILDBOT_ENVIRONMENT="dev"
```

You can read more about BaseSettings class here: https://pydantic-docs.helpmanual.io/usage/settings/

## Pre-commit

To install pre-commit simply run inside the shell:

```bash
pre-commit install
```

pre-commit is very useful to check your code before publishing it.
It's configured using .pre-commit-config.yaml file.

By default it runs:

- black (formats your code);
- mypy (validates types);
- ruff (spots possible bugs);

You can read more about pre-commit here: https://pre-commit.com/

## Running tests

If you want to run it in docker, simply run:

```bash
docker-compose run --build --rm api pytest -vv .
docker-compose down
```

For running tests on your local machine.

2. Run the pytest.

```bash
pytest -vv .
```
