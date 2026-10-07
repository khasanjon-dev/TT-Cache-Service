# TT Cache Service

A FastAPI service for caching transformed string payloads. This initial scaffold
provides a health endpoint; service behavior will be added incrementally.

## Development

Requires Python 3.12 or newer. Install the project and development dependencies
in editable mode:

```sh
python -m pip install -e '.[dev]'
uvicorn app.main:app --reload
```

The database URL is configurable through `CACHE_DATABASE_URL`. For local
development, for example:

```sh
export CACHE_DATABASE_URL='postgresql+psycopg://cache_user:password@localhost:5432/cache_db'
```

For local development, initialize any missing tables with:

```sh
python -m app.database
```

Install the command-line client with the project and submit a JSON request:

```sh
python -m pip install -e .
cache-cli --json '{"list_1":["hello"],"list_2":["world"]}'
```

Use `-H`/`--host` for the service URL (`-h`/`--help` displays help), `--repeat`
to send the same request multiple times, `--input` to read JSON from a file or
stdin, and `--output` to write response JSON lines to a file or stdout.

## Docker

Build and start the API with Docker Compose:

```sh
docker compose build
docker compose up
```

The API is available at `http://localhost:8000`; PostgreSQL is available to
local tools on `localhost:5432` and inside Compose on port 5432. Database files
persist in the `postgres_data` volume.
Set `POSTGRES_PASSWORD` in your shell or a local `.env` file to override the
development default. Compose waits for PostgreSQL's health check before starting
the API, which initializes missing tables at startup. Stop the services with
`docker compose down`; the database volume remains available for the next start.

To run tests against PostgreSQL, set `TEST_DATABASE_URL` to a dedicated test
database URL. Test fixtures drop and recreate the application's tables, so do
not point it at a database containing data you need to keep. If unset, tests use
an isolated temporary SQLite database.

Check the health endpoint and create/read a payload:

```sh
curl http://localhost:8000/health
curl -X POST http://localhost:8000/payload \
  -H 'Content-Type: application/json' \
  -d '{"list_1":["first string","second string"],"list_2":["other string","another string"]}'
curl http://localhost:8000/payload/<payload_id>
```
