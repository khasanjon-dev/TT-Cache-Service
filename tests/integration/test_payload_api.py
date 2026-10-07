from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.database import get_db_session, initialize_database
from app.main import app


@pytest.fixture
def client(tmp_path: Path) -> Iterator[TestClient]:
    engine = create_engine(f"sqlite:///{tmp_path / 'api.sqlite3'}")
    initialize_database(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)

    def override_session() -> Iterator[Session]:
        with factory() as session:
            yield session

    app.dependency_overrides[get_db_session] = override_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    engine.dispose()


def test_post_creates_payload(client: TestClient) -> None:
    response = client.post(
        "/payload",
        json={
            "list_1": ["first string", "second string"],
            "list_2": ["other string", "another string"],
        },
    )

    assert response.status_code == 201
    assert response.json()["payload_id"]


def test_get_returns_formatted_payload(client: TestClient) -> None:
    create_response = client.post(
        "/payload",
        json={
            "list_1": ["first string", "second string"],
            "list_2": ["other string", "another string"],
        },
    )
    payload_id = create_response.json()["payload_id"]

    response = client.get(f"/payload/{payload_id}")

    assert response.status_code == 200
    assert response.json() == {
        "output": "FIRST STRING, OTHER STRING, SECOND STRING, ANOTHER STRING"
    }


def test_repeated_post_returns_same_payload_id(client: TestClient) -> None:
    request_body = {"list_1": ["hello"], "list_2": ["world"]}

    first_response = client.post("/payload", json=request_body)
    second_response = client.post("/payload", json=request_body)

    assert first_response.status_code == second_response.status_code == 201
    assert first_response.json()["payload_id"] == second_response.json()["payload_id"]


def test_post_rejects_unequal_list_lengths(client: TestClient) -> None:
    response = client.post(
        "/payload",
        json={"list_1": ["one"], "list_2": []},
    )

    assert response.status_code == 422


def test_get_returns_404_for_unknown_payload(client: TestClient) -> None:
    response = client.get("/payload/00000000-0000-0000-0000-000000000000")

    assert response.status_code == 404
