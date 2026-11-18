import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from dotenv import dotenv_values

AI_ROOT = Path(__file__).resolve().parents[2]
BENCHMARK_ROOT = (AI_ROOT.parent / "data" / "benchmark").resolve()
MANIFEST_PATH = BENCHMARK_ROOT / "manifest.json"
PROMPT_PATH = AI_ROOT / "prompts" / "b0_v1.txt"
SESSIONS_DIR = AI_ROOT / "evaluation" / "sessions"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_file(relative_path, expected_hash):
    path = (BENCHMARK_ROOT / relative_path).resolve()

    if not path.is_relative_to(BENCHMARK_ROOT):
        raise ValueError("Unsafe benchmark path")

    if not path.is_file():
        raise FileNotFoundError(path)

    if sha256(path) != expected_hash:
        raise ValueError(f"Hash mismatch: {path}")

    return path


def main():
    parser = argparse.ArgumentParser(
        description="Plan a reproducible VLM experiment session."
    )
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--max-requests", type=int, default=10)
    parser.add_argument("--ids", nargs="+")
    args = parser.parse_args()

    if not 1 <= args.repeats <= 20:
        raise SystemExit("Repeats must be between 1 and 20.")

    manifest = json.loads(
        MANIFEST_PATH.read_text(encoding="utf-8")
    )
    prompt = PROMPT_PATH.read_text(encoding="utf-8").strip()

    config = dotenv_values(AI_ROOT / ".env")
    model = os.getenv("OPENROUTER_MODEL") or config.get("OPENROUTER_MODEL")

    if not model:
        raise SystemExit("OPENROUTER_MODEL is not configured.")

    items = manifest["items"]

    if args.ids:
        requested = set(args.ids)
        available = {item["id"] for item in items}
        unknown = requested - available

        if unknown:
            raise SystemExit(f"Unknown image IDs: {sorted(unknown)}")

        items = [item for item in items if item["id"] in requested]

    total = len(items) * args.repeats

    if not 1 <= total <= args.max_requests:
        raise SystemExit(
            f"Planned requests ({total}) exceed the limit "
            f"({args.max_requests})."
        )

    tasks = []

    for item in items:
        verify_file(item["image"], item["sha256"])
        truth_path = verify_file(
            item["ground_truth"],
            item["ground_truth_sha256"],
        )
        json.loads(truth_path.read_text(encoding="utf-8"))

        for repeat in range(1, args.repeats + 1):
            tasks.append({
                "task_id": f"{item['id']}_r{repeat:02d}",
                "benchmark_id": item["id"],
                "image_sha256": item["sha256"],
                "repeat_index": repeat,
                "status": "planned",
            })

    now = datetime.now(timezone.utc)
    session_id = (
        now.strftime("%Y%m%dT%H%M%S")
        + "_" + uuid4().hex[:8]
    )

    plan = {
        "session_id": session_id,
        "created_at_utc": now.isoformat(),
        "status": "planned",
        "benchmark_version": manifest["version"],
        "manifest_sha256": sha256(MANIFEST_PATH),
        "prompt_id": "b0_v1",
        "prompt_sha256": hashlib.sha256(
            prompt.encode("utf-8")
        ).hexdigest(),
        "model": model,
        "temperature": 0.2,
        "max_tokens": 600,
        "reasoning": {"enabled": False},
        "repeats": args.repeats,
        "request_limit": args.max_requests,
        "planned_requests": total,
        "tasks": tasks,
    }

    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    output = SESSIONS_DIR / f"{session_id}.json"

    with output.open("x", encoding="utf-8") as file:
        json.dump(plan, file, ensure_ascii=False, indent=2)
        file.write("\n")

    print("Session ID:", session_id)
    print("Benchmark:", manifest["version"])
    print("Prompt:", plan["prompt_id"])
    print("Model:", model)
    print("Images:", len(items))
    print("Repeats per image:", args.repeats)
    print("Planned requests:", total)
    print("API requests sent: 0")
    print("Session plan:", output)

    print("\nTasks:")
    for task in tasks:
        print(" ", task["task_id"])


if __name__ == "__main__":
    main()
