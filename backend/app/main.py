from __future__ import annotations

import time
import uuid
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import auth, curriculum, dashboard, families, ingestion, materials, providers, students, tasks
from app.config import settings
from app.logging_config import configure_logging
from app.redis import redis_client

configure_logging()
logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield
    await redis_client.aclose()


app = FastAPI(title="Mary Education Hub", version="0.1.1", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = str(uuid.uuid4())
    start = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        logger.exception("request_failed", request_id=request_id, path=request.url.path, method=request.method)
        raise
    latency_ms = round((time.perf_counter() - start) * 1000, 2)
    response.headers["X-Request-Id"] = request_id
    logger.info(
        "request_completed",
        request_id=request_id,
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        latency_ms=latency_ms,
    )
    return response


@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
    if isinstance(exc.detail, dict):
        return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": "HTTP_ERROR", "message": str(exc.detail), "details": {}}},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={"error": {"code": "VALIDATION_ERROR", "message": "Validation failed", "details": {"errors": exc.errors()}}},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    if isinstance(exc, (RequestValidationError, HTTPException)):
        raise exc
    logger.exception("unhandled_error")
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "INTERNAL_SERVER_ERROR", "message": "Unexpected server error", "details": {}}},
    )


@app.get("/health")
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


api_prefix = "/api/v1"
app.include_router(auth.router, prefix=api_prefix)
app.include_router(families.router, prefix=api_prefix)
app.include_router(students.router, prefix=api_prefix)
app.include_router(materials.router, prefix=api_prefix)
app.include_router(tasks.router, prefix=api_prefix)
app.include_router(curriculum.router, prefix=api_prefix)
app.include_router(dashboard.router, prefix=api_prefix)
app.include_router(providers.router, prefix=api_prefix)
app.include_router(ingestion.router, prefix=api_prefix)
