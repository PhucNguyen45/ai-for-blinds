import argparse
import hashlib
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
    # Prefer archived research records, then fall back to local logs.
    candidates = [
        EVALUATION_DIR / "records" / f"{run_id}.json",
        EVALUATION_DIR / "runs" / f"{run_id}.json",
    ]

    run_file = next(
        (candidate for candidate in candidates if candidate.is_file()),
        None,
    )

    if run_file is None:
        raise SystemExit(
            f"ERROR: Experiment record not found for {run_id}"
        )

    run = json.loads(run_file.read_text(encoding="utf-8"))

    if run.get("run_id") != run_id:
        raise SystemExit("ERROR: Run ID mismatch.")

    if run_file.parent.name == "records":
        benchmark_root = (
            EVALUATION_DIR.parents[1] / "data" / "benchmark"
        ).resolve()

        manifest = json.loads(
            (benchmark_root / "manifest.json").read_text(
                encoding="utf-8"
            )
        )

        matches = [
            item for item in manifest["items"]
            if item["id"] == run.get("benchmark_id")
        ]

        if len(matches) != 1:
            raise SystemExit("ERROR: Invalid benchmark ID.")

        item = matches[0]

        image = (benchmark_root / item["image"]).resolve()

        if not image.is_relative_to(benchmark_root):
            raise SystemExit("ERROR: Unsafe benchmark image path.")

        if not image.is_file():
            raise SystemExit("ERROR: Benchmark image missing.")

        actual_hash = hashlib.sha256(image.read_bytes()).hexdigest()

        if (
            actual_hash != item["sha256"]
            or actual_hash != run.get("image_sha256")
        ):
            raise SystemExit("ERROR: Benchmark image hash mismatch.")

        # Verify the ground-truth file against its manifest hash.
        truth = (benchmark_root / item["ground_truth"]).resolve()

        if not truth.is_relative_to(benchmark_root):
            raise SystemExit("ERROR: Unsafe ground-truth path.")

        if not truth.is_file():
            raise SystemExit("ERROR: Ground-truth file missing.")

        truth_hash = hashlib.sha256(truth.read_bytes()).hexdigest()

        if truth_hash != item.get("ground_truth_sha256"):
            raise SystemExit("ERROR: Ground-truth hash mismatch.")

        print("Ground truth integrity: PASS")

        expected_path = (
            Path("data") / "benchmark" / item["image"]
        ).as_posix()

        if run.get("image_path") != expected_path:
            raise SystemExit("ERROR: Benchmark image path mismatch.")

        if run.get("benchmark_version") != manifest["version"]:
            raise SystemExit("ERROR: Benchmark version mismatch.")

        print("Benchmark integrity: PASS")


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
    print("Record source:", run_file.parent.name)
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
