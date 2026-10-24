import argparse
import json
from pathlib import Path

EVALUATION_DIR = Path(__file__).resolve().parents[1]
EXPECTED_CRITERIA = {f"C{i}" for i in range(1, 7)}


def main():
    parser = argparse.ArgumentParser(
        description="Validate a VLM evaluation scorecard."
    )
    parser.add_argument("score_file", type=Path)
    args = parser.parse_args()

    scorecard = json.loads(
        args.score_file.read_text(encoding="utf-8")
    )

    run_id = scorecard["run_id"]
    run_file = EVALUATION_DIR / "runs" / f"{run_id}.json"

    if not run_file.is_file():
        raise SystemExit(f"ERROR: Experiment log not found: {run_file}")

    run = json.loads(run_file.read_text(encoding="utf-8"))

    if scorecard["model"] != run["model"]:
        raise SystemExit("ERROR: Model does not match experiment log.")

    if scorecard["image_id"] != (
        Path(run["image_path"]).stem if run.get("image_path") else ""
    ):
        raise SystemExit("ERROR: Image ID does not match experiment log.")

    criteria = scorecard["criteria"]

    if set(criteria) != EXPECTED_CRITERIA:
        raise SystemExit("ERROR: Expected exactly C1 through C6.")

    if scorecard["rubric_version"] != "v1":
        raise SystemExit("ERROR: Unsupported rubric version.")

    scores = []

    for criterion in sorted(EXPECTED_CRITERIA):
        item = criteria[criterion]
        value = item["score"]

        if value is not None and (
            type(value) is not int or value not in (0, 1, 2)
        ):
            raise SystemExit(
                f"ERROR: Invalid score for {criterion}: {value}"
            )

        if not isinstance(item["evidence"], str):
            raise SystemExit(
                f"ERROR: Evidence for {criterion} must be text."
            )

        if value is not None:
            scores.append(value)

    status = scorecard["evaluation_status"]

    if status not in ("pending", "completed"):
        raise SystemExit("ERROR: Invalid evaluation status.")

    if status == "completed":
        if len(scores) != 6:
            raise SystemExit("ERROR: Completed scorecard has missing scores.")

        if any(not criteria[c]["evidence"].strip() for c in EXPECTED_CRITERIA):
            raise SystemExit("ERROR: Completed scorecard requires evidence.")

        if scorecard["total_score"] != sum(scores):
            raise SystemExit("ERROR: Total score does not match criteria.")

    elif scorecard["total_score"] is not None:
        raise SystemExit("ERROR: Pending scorecard must have a null total.")

    print("Validation: PASS")
    print("Run ID:", run_id)
    print("Rubric:", scorecard["rubric_version"])
    print("Status:", status)
    print("Scored criteria:", f"{len(scores)}/6")

    if len(scores) == 6:
        print("Calculated score:", f"{sum(scores)}/12")
    else:
        print("Calculated score: incomplete")


if __name__ == "__main__":
    main()
