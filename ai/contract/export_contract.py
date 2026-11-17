#!/usr/bin/env python3
"""Xuất JSON Schema và các ví dụ response của hợp đồng v0.1.

Chạy từ thư mục ai/:  uv run python contract/export_contract.py
Ví dụ được dựng bằng chính model Pydantic nên luôn hợp lệ.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

from contract.models import (
    CONTRACT_VERSION, DescriptionResult, ErrorInfo, Fact, Meta, Usage,
)

HERE = Path(__file__).resolve().parent
META = Meta(model="example/model", prompt_id="b0_v1", prompt_sha256="0" * 64,
            temperature=0.2, max_tokens=600, finish_reason="stop", latency_seconds=3.4,
            usage=Usage(prompt_tokens=800, completion_tokens=250),
            created_at_utc=datetime(2026, 11, 17, 5, 0, tzinfo=timezone.utc))

EXAMPLES = {
    "ok_bar_chart": DescriptionResult(
        image_id="img-001", image_sha256="a" * 64, image_type="bar_chart", status="ok",
        summary_vi="Biểu đồ cột về số sách thư viện cho mượn trong tuần.",
        facts=[Fact(subject="Cột Thứ 2", predicate="có giá trị", object="40 quyển",
                    evidence="Nhãn số 40 phía trên cột")],
        interpretation_vi=("Biểu đồ có năm cột từ Thứ 2 đến Thứ 6. Thứ 2 cao nhất với 40 quyển, "
                           "Thứ 4 thấp nhất với 5 quyển."),
        uncertainties=[], question_answering_ready=True, meta=META),
    "partial_truncated": DescriptionResult(
        image_id="img-002", image_sha256="b" * 64, status="partial",
        summary_vi="Bảng số liệu về số ngày có mưa.",
        interpretation_vi="Bảng có năm hàng tháng và ba cột miền. Số liệu ở các ô chưa được đọc",
        uncertainties=["Câu trả lời bị cắt do giới hạn độ dài."], meta=META),
    "unreadable_blurred": DescriptionResult(
        image_id="img-003", image_sha256="c" * 64, status="unreadable",
        summary_vi="Ảnh quá mờ nên không đọc được nhãn và số liệu; chưa thể diễn giải.",
        uncertainties=["Không xác định được tiêu đề, trục và giá trị."], meta=META),
    "error_timeout": DescriptionResult(
        image_id="img-004", image_sha256="d" * 64, status="error",
        error=ErrorInfo(code="timeout", message="Hết thời gian chờ mô hình.", retryable=True),
        meta=META),
}


def main():
    (HERE / "examples").mkdir(exist_ok=True)
    schema = DescriptionResult.model_json_schema()
    (HERE / f"schema_v{CONTRACT_VERSION.replace('.', '_')}.json").write_text(
        json.dumps(schema, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for name, value in EXAMPLES.items():
        (HERE / "examples" / f"{name}.json").write_text(
            value.model_dump_json(indent=2, exclude_none=True) + "\n", encoding="utf-8")
    print("Đã xuất schema và", len(EXAMPLES), "ví dụ.")


if __name__ == "__main__":
    main()
