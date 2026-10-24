import csv
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCORES = ROOT / "scores"
OUTPUT = ROOT / "reports" / "score_summary.csv"
VALIDATOR = Path(__file__).with_name("validate_score.py")

FIELDS = [
    "run_id",
    "image_id",
    "model",
    "rubric_version",
    "C1", "C2", "C3", "C4", "C5", "C6",
    "total_score",
]

rows = []
pending = 0

for path in sorted(SCORES.glob("*_score.json")):
    data = json.loads(path.read_text(encoding="utf-8"))

    if data["evaluation_status"] == "pending":
        pending += 1
        continue

    if data["evaluation_status"] != "completed":
        raise SystemExit(f"Invalid status: {path}")

    result = subprocess.run(
        [sys.executable, str(VALIDATOR), str(path)],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise SystemExit(
            f"Invalid scorecard: {path}\n"
            + result.stdout + result.stderr
        )

    row = {
        "run_id": data["run_id"],
        "image_id": data["image_id"],
        "model": data["model"],
        "rubric_version": data["rubric_version"],
        "total_score": data["total_score"],
    }

    for i in range(1, 7):
        code = f"C{i}"
        row[code] = data["criteria"][code]["score"]

    rows.append(row)

OUTPUT.parent.mkdir(parents=True, exist_ok=True)

with OUTPUT.open("w", encoding="utf-8-sig", newline="") as file:
    writer = csv.DictWriter(file, fieldnames=FIELDS)
    writer.writeheader()
    writer.writerows(rows)

print("Completed evaluations:", len(rows))
print("Pending evaluations:", pending)
print("Summary:", OUTPUT)
print()

for row in rows:
    print(
        f"{row['run_id']} | "
        f"{row['model']} | "
        f"{row['total_score']}/12"
    )
