"""
API key authentication middleware for SgBe Vision.

Requires all AI-heavy endpoints to present a valid X-API-Key header.
"""

from fastapi import Header, HTTPException

from backend.config import settings


async def verify_api_key(
    x_api_key: str = Header(..., description="API key for authentication"),
):
    if x_api_key != settings.api_key:
        raise HTTPException(
            status_code=403,
            detail="Invalid API key. Provide a valid X-API-Key header.",
        )
    return x_api_key
