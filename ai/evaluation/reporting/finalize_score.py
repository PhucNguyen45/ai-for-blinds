import argparse
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("score_file", type=Path)
    parser.add_argument("--reviewer", required=True)
    parser.add_argument("--approve", action="store_true")
    args = parser.parse_args()

    reviewer = args.reviewer.strip()

    if not args.approve:
        raise SystemExit("ERROR: Explicit --approve is required.")

    if not reviewer or reviewer == "assistant_preliminary":
        raise SystemExit("ERROR: A human reviewer is required.")

    path = args.score_file.resolve()
    data = json.loads(path.read_text(encoding="utf-8"))

    if data["evaluation_status"] != "pending":
        raise SystemExit("ERROR: Scorecard is not pending.")

    criteria = data["criteria"]
    expected = {f"C{i}" for i in range(1, 7)}

    if set(criteria) != expected:
        raise SystemExit("ERROR: Missing or unexpected criteria.")

    for code in expected:
        item = criteria[code]

        if type(item["score"]) is not int or item["score"] not in (0, 1, 2):
            raise SystemExit(f"ERROR: Invalid score for {code}.")

        if not isinstance(item["evidence"], str) or not item["evidence"].strip():
            raise SystemExit(f"ERROR: Missing evidence for {code}.")

    data["preliminary_evaluator"] = data.get("evaluator")
    data["evaluator"] = reviewer
    data["reviewed_at_utc"] = datetime.now(timezone.utc).isoformat()
    data["evaluation_status"] = "completed"
    data["total_score"] = sum(
        item["score"] for item in criteria.values()
    )

    validator = Path(__file__).with_name("validate_score.py")

    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        suffix=".json",
        prefix=".score_",
        dir=path.parent,
        delete=False,
    ) as temp:
        temporary_path = Path(temp.name)
        json.dump(data, temp, ensure_ascii=False, indent=2)

    try:
        result = subprocess.run(
            [sys.executable, str(validator), str(temporary_path)],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            raise SystemExit(
                "Validation failed:\n" + result.stdout + result.stderr
            )

        os.replace(temporary_path, path)
    finally:
        temporary_path.unlink(missing_ok=True)

    print("Evaluation finalized:", path)
    print("Reviewer:", reviewer)
    print("Total score:", f"{data['total_score']}/12")
    print("Status:", data["evaluation_status"])


if __name__ == "__main__":
    main()
