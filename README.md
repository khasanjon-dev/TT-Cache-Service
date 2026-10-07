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
