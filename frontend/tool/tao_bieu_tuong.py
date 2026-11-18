"""Sinh biểu tượng app SgBe cho Android: nền vàng dẫn đường, cuốn sách mở màu đen và sóng âm.

Chạy lại khi muốn đổi biểu tượng: python tool/tao_bieu_tuong.py
- mipmap-*/ic_launcher.png: biểu tượng kiểu cũ (Android 7 trở xuống), vuông bo góc.
- mipmap-*/ic_launcher_foreground.png + mipmap-anydpi-v26/ic_launcher.xml: biểu tượng thích ứng
  (Android 8 trở lên), launcher tự cắt hình tròn / vuông bo góc theo máy.
Hình do script tự vẽ nên không vướng bản quyền.
"""
from pathlib import Path

from PIL import Image, ImageDraw

RES = Path(__file__).resolve().parent.parent / "android" / "app" / "src" / "main" / "res"
YELLOW = (255, 212, 0, 255)
INK = (11, 11, 12, 255)
S = 1024  # vẽ lớn rồi thu nhỏ cho mịn


def glyph(draw: ImageDraw.ImageDraw, cx: float, cy: float, k: float) -> None:
    """Cuốn sách mở + hai vòng sóng âm phía trên; k = tỉ lệ (1.0 cho khung 1024)."""
    def p(x, y):
        return (cx + x * k, cy + y * k)

    # Hai trang sách, hơi chéo như sách mở, khe giữa là gáy.
    draw.polygon([p(-300, -70), p(-24, -20), p(-24, 250), p(-300, 200)], fill=INK)
    draw.polygon([p(24, -20), p(300, -70), p(300, 200), p(24, 250)], fill=INK)
    # Dòng chữ trên trang (nét vàng mảnh)
    for i, y in enumerate((20, 80, 140)):
        draw.line([p(-250, y - 40 + i * 4), p(-74, y - 10 + i * 4)], fill=YELLOW, width=int(18 * k))
        draw.line([p(74, y - 10 + i * 4), p(250, y - 40 + i * 4)], fill=YELLOW, width=int(18 * k))
    # Sóng âm: sách được đọc thành tiếng
    for r in (150, 250):
        box = [p(-r, -150 - r), p(r, -150 + r)]
        draw.arc(box, start=215, end=325, fill=INK, width=int(40 * k))


def legacy(size: int) -> Image.Image:
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, S - 1, S - 1], radius=220, fill=YELLOW)
    glyph(d, S / 2, S / 2 + 40, 1.0)
    return im.resize((size, size), Image.LANCZOS)


def foreground(size: int) -> Image.Image:
    # Khung 108dp, vùng an toàn 66dp ở giữa: hình chiếm khoảng 60% để không bị cắt.
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    glyph(d, S / 2, S / 2 + 26, 0.62)
    return im.resize((size, size), Image.LANCZOS)


DENSITIES = {"mdpi": 1, "hdpi": 1.5, "xhdpi": 2, "xxhdpi": 3, "xxxhdpi": 4}
for name, f in DENSITIES.items():
    folder = RES / f"mipmap-{name}"
    folder.mkdir(parents=True, exist_ok=True)
    legacy(int(48 * f)).save(folder / "ic_launcher.png")
    foreground(int(108 * f)).save(folder / "ic_launcher_foreground.png")

(RES / "mipmap-anydpi-v26").mkdir(exist_ok=True)
(RES / "mipmap-anydpi-v26" / "ic_launcher.xml").write_text(
    """<?xml version="1.0" encoding="utf-8"?>
<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@color/sgbe_yellow" />
    <foreground android:drawable="@mipmap/ic_launcher_foreground" />
    <monochrome android:drawable="@mipmap/ic_launcher_foreground" />
</adaptive-icon>
""",
    encoding="utf-8",
)
legacy(512).save(Path(__file__).resolve().parent.parent / "docs" / "anh-giao-dien" / "bieu-tuong.png")
print("Đã ghi biểu tượng vào", RES)
