"""Generate an interleaved payload from two lists of input strings."""

from app.services.transformer_cache_service import TransformerCacheService


class PayloadGenerationService:
    """Transform and interleave values using the shared transformer cache."""

    def __init__(self, transformer_cache: TransformerCacheService) -> None:
        self._transformer_cache = transformer_cache

    def generate(self, list_1: list[str], list_2: list[str]) -> list[str]:
        """Transform both lists and return their values interleaved by position."""
        if len(list_1) != len(list_2):
            raise ValueError("Both input lists must have the same length")

        payload: list[str] = []
        for first, second in zip(list_1, list_2, strict=True):
            payload.append(self._transformer_cache.transform(first))
            payload.append(self._transformer_cache.transform(second))
        return payload
