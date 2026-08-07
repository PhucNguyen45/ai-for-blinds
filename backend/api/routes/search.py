"""
POST /search — Internet Retrieval (IR).

Searches the web (DuckDuckGo) and Vietnamese news (RSS + TF-IDF),
returning merged, relevance-ranked results for blind students.
"""

from fastapi import APIRouter, Depends, Request

from backend.api.auth import verify_api_key
from backend.deps import limiter
from backend.schemas.search import SearchRequest, SearchResult, SearchResponse
from backend.services.ir_service import ir_service
from backend.utils.response_builder import success_response

router = APIRouter()


@router.post("/search")
@limiter.limit("20/minute")
async def search_web(
    request: Request,
    body: SearchRequest,
    api_key: str = Depends(verify_api_key),
):
    """
    Tìm kiếm thông tin trên Internet (web + tin tức tiếng Việt).

    Kết quả bao gồm nguồn (web/news), tiêu đề, đoạn trích và điểm liên quan.
    """
    results = ir_service.search(body.query, body.n_results)

    return success_response(
        data=SearchResponse(
            query=body.query,
            results=[SearchResult(**r) for r in results],
        ).model_dump()
    )
