#!/usr/bin/env python3
"""
Launch AlphaPilot Web Platform.
Starts FastAPI backend on port 8000.
In production (when frontend/dist exists), also serves the React app.
"""

import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
