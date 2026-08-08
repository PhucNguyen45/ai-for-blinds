"""
POST /moments, GET /moments, DELETE /moments/{id}, POST /moments/search —
Persistent Visual Memory API.

Stores learning moments (captured images, descriptions, OCR text, Q&A answers)
per device so students can revisit and semantically search them later.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Request

from backend.api.auth import verify_api_key
from backend.deps import limiter
from backend.schemas.moment import (
    MomentCreate,
    MomentResponse,
    MomentSearchRequest,
    MomentSearchResponse,
    MomentSearchResult,
)
from backend.services.moment_service import moment_service
from backend.utils.response_builder import success_response

logger = logging.getLogger(__name__)

router = APIRouter()


def _device_id(request: Request) -> str:
    """Read device_id from header, falling back to query param."""
    device_id = request.headers.get("X-Device-Id") or request.query_params.get("device_id")
    if not device_id:
        raise HTTPException(status_code=422, detail="Thiếu device_id (header X-Device-Id).")
    return device_id.strip()


def _require_available() -> None:
    if not moment_service.available:
        raise HTTPException(
            status_code=503,
            detail="Lưu trữ khoảnh khắc không khả dụng. Vui lòng kiểm tra cơ sở dữ liệu.",
        )


@router.post("/moments", response_model=None)
@limiter.limit("30/minute")
async def create_moment(
    request: Request,
    body: MomentCreate,
    api_key: str = Depends(verify_api_key),
):
    """Lưu một khoảnh khắc học tập (nội dung + embedding ngữ nghĩa)."""
    device_id = _device_id(request)
    _require_available()

    moment = await moment_service.create(
        device_id=device_id,
        title=body.title,
        content=body.content,
        content_type=body.content_type,
        grade=body.grade,
        subject=body.subject,
        chapter=body.chapter,
        page_number=body.page_number,
    )
    if moment is None:
        raise HTTPException(status_code=500, detail="Không thể lưu khoảnh khắc học tập.")

    return success_response(data=moment, message="Đã lưu khoảnh khắc học tập.")


@router.get("/moments", response_model=None)
@limiter.limit("60/minute")
async def list_moments(
    request: Request,
    api_key: str = Depends(verify_api_key),
):
    """Liệt kê các khoảnh khắc học tập của thiết bị, mới nhất trước."""
    device_id = _device_id(request)
    _require_available()

    moments = await moment_service.list_for_device(device_id)
    return success_response(data=moments, message=f"Có {len(moments)} khoảnh khắc.")


@router.delete("/moments/{moment_id}", response_model=None)
@limiter.limit("30/minute")
async def delete_moment(
    request: Request,
    moment_id: str,
    api_key: str = Depends(verify_api_key),
):
    """Xóa một khoảnh khắc học tập của thiết bị."""
    device_id = _device_id(request)
    _require_available()

    deleted = await moment_service.delete(device_id, moment_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Không tìm thấy khoảnh khắc học tập.")

    return success_response(message="Đã xóa khoảnh khắc học tập.")


@router.post("/moments/search", response_model=None)
@limiter.limit("30/minute")
async def search_moments(
    request: Request,
    body: MomentSearchRequest,
    api_key: str = Depends(verify_api_key),
):
    """Tìm kiếm ngữ nghĩa các khoảnh khắc học tập bằng câu hỏi/từ khóa."""
    device_id = _device_id(request)
    _require_available()

    results = await moment_service.search(
        device_id,
        query=body.query,
        n_results=body.n_results,
    )
    response = MomentSearchResponse(
        query=body.query,
        results=[
            MomentSearchResult(**r)
            for r in results
        ],
    ).model_dump(mode="json")
    return success_response(data=response, message=f"Tìm thấy {len(results)} kết quả.")
