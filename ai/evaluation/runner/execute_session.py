import argparse
import fcntl
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from dotenv import dotenv_values

AI_ROOT = Path(__file__).resolve().parents[2]
EVAL_ROOT = AI_ROOT / "evaluation"
BENCHMARK_ROOT = (AI_ROOT.parent / "data" / "benchmark").resolve()
SESSION_DIR = EVAL_ROOT / "sessions"
RUNS_DIR = EVAL_ROOT / "runs"
SCRIPT = AI_ROOT / "vlm" / "test_openrouter.py"
PROMPT_FILE = AI_ROOT / "prompts" / "b0_v1.txt"
MANIFEST_FILE = BENCHMARK_ROOT / "manifest.json"


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def timestamp():
    return datetime.now(timezone.utc).isoformat()


def save_atomic(path, data):
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=path.parent,
        prefix=".session_",
        suffix=".tmp",
        delete=False,
    ) as file:
        temporary = Path(file.name)
        json.dump(data, file, ensure_ascii=False, indent=2)
        file.write("\n")
        file.flush()
        os.fsync(file.fileno())

    try:
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def verify_file(relative_path, expected_hash):
    path = (BENCHMARK_ROOT / relative_path).resolve()

    if not path.is_relative_to(BENCHMARK_ROOT):
        raise ValueError("Unsafe benchmark path.")

    if not path.is_file() or sha256(path.read_bytes()) != expected_hash:
        raise ValueError(f"Benchmark integrity failed: {relative_path}")

    return path


def execute(session_path, max_tasks, should_execute):
    session = json.loads(session_path.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST_FILE.read_text(encoding="utf-8"))
    prompt = PROMPT_FILE.read_text(encoding="utf-8").strip()

    if session["manifest_sha256"] != sha256(MANIFEST_FILE.read_bytes()):
        raise ValueError("Manifest has changed since session planning.")

    if session["prompt_sha256"] != sha256(prompt.encode("utf-8")):
        raise ValueError("Prompt has changed since session planning.")

    if session["benchmark_version"] != manifest["version"]:
        raise ValueError("Benchmark version mismatch.")

    if session["reasoning"] != {"enabled": False}:
        raise ValueError("Unexpected reasoning configuration.")

    config = dotenv_values(AI_ROOT / ".env")
    current_model = os.getenv("OPENROUTER_MODEL") or config.get(
        "OPENROUTER_MODEL"
    )

    if current_model != session["model"]:
        raise ValueError("Configured model differs from session plan.")

    if len(session["tasks"]) != session["planned_requests"]:
        raise ValueError("Session task count mismatch.")

    if len(session["tasks"]) > session["request_limit"]:
        raise ValueError("Session request limit exceeded.")

    items = {item["id"]: item for item in manifest["items"]}

    if any(task["status"] == "running" for task in session["tasks"]):
        raise ValueError(
            "Session has an interrupted running task. "
            "Manual inspection required before resuming."
        )

    planned = [
        task for task in session["tasks"]
        if task["status"] == "planned"
    ]

    print("Session:", session["session_id"])
    print("Model:", session["model"])
    print("Pending tasks:", len(planned))
    print("Tasks this invocation:", min(max_tasks, len(planned)))
    print("Mode:", "EXECUTE" if should_execute else "DRY RUN")

    for task in planned[:max_tasks]:
        item = items[task["benchmark_id"]]

        if task["image_sha256"] != item["sha256"]:
            raise ValueError("Task image hash mismatch.")

        image = verify_file(item["image"], item["sha256"])

        truth = verify_file(
            item["ground_truth"],
            item["ground_truth_sha256"],
        )
        json.loads(truth.read_text(encoding="utf-8"))

        print(f"\nTask: {task['task_id']}")
        print("Image:", image.name)
        print("Integrity: PASS", flush=True)

        if not should_execute:
            print("Request: SKIPPED")
            continue

        task["status"] = "running"
        task["started_at_utc"] = timestamp()
        session["status"] = "running"
        save_atomic(session_path, session)

        command = [
            sys.executable,
            str(SCRIPT),
            "--image", str(image),
            "--prompt", prompt,
            "--temperature", str(session["temperature"]),
            "--max-tokens", str(session["max_tokens"]),
        ]

        try:
            result = subprocess.run(
                command,
                cwd=AI_ROOT,
                capture_output=True,
                text=True,
                timeout=120,
            )

            if result.returncode != 0:
                raise RuntimeError(
                    (result.stdout + "\n" + result.stderr)[-1000:]
                )

            prefix = "Experiment log saved to:"
            paths = [
                line[len(prefix):].strip()
                for line in result.stdout.splitlines()
                if line.startswith(prefix)
            ]

            if len(paths) != 1:
                raise RuntimeError("Cannot identify generated run log.")

            log_path = Path(paths[0]).resolve()

            if log_path.parent != RUNS_DIR.resolve():
                raise RuntimeError("Unexpected log location.")

            log = json.loads(log_path.read_text(encoding="utf-8"))
            response = log["response"]

            if (
                log["model"] != session["model"]
                or log["prompt"] != prompt
                or log["image_sha256"] != item["sha256"]
                or log["temperature"] != session["temperature"]
                or log["max_tokens"] != session["max_tokens"]
                or log["reasoning"] != session["reasoning"]
                or log["http_status"] != 200
                or response["choices"][0]["finish_reason"] != "stop"
            ):
                raise RuntimeError("Generated log does not match session.")

            task["status"] = "completed"
            task["run_id"] = log["run_id"]
            task["completed_at_utc"] = timestamp()
            task["latency_seconds"] = log["latency_seconds"]

            print("Completed:", task["task_id"])
            print("Run ID:", task["run_id"])

        except Exception as error:
            task["status"] = "failed"
            task["error"] = str(error)
            save_atomic(session_path, session)
            raise RuntimeError(
                f"Task {task['task_id']} failed. "
                "Automatic retry is disabled."
            ) from error

        save_atomic(session_path, session)

    if should_execute:
        if all(t["status"] == "completed" for t in session["tasks"]):
            session["status"] = "completed"
        else:
            session["status"] = "partial"

        save_atomic(session_path, session)

    print("\nSession execution finished.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--session", required=True)
    parser.add_argument("--max-tasks", type=int, default=1)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()

    if not re.fullmatch(
        r"\d{8}T\d{6}_[0-9a-f]{8}", args.session
    ):
        raise SystemExit("Invalid session ID.")

    if not 1 <= args.max_tasks <= 10:
        raise SystemExit("max-tasks must be between 1 and 10.")

    path = SESSION_DIR / f"{args.session}.json"

    if not path.is_file():
        raise SystemExit(f"Session not found: {path}")

    # Prevent concurrent execution of the same session.
    lock_path = SESSION_DIR / f"{args.session}.lock"

    with lock_path.open("a+") as lock:
        try:
            fcntl.flock(
                lock.fileno(),
                fcntl.LOCK_EX | fcntl.LOCK_NB,
            )
        except BlockingIOError:
            raise SystemExit("This session is already running.")

        execute(path, args.max_tasks, args.execute)


if __name__ == "__main__":
    main()
