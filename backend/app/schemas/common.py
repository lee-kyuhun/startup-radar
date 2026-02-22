from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ErrorDetail(BaseModel):
    code: str
    message: str


class PaginationMeta(BaseModel):
    current_page: int = 1
    total_pages: int = 0
    total_count: int = 0
    limit: int = 20
    has_prev: bool = False
    has_next: bool = False


class ResponseEnvelope(BaseModel, Generic[T]):
    """Standard API response wrapper."""
    data: T | None = None
    error: ErrorDetail | None = None
    meta: dict[str, Any] | None = None

    @classmethod
    def ok(cls, data: T, meta: dict[str, Any] | None = None) -> "ResponseEnvelope[T]":
        return cls(data=data, error=None, meta=meta)

    @classmethod
    def fail(cls, code: str, message: str) -> "ResponseEnvelope[None]":
        return cls(data=None, error=ErrorDetail(code=code, message=message), meta=None)
