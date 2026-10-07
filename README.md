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
