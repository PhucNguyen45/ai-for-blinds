import argparse
import hashlib
import json
import re
from pathlib import Path

AI_ROOT = Path(__file__).resolve().parents[2]
BENCHMARK_ROOT = AI_ROOT.parent / "data" / "benchmark"
EVALUATION_ROOT = AI_ROOT / "evaluation"

FIELDS = [
    "run_id",
    "timestamp_utc",
    "model",
    "image_sha256",
    "prompt",
    "temperature",
    "max_tokens",
    "reasoning",
    "http_status",
    "latency_seconds",
    "response",
]


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("run_ids", nargs="+")
    args = parser.parse_args()

    manifest = json.loads(
        (BENCHMARK_ROOT / "manifest.json").read_text(encoding="utf-8")
    )

    prompt = (AI_ROOT / "prompts" / "b0_v1.txt").read_text(
        encoding="utf-8"
    ).strip()

    prompt_hash = hashlib.sha256(prompt.encode("utf-8")).hexdigest()

    records_dir = EVALUATION_ROOT / "records"
    records_dir.mkdir(parents=True, exist_ok=True)

    for run_id in args.run_ids:
        if not re.fullmatch(r"\d{8}T\d{6}_[0-9a-f]{8}", run_id):
            raise SystemExit(f"Invalid run ID: {run_id}")

        run_path = EVALUATION_ROOT / "runs" / f"{run_id}.json"
        run = json.loads(run_path.read_text(encoding="utf-8"))

        if run["run_id"] != run_id:
            raise SystemExit(f"Run ID mismatch: {run_id}")

        if run["prompt"] != prompt:
            raise SystemExit(f"Prompt mismatch: {run_id}")

        if run["http_status"] != 200:
            raise SystemExit(f"Unsuccessful request: {run_id}")

        if run["response"]["choices"][0]["finish_reason"] != "stop":
            raise SystemExit(f"Incomplete response: {run_id}")

        matches = [
            item for item in manifest["items"]
            if item["sha256"] == run["image_sha256"]
        ]

        if len(matches) != 1:
            raise SystemExit(f"Benchmark match error: {run_id}")

        item = matches[0]

        for key, hash_key in [
            ("image", "sha256"),
            ("ground_truth", "ground_truth_sha256"),
        ]:
            path = (BENCHMARK_ROOT / item[key]).resolve()

            if not path.is_relative_to(BENCHMARK_ROOT.resolve()):
                raise SystemExit(f"Unsafe benchmark path: {path}")

            if not path.is_file() or sha256(path) != item[hash_key]:
                raise SystemExit(f"Integrity error: {path}")

        record = {key: run[key] for key in FIELDS}
        record["benchmark_id"] = item["id"]
        record["benchmark_version"] = manifest["version"]
        record["image_path"] = f"data/benchmark/{item['image']}"
        record["prompt_id"] = "b0_v1"
        record["prompt_sha256"] = prompt_hash

        output = records_dir / f"{run_id}.json"

        with output.open("x", encoding="utf-8") as file:
            json.dump(record, file, ensure_ascii=False, indent=2)

        print(f"Archived: {item['id']} -> {output.name}")

    print("Archiving completed.")


if __name__ == "__main__":
    main()
