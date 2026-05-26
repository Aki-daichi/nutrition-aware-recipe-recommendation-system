"""Main FastAPI application"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
from pathlib import Path

from config import CORS_ORIGINS, API_TITLE, API_DESCRIPTION, API_VERSION, DEBUG
from database import init_db
from routes import router

# Initialize database tables
init_db()

# Create FastAPI app
app = FastAPI(
    title=API_TITLE,
    description=API_DESCRIPTION,
    version=API_VERSION,
    debug=DEBUG
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router)

# Mount frontend static files
frontend_path = Path(__file__).parent.parent / "frontend"
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_path / "static")), name="static")


# Root endpoint to serve index.html
@app.get("/", include_in_schema=False)
async def root():
    """Serve the main dashboard page"""
    index_path = frontend_path / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {"message": "Nutrition-Aware Recipe Recommendation System API"}


@app.get("/dashboard", include_in_schema=False)
async def dashboard():
    """Serve the dashboard page"""
    dashboard_path = frontend_path / "dashboard.html"
    if dashboard_path.exists():
        return FileResponse(str(dashboard_path))
    return {"message": "Dashboard page not found"}


@app.get("/api/info")
def api_info():
    """Get API information"""
    return {
        "name": API_TITLE,
        "description": API_DESCRIPTION,
        "version": API_VERSION,
        "status": "running"
    }


if __name__ == "__main__":
    import uvicorn
    from config import HOST, PORT
    
    uvicorn.run(
        "main:app",
        host=HOST,
        port=PORT,
        reload=DEBUG
    )
