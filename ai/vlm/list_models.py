#!/usr/bin/env python3
"""Liệt kê model khả dụng của nhà cung cấp đang chọn (tên model Gemini đổi rất nhanh).

Chạy từ thư mục ai/:  uv run python vlm/list_models.py --provider google [--filter flash]
Chỉ in tên model, không in khóa.
"""
import argparse
import os
import sys
from pathlib import Path

import httpx
from dotenv import dotenv_values

AI_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(AI_ROOT))

from vlm.providers import ConfigError, resolve_provider  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--provider", choices=["openrouter", "google", "lmstudio"])
    ap.add_argument("--filter", default="")
    args = ap.parse_args()
    config = {**dotenv_values(AI_ROOT / ".env"), **os.environ}
    try:
        prov = resolve_provider({**config, "OPENROUTER_MODEL": config.get("OPENROUTER_MODEL") or "x",
                                 "GOOGLE_MODEL": config.get("GOOGLE_MODEL") or "x",
                                 "LMSTUDIO_MODEL": config.get("LMSTUDIO_MODEL") or "x"}, args.provider)
    except ConfigError as exc:
        raise SystemExit(str(exc))
    print(f"# {prov.name}: {prov.base_url}", file=sys.stderr)
    r = httpx.get(prov.base_url + "/models", headers={"Authorization": f"Bearer {prov.api_key}"},
                  timeout=30)
    if r.status_code != 200:
        raise SystemExit(f"HTTP {r.status_code} khi lấy danh sách model.")
    ids = sorted(m["id"].removeprefix("models/") for m in r.json().get("data", []))
    for i in ids:
        if args.filter.lower() in i.lower():
            print(i)


if __name__ == "__main__":
    main()
