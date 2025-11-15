"""
FastAPI Main Application Entry Point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="SOR-HD API",
    description="Sistema de Optimización de Rutas para Hospitalización Domiciliaria",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "sor-hd-backend"}

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "SOR-HD API - Sistema de Optimización de Rutas para Hospitalización Domiciliaria",
        "version": "1.0.0",
        "docs": "/api/docs"
    }
