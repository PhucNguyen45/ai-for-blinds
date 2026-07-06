"""
POST /rag/query — Retrieval-Augmented Generation for textbook Q&A.

Answers student questions grounded in Vietnamese textbook (SGK) content.
Returns answer with source citations for trustworthiness.
"""

from fastapi import APIRouter, Depends, HTTPException, Request

from backend.api.auth import verify_api_key
from backend.main import limiter
from backend.schemas.rag import RagQueryRequest, RagQueryResponse, SourceCitation
from backend.services.rag_service import rag_service
from backend.services.vlm_service import vlm_service
from backend.utils.response_builder import success_response

router = APIRouter()


@router.post("/query")
@limiter.limit("20/minute")
async def rag_query(
    request: Request,
    query: RagQueryRequest,
    api_key: str = Depends(verify_api_key),
):
    """
    Hỏi đáp kiến thức dựa trên nội dung sách giáo khoa (SGK).

    Sử dụng ChromaDB + embeddings để truy xuất các đoạn văn bản
    phù hợp nhất, sau đó tổng hợp câu trả lời có trích dẫn nguồn.

    Trả về:
    - answer: Câu trả lời bằng tiếng Việt
    - source: Trích dẫn nguồn đáng tin cậy nhất
    """
    if not rag_service.available:
        raise HTTPException(
            status_code=503,
            detail="RAG không khả dụng. Vui lòng kiểm tra ChromaDB.",
        )

    # Build metadata filter for ChromaDB with sanitization
    ALLOWED_FILTER_KEYS = {"grade", "subject", "chapter"}
    raw_filter = {}
    if query.grade is not None:
        raw_filter["grade"] = query.grade
    if query.subject is not None:
        raw_filter["subject"] = query.subject
    metadata_filter = {k: v for k, v in raw_filter.items() if k in ALLOWED_FILTER_KEYS}

    # Retrieve relevant chunks from ChromaDB
    results = rag_service.search(
        query=query.question,
        n_results=query.n_results,
        filter_metadata=metadata_filter if metadata_filter else None,
    )

    if not results:
        return success_response(data={
            "answer": "Không tìm thấy thông tin liên quan trong sách giáo khoa. "
                      "Vui lòng đặt câu hỏi khác hoặc kiểm tra lại từ khóa.",
            "source": None,
            "sources": [],
        })

    # Build source citations
    sources = [
        SourceCitation(
            chunk_id=r["id"],
            text=r["text"],
            metadata=r.get("metadata", {}),
            distance=r.get("distance", 0.0),
        )
        for r in results
    ]

    # Use the top result as the primary source
    primary = sources[0]

    # Generate answer using Gemini with context from retrieved chunks
    if sources:
        answer = vlm_service.generate_answer(question=query.question, context_chunks=sources)
    else:
        answer = "Không tìm thấy thông tin liên quan trong sách giáo khoa."

    return success_response(data=RagQueryResponse(
        answer=answer,
        source=primary,
        sources=sources,
    ).model_dump())
