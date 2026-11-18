import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[3]
OUTPUT = ROOT / "data" / "benchmark" / "_legacy" / "regen"  # không ghi đè bản chính thức ở benchmark/synthetic
OUTPUT.mkdir(parents=True, exist_ok=True)

DATA = {"3A": 12, "3B": 18, "3C": 15, "3D": 9}

FONT_PATH = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")

if not FONT_PATH.exists():
    raise SystemExit("Chưa tìm thấy font DejaVu Sans.")

def font(size):
    return ImageFont.truetype(str(FONT_PATH), size)

image = Image.new("RGB", (1100, 720), "white")
draw = ImageDraw.Draw(image)

draw.text(
    (120, 45),
    "Số cây trồng được của các lớp",
    font=font(37),
    fill="black",
)

draw.text(
    (120, 102),
    "Dữ liệu minh họa",
    font=font(22),
    fill="gray",
)

left, top, right, bottom = 150, 180, 1020, 620
max_value = 20

# Trục và đường lưới
for tick in range(0, 21, 5):
    y = bottom - tick / max_value * (bottom - top)

    draw.line((left, y, right, y), fill="#dddddd", width=2)
    draw.text((92, y - 15), str(tick), font=font(25), fill="black")

draw.text((58, 145), "Số cây", font=font(23), fill="black")

# Các cột
for i, (class_name, value) in enumerate(DATA.items()):
    x = 230 + i * 205
    width = 110
    y = bottom - value / max_value * (bottom - top)

    draw.rectangle(
        (x, y, x + width, bottom),
        fill="#3679b5",
    )


    draw.text(
        (x + 29, bottom + 15),
        class_name,
        font=font(27),
        fill="black",
    )

image_path = OUTPUT / "chart_02_no_labels.png"
image.save(image_path)

ground_truth = {
    "chart_type": "bar_chart",
    "synthetic": True,
    "title": "Số cây trồng được của các lớp",
    "values": DATA,
    "maximum_class": "3B",
    "minimum_class": "3D",
    "difference": 9,
    "total": 54,
}

truth_path = OUTPUT / "chart_02_no_labels_truth.json"
truth_path.write_text(
    json.dumps(ground_truth, ensure_ascii=False, indent=2),
    encoding="utf-8",
)

print("Image:", image_path)
print("Ground truth:", truth_path)
