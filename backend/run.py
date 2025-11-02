#!/usr/bin/env python3
"""
FastAPI Trip Planner Backend
Run this script to start the development server
"""

import uvicorn
from app.main import app
from app.core.config import settings

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=settings.debug,
        log_level="info"
    )
