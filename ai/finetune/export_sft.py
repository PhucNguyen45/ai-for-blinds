#!/usr/bin/env python3
"""Xuất tập huấn luyện đã sinh thành JSONL hội thoại (SFT) cho fine-tune VLM.

Mỗi dòng là một hội thoại:
  - kind=describe: ảnh -> lời diễn giải (định dạng đầu ra chọn bằng --format)
  - kind=ask:      ảnh + lời mô tả trước đó + câu hỏi -> trả lời nói (bật bằng --include-ask)

--format api_v1  Trợ lý trả đúng MỘT đối tượng JSON {"page_type","unreadable","description"} như backend API v1 hiện
                 tại mong đợi. LƯU Ý: hợp đồng API v1 đang được nhóm thống nhất lại; đổi định dạng ở đây khi hợp đồng đổi.
--format plain   Trợ lý trả thẳng lời diễn giải (văn nói thuần).
--format spoken  Như plain nhưng ảnh có lỗi chụp (unreadable) thì câu trả lời bắt đầu bằng "KHÔNG ĐỌC ĐƯỢC:" (cụm module `vlm/common.py::UNREADABLE_RE`
                 nhận ra), khớp prompt `prompts/ft_describe_v1.txt`; chỉ xuất mẫu `describe` (dùng với --describe-only).

Prompt hệ thống dùng khi huấn luyện PHẢI giống prompt dùng khi chạy thật: dùng --describe-system-file/--ask-system-file
để nạp đúng prompt của backend (vd prompts/v1/system.md, ask.md) thay vì bản rút gọn mặc định bên dưới.

  uv run python finetune/export_sft.py --data ../data/train/v1 --out ../data/train/v1/sft_api_v1.jsonl --split train
"""

import argparse
import json
from pathlib import Path

DESCRIBE_SYSTEM = (
    "Bạn là trợ lý đọc học liệu cho học sinh khiếm thị ở Việt Nam. Học sinh không nhìn thấy trang, chỉ nghe lời bạn nói.\n"
    "Quy tắc: nói ý chính trước; dùng văn nói tiếng Việt, câu ngắn, không dùng ký hiệu định dạng; đọc số bằng chữ; "
    "chỉ nói điều đọc được rõ trên ảnh, không bịa; nếu ảnh mờ, tối, chói hoặc bị cắt mất thì nói thẳng và hướng dẫn "
    "chụp lại; kết thúc bằng một câu hỏi gợi ý học sinh muốn nghe thêm gì."
)
ASK_SYSTEM = (
    "Bạn là trợ lý đọc học liệu cho học sinh khiếm thị. Học sinh đang hỏi thêm về trang vừa chụp. Trả lời đúng câu hỏi, "
    "một đến bốn câu, văn nói tiếng Việt, không ký hiệu định dạng, chỉ dựa vào ảnh, không bịa tên hay số."
)
DESCRIBE_USER = "Hãy mô tả trang này theo đúng hướng dẫn và trả về JSON."
DESCRIBE_USER_PLAIN = "Hãy mô tả trang này theo đúng hướng dẫn."
DESCRIBE_USER_SPOKEN = "Hãy mô tả trang này."
UNREADABLE_PREFIX = "KHÔNG ĐỌC ĐƯỢC: "


def image_part(path):
    return {"type": "image", "image": str(path)}


def describe_line(item, img, fmt, system):
    t = item["target"]
    if fmt == "api_v1":
        answer, user = json.dumps(t, ensure_ascii=False, separators=(",", ":")), DESCRIBE_USER
    elif fmt == "spoken":
        answer = (UNREADABLE_PREFIX if t["unreadable"] else "") + t["description"]
        user = DESCRIBE_USER_SPOKEN
    else:
        answer, user = t["description"], DESCRIBE_USER_PLAIN
    return {"id": item["id"], "kind": "describe", "split": item["split"], "category": item["category"],
            "messages": [{"role": "system", "content": system},
                         {"role": "user", "content": [image_part(img), {"type": "text", "text": user}]},
                         {"role": "assistant", "content": answer}]}


def ask_lines(item, img, system):
    out = []
    for n, qa in enumerate(item["qa"]):
        out.append({"id": f"{item['id']}_q{n + 1}", "kind": "ask", "split": item["split"],
                    "category": item["category"],
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": [image_part(img), {"type": "text", "text":
                         "Đây là trang học sinh vừa chụp. Bạn đã mô tả cho học sinh như sau:\n"
                         + item["target"]["description"]}]},
                        {"role": "assistant", "content": "Mình đã xem trang này. Bạn muốn hỏi gì?"},
                        {"role": "user", "content": qa["question"]},
                        {"role": "assistant", "content": qa["answer_spoken"]}]})
    return out


def export(data_dir, out_path, fmt="api_v1", split="train", include_ask=False, image_root=None,
           describe_system=DESCRIBE_SYSTEM, ask_system=ASK_SYSTEM, describe_only=False):
    data_dir = Path(data_dir)
    lines = []
    for p in sorted(data_dir.glob("tr_*.json")):
        item = json.loads(p.read_text(encoding="utf-8"))
        if split != "all" and item["split"] != split:
            continue
        img = (Path(image_root) / item["image"]) if image_root else (data_dir / item["image"]).resolve()
        lines.append(describe_line(item, img, fmt, describe_system))
        if include_ask and item["qa"] and not describe_only:
            lines.extend(ask_lines(item, img, ask_system))
    Path(out_path).write_text("".join(json.dumps(l, ensure_ascii=False) + "\n" for l in lines), encoding="utf-8")
    return lines


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--format", choices=["api_v1", "plain", "spoken"], default="api_v1")
    ap.add_argument("--describe-only", action="store_true", help="chỉ xuất mẫu describe (bỏ hỏi đáp)")
    ap.add_argument("--split", choices=["train", "val", "all"], default="train")
    ap.add_argument("--include-ask", action="store_true")
    ap.add_argument("--image-root", help="đường dẫn gốc ảnh ghi vào JSONL (mặc định: đường dẫn tuyệt đối)")
    ap.add_argument("--describe-system-file")
    ap.add_argument("--ask-system-file")
    a = ap.parse_args()
    ds = Path(a.describe_system_file).read_text(encoding="utf-8").strip() if a.describe_system_file else DESCRIBE_SYSTEM
    ask = Path(a.ask_system_file).read_text(encoding="utf-8").strip() if a.ask_system_file else ASK_SYSTEM
    lines = export(a.data, a.out, a.format, a.split, a.include_ask, a.image_root, ds, ask, a.describe_only)
    kinds = {}
    for l in lines:
        kinds[l["kind"]] = kinds.get(l["kind"], 0) + 1
    print(f"Đã ghi {len(lines)} hội thoại vào {a.out}: {kinds} (split={a.split}, format={a.format})")
    if not (a.describe_system_file and a.ask_system_file):
        print("Cảnh báo: đang dùng prompt hệ thống rút gọn mặc định; hãy dùng đúng prompt của backend khi huấn luyện thật.")


if __name__ == "__main__":
    main()
