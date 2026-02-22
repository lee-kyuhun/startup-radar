from __future__ import annotations

from pydantic import BaseModel


class SourceSchema(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    name: str
    slug: str
    source_type: str
    is_active: bool
