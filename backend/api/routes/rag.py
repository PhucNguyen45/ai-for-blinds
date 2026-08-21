"""
POST /rag/query — Retrieval-Augmented Generation for textbook Q&A.

Answers student questions grounded in Vietnamese textbook (SGK) content.
Returns answer with source citations for trustworthiness.
"""

from fastapi import APIRouter

from backend.schemas.rag import RagQueryRequest, RagQueryResponse, SourceCitation
from backend.services.rag_service import rag_service
from backend.services.vlm_service import vlm_service
from backend.utils.response_builder import success_response, error_response

router = APIRouter()


@router.post("/query")
async def rag_query(query: RagQueryRequest):
    """
    Hỏi đáp kiến thức dựa trên nội dung sách giáo khoa (SGK).

    Sử dụng ChromaDB + embeddings để truy xuất các đoạn văn bản
    phù hợp nhất, sau đó tổng hợp câu trả lời có trích dẫn nguồn.

    Trả về:
    - answer: Câu trả lời bằng tiếng Việt
    - source: Trích dẫn nguồn đáng tin cậy nhất
    """
    if not rag_service.available:
        return error_response(
            message="RAG không khả dụng. Vui lòng kiểm tra ChromaDB.",
            status_code=503,
        )

    metadata_filter = {}
    if query.grade is not None:
        metadata_filter["grade"] = query.grade
    if query.subject is not None:
        metadata_filter["subject"] = query.subject

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

    # Chroma trả metadata trong một dict; SourceCitation lại khai báo từng
    # trường riêng, nên phải trải ra — nếu không, nguồn trích dẫn bị mất và
    # học sinh nghe câu trả lời mà không biết lấy từ bài nào.
    def to_citation(r: dict) -> SourceCitation:
        meta = r.get("metadata") or {}
        return SourceCitation(
            chunk_id=r["id"],
            text=r["text"],
            grade=meta.get("grade"),
            subject=meta.get("subject"),
            chapter=meta.get("section"),
            page_number=meta.get("page_number"),
            citation=meta.get("source"),
            distance=r.get("distance", 0.0),
        )

    sources = [to_citation(r) for r in results]

    # Use the top result as the primary source
    primary = sources[0]

    # Let the model turn the retrieved passages into spoken Vietnamese. If the
    # call fails, fall back to the top passage so the student still hears
    # something rather than silence.
    answer = vlm_service.answer_from_context(
        question=query.question,
        passages=[s.text for s in sources],
    ) or primary.text

    return success_response(data=RagQueryResponse(
        answer=answer,
        source=primary,
        sources=sources,
    ).model_dump())
