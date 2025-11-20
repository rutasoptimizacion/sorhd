"""
FastAPI Main Application Entry Point
"""

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1 import api_router
from app.core.config import settings
from app.core.exceptions import SORHDException
from app.services.tracking.websocket_manager import keep_alive_task


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    # Startup: Start WebSocket keep-alive task
    task = asyncio.create_task(keep_alive_task())

    yield

    # Shutdown: Cancel keep-alive task
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


app = FastAPI(
    title="FlamenGO! API",
    description="Sistema de Optimización de Rutas para Hospitalización Domiciliaria",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global Exception Handlers
@app.exception_handler(SORHDException)
async def sorhd_exception_handler(request: Request, exc: SORHDException):
    """Handle custom FlamenGO! exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors"""
    # Convert errors to JSON-serializable format
    errors = []
    for error in exc.errors():
        error_dict = {}
        for key, value in error.items():
            if isinstance(value, bytes):
                try:
                    error_dict[key] = value.decode("utf-8")
                except Exception:
                    error_dict[key] = str(value)
            else:
                error_dict[key] = value
        errors.append(error_dict)

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": errors},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions"""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "sor-hd-backend"}


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "FlamenGO! API - Sistema de Optimización de Rutas para Hospitalización Domiciliaria",
        "version": "1.0.0",
        "docs": "/api/docs",
    }


# Include API v1 router
app.include_router(api_router, prefix="/api/v1")
