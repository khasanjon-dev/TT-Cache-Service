import json
from io import StringIO
from pathlib import Path
from unittest.mock import Mock

import httpx
import pytest

from app.cli.command import main
from app.cli.config import parse_cli_settings

JSON_INPUT = '{"list_1":["hello"],"list_2":["world"]}'


def response(payload_id: str = "payload-123") -> httpx.Response:
    return httpx.Response(
        201,
        json={"payload_id": payload_id},
        request=httpx.Request("POST", "http://localhost:8000/payload"),
    )


def test_cli_settings_defaults_and_parses_arguments() -> None:
    settings = parse_cli_settings(["--json", JSON_INPUT])

    assert str(settings.host).rstrip("/") == "http://localhost:8000"
    assert settings.repeat == 1
    assert settings.output == "-"

    configured = parse_cli_settings(
        ["--host", "http://cache.local:9000", "--repeat", "3", "--json", JSON_INPUT]
    )
    assert str(configured.host).startswith("http://cache.local:9000")
    assert configured.repeat == 3


@pytest.mark.parametrize(
    "arguments",
    [
        ["--json", JSON_INPUT, "--repeat", "0"],
        ["--json", JSON_INPUT, "--repeat", "not-a-number"],
        ["--input", "request.json", "--json", JSON_INPUT],
        [],
    ],
)
def test_cli_rejects_invalid_configuration(
    arguments: list[str], capsys: pytest.CaptureFixture[str]
) -> None:
    with pytest.raises(SystemExit) as error:
        parse_cli_settings(arguments)

    assert error.value.code == 2
    assert "error:" in capsys.readouterr().err


def test_json_argument_posts_repeatedly_and_writes_responses(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    post = Mock(side_effect=[response("same-id"), response("same-id")])
    monkeypatch.setattr("app.cli.command.httpx.post", post)

    exit_code = main(["--host", "http://test.local", "--repeat", "2", "--json", JSON_INPUT])

    assert exit_code == 0
    assert post.call_count == 2
    assert all(call.args[0] == "http://test.local/payload" for call in post.call_args_list)
    output_lines = capsys.readouterr().out.strip().splitlines()
    assert [json.loads(line)["payload_id"] for line in output_lines] == ["same-id", "same-id"]


def test_input_file_and_output_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    input_file = tmp_path / "request.json"
    output_file = tmp_path / "responses.jsonl"
    input_file.write_text(JSON_INPUT, encoding="utf-8")
    monkeypatch.setattr("app.cli.command.httpx.post", Mock(return_value=response("file-id")))

    exit_code = main(["--input", str(input_file), "--output", str(output_file)])

    assert exit_code == 0
    assert json.loads(output_file.read_text(encoding="utf-8")) == {"payload_id": "file-id"}


def test_stdin_input_and_stdout_output(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr("app.cli.command.sys.stdin", StringIO(JSON_INPUT))
    monkeypatch.setattr("app.cli.command.httpx.post", Mock(return_value=response("stdin-id")))

    exit_code = main(["--input", "-"])

    assert exit_code == 0
    assert json.loads(capsys.readouterr().out) == {"payload_id": "stdin-id"}


def test_invalid_payload_returns_nonzero_without_request(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    post = Mock()
    monkeypatch.setattr("app.cli.command.httpx.post", post)

    exit_code = main(["--json", '{"list_1":["one"],"list_2":[]}'])

    assert exit_code == 3
    assert "invalid payload" in capsys.readouterr().err
    post.assert_not_called()


def test_http_error_returns_nonzero(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    failed_response = httpx.Response(
        503,
        request=httpx.Request("POST", "http://localhost:8000/payload"),
    )
    monkeypatch.setattr("app.cli.command.httpx.post", Mock(return_value=failed_response))

    exit_code = main(["--json", JSON_INPUT])

    assert exit_code == 4
    assert "request failed" in capsys.readouterr().err
