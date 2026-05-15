"""
Entry point for deployment platforms (HuggingFace Spaces, Render, etc.)
Runs the FastAPI backend from the backend/ directory.
"""
import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.app import app  # noqa: F401 — re-export for uvicorn
