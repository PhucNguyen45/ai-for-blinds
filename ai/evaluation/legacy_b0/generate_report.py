import argparse
import json
from pathlib import Path

EVALUATION_DIR = Path(__file__).resolve().parents[1]
RUNS_DIR = EVALUATION_DIR / "runs"
REPORTS_DIR = EVALUATION_DIR / "reports"


def main():
    parser = argparse.ArgumentParser(
        description="Generate a Markdown report from a VLM experiment log."
    )
    parser.add_argument(
        "--run",
        type=Path,
        help="Path to experiment JSON; defaults to the latest run.",
    )
    args = parser.parse_args()

    if args.run:
        run_file = args.run
    else:
        files = list(RUNS_DIR.glob("*.json"))
        if not files:
            raise SystemExit("No experiment logs found.")
        run_file = max(files, key=lambda p: p.stat().st_mtime_ns)

    data = json.loads(run_file.read_text(encoding="utf-8"))
    response = data["response"]
    choice = response["choices"][0]
    usage = response.get("usage", {})

    answer = choice.get("message", {}).get("content")
    if not isinstance(answer, str):
        answer = json.dumps(answer, ensure_ascii=False, indent=2)

    # Use a safe Markdown fence even if the response contains backticks.
    fence = "````"
    while fence in answer:
        fence += "`"

    report = f"""# Báo cáo thực nghiệm VLM — {data["run_id"]}

## 1. Thông tin thực nghiệm

- Run ID: `{data["run_id"]}`
- Thời điểm UTC: {data["timestamp_utc"]}
- Mô hình: `{data["model"]}`
- Ảnh: `{Path(data["image_path"]).name if data.get("image_path") else "Không có"}`
- SHA-256 ảnh: `{data.get("image_sha256") or "N/A"}`
- Temperature: {data["temperature"]}
- Max tokens: {data["max_tokens"]}

## 2. Hiệu năng

- HTTP status: {data["http_status"]}
- Finish reason: `{choice.get("finish_reason")}`
- Độ trễ: {data["latency_seconds"]} giây
- Input tokens: {usage.get("prompt_tokens", "N/A")}
- Output tokens: {usage.get("completion_tokens", "N/A")}
- Total tokens: {usage.get("total_tokens", "N/A")}
- Chi phí API báo cáo: {usage.get("cost", "N/A")} USD

## 3. Prompt

{data["prompt"]}

## 4. Câu trả lời của VLM

{fence}text
{answer}
{fence}

## 5. Đánh giá

**Trạng thái: CHƯA CHẤM**

- Độ chính xác dữ kiện: Chưa đánh giá
- Độ chính xác quan hệ trực quan: Chưa đánh giá
- Hallucination: Chưa đánh giá
- Chất lượng tiếng Việt: Chưa đánh giá
- Mức độ phù hợp với học sinh khiếm thị: Chưa đánh giá

Ghi chú: Cần đối chiếu với đáp án chuẩn và rubric trước khi kết luận.
"""

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    output = REPORTS_DIR / f"run_{data['run_id']}.md"

    if output.exists():
        raise SystemExit(f"Report already exists: {output}")

    output.write_text(report, encoding="utf-8")
    print("Report generated:", output)


if __name__ == "__main__":
    main()
