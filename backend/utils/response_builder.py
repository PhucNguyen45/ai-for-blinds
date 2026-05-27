"""
Standardized API response helpers.

Ensures consistent JSON response format across all endpoints.
"""

from typing import Any, Optional

from fastapi.responses import JSONResponse


def success_response(
    data: Any = None,
    message: str = "Thành công",
    status_code: int = 200,
) -> JSONResponse:
    """
    Return a standardized success response.

    Args:
        data: Response payload.
        message: Human-readable success message (Vietnamese).
        status_code: HTTP status code.

    Returns:
        JSONResponse with standard format.
    """
    body: dict[str, Any] = {
        "success": True,
        "message": message,
    }
    if data is not None:
        body["data"] = data

    return JSONResponse(content=body, status_code=status_code)


def error_response(
    message: str = "Đã xảy ra lỗi",
    status_code: int = 500,
    detail: Optional[str] = None,
) -> JSONResponse:
    """
    Return a standardized error response.

    Args:
        message: Human-readable error message (Vietnamese).
        status_code: HTTP status code.
        detail: Optional technical detail for debugging.

    Returns:
        JSONResponse with standard error format.
    """
    body: dict[str, Any] = {
        "success": False,
        "message": message,
    }
    if detail is not None:
        body["detail"] = detail

    return JSONResponse(content=body, status_code=status_code)
