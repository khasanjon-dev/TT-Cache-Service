"""Pydantic Settings and argument parsing for ``cache-cli``."""

import argparse

from pydantic import AnyHttpUrl, Field, ValidationError, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class CLISettings(BaseSettings):
    """Validated configuration for one cache-cli invocation."""

    model_config = SettingsConfigDict(env_prefix="CACHE_CLI_", extra="ignore")

    host: AnyHttpUrl = "http://localhost:8000"
    repeat: int = Field(default=1, ge=1)
    input: str | None = None
    json_input: str | None = None
    output: str = "-"

    @model_validator(mode="after")
    def validate_input_source(self) -> "CLISettings":
        """Require exactly one source for the request JSON."""
        if self.input is not None and self.json_input is not None:
            raise ValueError("--input and --json cannot be used together")
        if self.input is None and self.json_input is None:
            raise ValueError("provide one of --input or --json")
        return self


def _argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cache-cli",
        description="Send payload requests to the TT Cache Service.",
    )
    parser.add_argument("-H", "--host", help="FastAPI server URL")
    parser.add_argument("-r", "--repeat", help="number of identical requests to send")
    parser.add_argument("-i", "--input", help="JSON input file, or - for stdin")
    parser.add_argument(
        "-j", "--json", dest="json_input", help="JSON request body provided directly"
    )
    parser.add_argument("-o", "--output", help="output file, or - for stdout")
    return parser


def parse_cli_settings(argv: list[str] | None = None) -> CLISettings:
    """Parse arguments and validate them with Pydantic Settings."""
    parser = _argument_parser()
    arguments = vars(parser.parse_args(argv))
    provided = {key: value for key, value in arguments.items() if value is not None}
    try:
        return CLISettings(**provided)
    except ValidationError as error:
        details = "; ".join(item["msg"] for item in error.errors())
        parser.error(details)
