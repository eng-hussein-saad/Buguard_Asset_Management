from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict


class HealthResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["ok"]


router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse, operation_id="getHealth")
async def health() -> HealthResponse:
    return HealthResponse(status="ok")

