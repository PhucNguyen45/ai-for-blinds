"""
POST /sonify — Sonification Service.

Converts structured data points into audio descriptions and tone
mappings for playback via Tone.js on the frontend.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Request

from backend.api.auth import verify_api_key
from backend.main import limiter
from backend.schemas.sonify import SonifyRequest
from backend.services.sonification import sonify_data
from backend.utils.response_builder import success_response

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/sonify")
@limiter.limit("30/minute")
async def sonify(
    request: Request,
    body: SonifyRequest,
    api_key: str = Depends(verify_api_key),
):
    """Chuyển đổi dữ liệu thành mô tả âm thanh và thông số sonification."""

    result = sonify_data(
        data_points=[dp.model_dump() for dp in body.data_points],
        chart_type=body.chart_type,
    )

    if result is None:
        raise HTTPException(status_code=400, detail="Invalid or empty data")

    return success_response(data=result, message=result["summary"])
