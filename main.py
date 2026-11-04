"""ASGI entry point: uvicorn main:app --reload"""

from property_intelligence.api import app

__all__ = ["app"]
