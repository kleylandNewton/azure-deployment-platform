"""
Simple Hello World Backend API
Replace this with your actual application code
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI(title="Hello World API")

# CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Hello from Azure! 🚀",
        "status": "running",
        "environment": os.getenv("ENVIRONMENT", "unknown")
    }

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}

@app.get("/api/info")
async def info():
    """App information"""
    return {
        "app": "Azure App Template",
        "version": "1.0.0",
        "description": "This is a template - replace with your app!"
    }
