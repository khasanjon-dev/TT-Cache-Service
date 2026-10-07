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

The SQLite database file defaults to `cache.db` in the current working
directory. Set `CACHE_DATABASE_PATH` to choose another file path.

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

The service is available at `http://localhost:8000`. Compose stores the SQLite
database in the persistent `cache_data` volume at `/data/cache.db`; set
`CACHE_DATABASE_PATH` in the Compose environment to change its container path.
The container initializes missing tables when it starts. Stop it with
`docker compose down`; the database volume remains available for the next start.

Check the health endpoint and create/read a payload:

```sh
curl http://localhost:8000/health
curl -X POST http://localhost:8000/payload \
  -H 'Content-Type: application/json' \
  -d '{"list_1":["first string","second string"],"list_2":["other string","another string"]}'
curl http://localhost:8000/payload/<payload_id>
```
