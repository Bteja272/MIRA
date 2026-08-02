from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
)


class HealthResponse(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )

    status: Literal["ok"]
    application: str
    version: str
    environment: str


class ReadinessResponse(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )

    status: Literal["ready"]
    database: Literal["ok"]
    llm: Literal["ok"]