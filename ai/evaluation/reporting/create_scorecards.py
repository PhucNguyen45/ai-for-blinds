import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECORDS_DIR = ROOT / "records"
SCORES_DIR = ROOT / "scores"


def create_scorecard(run_id):
    if not re.fullmatch(r"\d{8}T\d{6}_[0-9a-f]{8}", run_id):
        raise ValueError(f"Invalid run ID: {run_id}")

    record_path = RECORDS_DIR / f"{run_id}.json"

    if not record_path.is_file():
        raise FileNotFoundError(record_path)

    record = json.loads(record_path.read_text(encoding="utf-8"))

    if record["run_id"] != run_id:
        raise ValueError(f"Run ID mismatch: {run_id}")

    image_id = record["benchmark_id"]

    if not isinstance(image_id, str) or not image_id:
        raise ValueError("Invalid benchmark ID")

    scorecard = {
        "run_id": run_id,
        "rubric_version": "v1",
        "image_id": image_id,
        "model": record["model"],
        "evaluation_status": "pending",
        "evaluator": None,
        "criteria": {
            f"C{i}": {
                "score": None,
                "evidence": ""
            }
            for i in range(1, 7)
        },
        "total_score": None,
        "notes": "",
    }

    SCORES_DIR.mkdir(parents=True, exist_ok=True)
    output = SCORES_DIR / f"{run_id}_score.json"

    # Exclusive creation: never overwrite an existing scorecard.
    with output.open("x", encoding="utf-8") as file:
        json.dump(scorecard, file, ensure_ascii=False, indent=2)
        file.write("\n")

    print(f"Created: {output.name}")
    print(f"  Benchmark: {image_id}")
    print("  Status: pending")
    print("  Criteria: 6")


def main():
    parser = argparse.ArgumentParser(
        description="Create scorecards from archived VLM records."
    )
    parser.add_argument("run_ids", nargs="+")
    args = parser.parse_args()

    for run_id in args.run_ids:
        create_scorecard(run_id)


if __name__ == "__main__":
    main()
