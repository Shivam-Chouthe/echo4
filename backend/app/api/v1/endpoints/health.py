from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class HealthCheck(BaseModel):
    status: str
    version: str


@router.get("/health", response_model=HealthCheck, tags=["Health"])
async def health_check() -> HealthCheck:
    return HealthCheck(status="ok", version="0.1.0")
