"""Request and response models for payload endpoints."""

from pydantic import BaseModel, model_validator


class PayloadCreateRequest(BaseModel):
    """Two equally sized lists of strings to transform and interleave."""

    list_1: list[str]
    list_2: list[str]

    @model_validator(mode="after")
    def validate_equal_lengths(self) -> "PayloadCreateRequest":
        """Reject requests whose input lists cannot be interleaved pairwise."""
        if len(self.list_1) != len(self.list_2):
            raise ValueError("list_1 and list_2 must have the same length")
        return self


class PayloadCreateResponse(BaseModel):
    """Identifier returned after a payload is generated or reused."""

    payload_id: str


class PayloadResponse(BaseModel):
    """Formatted generated payload output."""

    output: str
