# TT Cache Service

A Python 3.12+ FastAPI service that transforms pairs of string lists, stores
transformation results in PostgreSQL, and returns stable IDs for repeated
payload requests. It includes an HTTP-based `cache-cli` client and a Docker
Compose development setup.

## Features

- FastAPI endpoints with Pydantic request validation and response schemas.
- SQLAlchemy persistence using PostgreSQL and the Psycopg 3 driver.
- Database-backed transformer caching and generated-payload deduplication.
- `cache-cli` for submitting JSON requests over HTTP.
- Unit and integration tests for services, persistence, API, and CLI.
- Docker Compose services for the API and persistent PostgreSQL storage.

## Architecture

Routes validate HTTP input and delegate to services. Services own payload
generation, transformation caching, and request deduplication. Repositories
contain database queries; SQLAlchemy models define persisted records. FastAPI
injects a request-scoped database session from the shared engine/session
factory. The CLI is a separate HTTP client and uses the same Pydantic request
schema as the API.

```text
app/
├── api/          # FastAPI routes, dependencies, and Pydantic schemas
├── cli/          # cache-cli argument/configuration and HTTP client
├── core/         # application settings
├── models/       # SQLAlchemy persistence models
├── repositories/ # database queries and inserts
├── services/     # caching, transformation, and payload logic
├── database.py   # engine, session factory, and database dependency
├── init_db.py    # development schema initialization entry point
└── main.py       # FastAPI application
tests/
├── unit/
└── integration/
```

## Caching and deduplication

Each input string is SHA-256 hashed to form its `input_hash`. The transformer
service looks up that hash before invoking the transformer; a cache hit returns
the stored output and avoids another transformer call. The original input is
also retained so a hash collision can be detected.

The original two lists are serialized as canonical JSON and SHA-256 hashed to
form a `request_hash`. Including both lists and preserving their order and
boundaries means that only the same logical request maps to the same hash. If
that request already exists, the service returns its existing `payload_id`
without regenerating the output.

PostgreSQL unique constraints on `transformer_cache.input_hash` and
`generated_payloads.request_hash` protect both forms of deduplication across
requests and processes. A transaction savepoint handles a competing insert
that loses a uniqueness race. Concurrent cold requests can still call the
transformer more than once before one result is stored; the database keeps only
one cache record. No distributed lock or external cache is used.

## PostgreSQL data model

- `transformer_cache`: unique input hash, original input, transformed output,
  and creation timestamp.
- `generated_payloads`: UUID payload ID primary key, unique request hash,
  generated output stored as JSON, and creation timestamp.

The unique constraints are enforced by PostgreSQL, not by process-local state.
Tables are created with SQLAlchemy metadata during the development/container
startup flow. Schema migrations are not included in this assessment project.

## HTTP API

`GET /health` returns `{"status":"ok"}`.

`POST /payload` accepts two equal-length string lists and returns HTTP 201:

```json
{
  "list_1": ["first string", "second string"],
  "list_2": ["other string", "another string"]
}
```

```json
{"payload_id":"<stable-payload-id>"}
```

`GET /payload/{payload_id}` returns the interleaved transformed output:

```json
{"output":"FIRST STRING, OTHER STRING, SECOND STRING, ANOTHER STRING"}
```

Unequal list lengths are rejected with a 422 validation response. Unknown
payload IDs return 404.

## CLI

Install the project (see local setup below), then use `cache-cli`:

```sh
cache-cli --host http://localhost:8000 \
  --json '{"list_1":["hello"],"list_2":["world"]}'
```

| Option | Purpose |
| --- | --- |
| `-H`, `--host` | FastAPI server URL; defaults to `http://localhost:8000`. |
| `-r`, `--repeat` | Send the same request this many times; must be at least 1. |
| `-i`, `--input` | Read JSON from a file, or `-` for stdin. |
| `-j`, `--json` | Provide the request JSON directly. Mutually exclusive with `--input`. |
| `-o`, `--output` | Write response JSON lines to a file, or `-` for stdout (default). |
| `-h`, `--help` | Show command help. |

Examples for file and standard-stream input/output:

```sh
cache-cli --input request.json --output responses.jsonl
cat request.json | cache-cli --input - --output -
cache-cli --repeat 3 --json '{"list_1":["hello"],"list_2":["world"]}'
cache-cli --help
```

Each successful request writes one JSON response line, so `--repeat` produces
one line per response. CLI settings can also be supplied with the
`CACHE_CLI_` environment prefix (for example `CACHE_CLI_HOST` and
`CACHE_CLI_REPEAT`).

## Local development

Requires Python 3.12+ and a PostgreSQL server. Start the Compose database, then
install the project and development tools in a virtual environment:

```sh
docker compose up -d postgres
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[dev]'
export CACHE_DATABASE_URL='postgresql+psycopg://cache_user:cache_user_dev@localhost:5432/cache_db'
python -m app.init_db
uvicorn app.main:app --reload
```

The API listens on `http://localhost:8000`. The CLI is installed as the
`cache-cli` command. `CACHE_DATABASE_URL` is the application database URL; it
defaults to the local Compose database URL shown above. Set it to match your
PostgreSQL credentials when using another server.

## Docker Compose

Build and start both services:

```sh
docker compose build
docker compose up
```

Compose starts PostgreSQL and waits for its health check before starting the
API. PostgreSQL data persists in the `postgres_data` volume. The API is
available on port 8000; PostgreSQL is published on localhost port 5432. Set
`POSTGRES_PASSWORD` in the shell or a local Compose `.env` file to override the
development default. Stop the services with `docker compose down`; this keeps
the database volume.

## Configuration

| Variable | Used by | Default / purpose |
| --- | --- | --- |
| `CACHE_DATABASE_URL` | API | SQLAlchemy URL; Compose uses `cache_db` as database and `cache_user` as user. |
| `POSTGRES_PASSWORD` | Compose | PostgreSQL password; defaults to a development-only value. |
| `TEST_DATABASE_URL` | Tests | Optional dedicated PostgreSQL test URL. Test fixtures drop and recreate application tables; use a disposable database. |
| `CACHE_CLI_HOST` | CLI | Default service URL, overridden by `--host`. |
| `CACHE_CLI_REPEAT` | CLI | Default request count, overridden by `--repeat`. |
| `CACHE_CLI_INPUT` | CLI | Default input file or `-`, overridden by `--input`. |
| `CACHE_CLI_JSON_INPUT` | CLI | Default direct JSON input, overridden by `--json`. |
| `CACHE_CLI_OUTPUT` | CLI | Default output file or `-`, overridden by `--output`. |

## Tests

Install development dependencies with `python -m pip install -e '.[dev]'`,
then run:

```sh
python -m pytest
ruff check .
```

When `TEST_DATABASE_URL` is set, tests use that PostgreSQL database and clean up
the application tables. Without it, fixtures use a temporary SQLite database
for isolated local tests.

## End-to-end example

With the API running, submit a request and read the generated payload by its
returned ID:

```sh
response=$(cache-cli --json '{"list_1":["hello"],"list_2":["world"]}')
payload_id=$(printf '%s' "$response" | python -c 'import json,sys; print(json.load(sys.stdin)["payload_id"])')
curl "http://localhost:8000/payload/$payload_id"
```

The response output is `HELLO, WORLD`. Repeating the same request returns the
same payload ID.

## Design decisions and trade-offs

- PostgreSQL owns cache and request uniqueness so correctness does not depend
  on a single application process.
- Services and repositories keep business and persistence logic out of route
  handlers; SQLAlchemy sessions are injected and closed per request.
- The simulated transformer is isolated behind a service abstraction so it
  can later be replaced with an external implementation.
- Savepoints let a request recover from a uniqueness race without discarding
  the surrounding transaction. They do not prevent duplicate external calls
  for concurrent cold cache misses.
- Tables are initialized with `create_all` for this small assessment project;
  production schema evolution would need a migration tool and managed secrets.
