from fastapi import APIRouter, Depends, Request, status

from app.core.security import require_api_key
from app.models.request_response import (
    ArchitectureRequest,
    ArchitectureResponse,
    HealthResponse,
)
from app.services.architecture_generator import ArchitectureGeneratorService

router = APIRouter()


def get_architecture_service(request: Request) -> ArchitectureGeneratorService:
    return request.app.state.architecture_service


@router.get(
    "/health",
    response_model=HealthResponse,
    tags=["Health"],
    summary="Health check",
)
async def health_check() -> HealthResponse:
    return HealthResponse(status="ok", service="ai-system-architecture-generator")


@router.post(
    "/generate-architecture",
    response_model=ArchitectureResponse,
    status_code=status.HTTP_200_OK,
    tags=["Architecture"],
    summary="Generate a complete system architecture from a prompt",
    dependencies=[Depends(require_api_key)],
)
async def generate_architecture(
    payload: ArchitectureRequest,
    service: ArchitectureGeneratorService = Depends(get_architecture_service),
) -> ArchitectureResponse:
    return await service.generate(payload)
