from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from sqlalchemy import Engine, select
from sqlalchemy.orm import sessionmaker

from app.models import GeneratedPayload
from app.services.generated_payload_service import GeneratedPayloadService
from app.services.payload_generation_service import PayloadGenerationService
from app.services.transformer_cache_service import TransformerCacheService


def test_concurrent_identical_requests_persist_one_payload(db_engine: Engine) -> None:
    if db_engine.dialect.name != "postgresql":
        pytest.skip("PostgreSQL is required for the concurrent insert integration case")

    factory = sessionmaker(bind=db_engine, expire_on_commit=False)
    simultaneous_cache_misses = Barrier(2)

    class ConcurrentTransformer:
        def transform(self, value: str) -> str:
            if value == "first":
                simultaneous_cache_misses.wait(timeout=5)
            return value.upper()

    def request_payload() -> str:
        with factory() as database_session:
            cache = TransformerCacheService(database_session, ConcurrentTransformer())
            generator = PayloadGenerationService(cache)
            service = GeneratedPayloadService(database_session, generator)
            payload_id = service.get_or_create(["first"], ["other"])
            database_session.commit()
            return payload_id

    with ThreadPoolExecutor(max_workers=2) as executor:
        payload_ids = list(executor.map(lambda _: request_payload(), range(2)))

    with factory() as database_session:
        stored_payloads = database_session.scalars(select(GeneratedPayload)).all()
    assert payload_ids[0] == payload_ids[1]
    assert len(stored_payloads) == 1
