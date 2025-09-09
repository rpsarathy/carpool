#!/usr/bin/env python3
"""
Start the FastAPI server for testing
"""
import os
import uvicorn
from pathlib import Path

# Set environment for local SQLite database
os.environ["DATABASE_URL"] = "sqlite:///./carpool_local.db"

if __name__ == "__main__":
    # Start the server
    uvicorn.run(
        "src.carpool.api:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )
