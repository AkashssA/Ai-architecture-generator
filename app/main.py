import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.cache import build_cache
from app.core.config import get_settings
from app.core.exceptions import ArchitectureGenerationError
from app.core.logging import configure_logging
from app.core.rate_limiter import RateLimitMiddleware
from app.services.architecture_generator import ArchitectureGeneratorService

settings = get_settings()
configure_logging(settings.log_level)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    cache = await build_cache(settings.redis_url)
    app.state.cache = cache
    app.state.architecture_service = ArchitectureGeneratorService(settings=settings, cache=cache)
    logger.info("Application startup completed.")
    try:
        yield
    finally:
        await cache.close()
        logger.info("Application shutdown completed.")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
    lifespan=lifespan,
    description=(
        "Generate structured software architectures, Mermaid diagrams, endpoint designs, "
        "and scalability guidance from natural-language prompts."
    ),
    swagger_ui_parameters={"defaultModelsExpandDepth": -1, "displayRequestDuration": True},
    contact={"name": "Backend Platform Team", "email": "platform@example.com"},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    RateLimitMiddleware,
    max_requests=settings.rate_limit_requests,
    window_seconds=settings.rate_limit_window_seconds,
)
app.include_router(router, prefix="/api")


@app.exception_handler(ArchitectureGenerationError)
async def architecture_generation_exception_handler(
    request: Request,
    exc: ArchitectureGenerationError,
) -> JSONResponse:
    logger.warning("Architecture generation failed for %s: %s", request.url.path, exc)
    return JSONResponse(status_code=502, content={"detail": str(exc)})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    logger.info("Validation error for %s: %s", request.url.path, exc.errors())
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "message": "Invalid request payload."},
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error at %s", request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. Please try again later."},
    )
