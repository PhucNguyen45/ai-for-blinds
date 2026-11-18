import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

AI_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = AI_ROOT.parent
BENCHMARK_ROOT = (REPO_ROOT / "data" / "benchmark").resolve()
MANIFEST = BENCHMARK_ROOT / "manifest.json"
PROMPT_FILE = AI_ROOT / "prompts" / "b0_v1.txt"
TEST_SCRIPT = AI_ROOT / "evaluation" / "legacy_b0" / "test_openrouter.py"

TEMPERATURE = 0.2
MAX_TOKENS = 600


def verify_file(relative_path, expected_sha256):
    path = (BENCHMARK_ROOT / relative_path).resolve()

    if not path.is_relative_to(BENCHMARK_ROOT):
        raise ValueError(f"Unsafe path: {relative_path}")

    if not path.is_file():
        raise FileNotFoundError(path)

    actual_hash = hashlib.sha256(path.read_bytes()).hexdigest()

    if actual_hash != expected_sha256:
        raise ValueError(f"SHA-256 mismatch: {path}")

    return path


def main():
    parser = argparse.ArgumentParser(
        description="Run a reproducible VLM benchmark."
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually send requests to OpenRouter.",
    )
    parser.add_argument(
        "--ids",
        nargs="+",
        help="Run only the specified benchmark IDs.",
    )
    args = parser.parse_args()

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    prompt = PROMPT_FILE.read_text(encoding="utf-8").strip()

    items = manifest["items"]

    if args.ids:
        requested = set(args.ids)
        available = {item["id"] for item in items}
        unknown = requested - available

        if unknown:
            raise SystemExit(f"Unknown benchmark IDs: {sorted(unknown)}")

        items = [item for item in items if item["id"] in requested]

    print("Benchmark version:", manifest["version"])
    print("Prompt:", PROMPT_FILE.name)
    print("Prompt SHA-256:", hashlib.sha256(prompt.encode()).hexdigest())
    print("Temperature:", TEMPERATURE)
    print("Max tokens:", MAX_TOKENS)
    print("Number of images:", len(items))
    print("Mode:", "EXECUTE" if args.execute else "DRY RUN")
    print()

    for index, item in enumerate(items, start=1):
        image = verify_file(item["image"], item["sha256"])

        truth = verify_file(
            item["ground_truth"],
            item["ground_truth_sha256"],
        )
        json.loads(truth.read_text(encoding="utf-8"))

        print(f"[{index}/{len(items)}] {item['id']}")
        print("Image:", image)
        print("Ground truth:", truth)
        print("Integrity: PASS", flush=True)

        if not args.execute:
            print("Request: SKIPPED")
            print()
            continue

        command = [
            sys.executable,
            str(TEST_SCRIPT),
            "--image", str(image),
            "--prompt", prompt,
            "--temperature", str(TEMPERATURE),
            "--max-tokens", str(MAX_TOKENS),
        ]

        result = subprocess.run(command, cwd=AI_ROOT)

        if result.returncode != 0:
            raise SystemExit(
                f"Benchmark stopped at {item['id']}: "
                f"exit code {result.returncode}"
            )

        print()

    print("Benchmark finished.")


if __name__ == "__main__":
    main()
