"""HTTP command-line client for the TT Cache Service."""

import json
import sys
from pathlib import Path
from typing import TextIO

import httpx
from pydantic import ValidationError

from app.api.schemas.payload import PayloadCreateRequest, PayloadCreateResponse
from app.cli.config import CLISettings, parse_cli_settings


def _read_input(settings: CLISettings) -> PayloadCreateRequest:
    if settings.json_input is not None:
        raw_json = settings.json_input
    elif settings.input == "-":
        raw_json = sys.stdin.read()
    elif settings.input is not None:
        raw_json = Path(settings.input).read_text(encoding="utf-8")
    else:
        raise ValueError("provide one of --input or --json")

    try:
        decoded = json.loads(raw_json)
    except json.JSONDecodeError as error:
        raise ValueError(f"invalid JSON input: {error.msg}") from error

    try:
        return PayloadCreateRequest.model_validate(decoded)
    except ValidationError as error:
        details = "; ".join(item["msg"] for item in error.errors())
        raise ValueError(f"invalid payload: {details}") from error


def _write_responses(settings: CLISettings, responses: list[str]) -> None:
    if settings.output == "-":
        output: TextIO = sys.stdout
        output.write("\n".join(responses) + "\n")
        return
    Path(settings.output).write_text("\n".join(responses) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    """Run the CLI and return a process exit code."""
    try:
        settings = parse_cli_settings(argv)
    except SystemExit as error:
        return int(error.code)

    try:
        payload = _read_input(settings)
    except (OSError, ValueError) as error:
        print(f"cache-cli: {error}", file=sys.stderr)
        return 3

    endpoint = f"{str(settings.host).rstrip('/')}/payload"
    responses: list[str] = []
    for _ in range(settings.repeat):
        try:
            response = httpx.post(
                endpoint,
                json=payload.model_dump(mode="json"),
                timeout=10.0,
            )
            response.raise_for_status()
            result = PayloadCreateResponse.model_validate(response.json())
        except (httpx.HTTPError, ValueError, ValidationError) as error:
            print(f"cache-cli: request failed: {error}", file=sys.stderr)
            return 4
        responses.append(result.model_dump_json())

    try:
        _write_responses(settings, responses)
    except OSError as error:
        print(f"cache-cli: cannot write output: {error}", file=sys.stderr)
        return 5
    return 0
