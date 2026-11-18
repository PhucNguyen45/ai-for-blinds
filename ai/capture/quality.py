"""Cổng kiểm tra chất lượng ảnh chụp trước khi gọi VLM.

Mục đích: ảnh quá tối hoặc quá mờ thì không cần tốn một lượt VLM; trả ngay lời hướng dẫn chụp lại bằng tiếng Việt
(đọc được bằng giọng nói). Chỉ dùng Pillow, không cần mạng, chạy trong chưa tới một giây.

Phạm vi: bắt được các lỗi VẬT LÝ đo bằng thống kê ảnh (tối, mờ, cháy sáng toàn ảnh). Các lỗi phụ thuộc nội dung
(chói che một phần, hình bị cắt mất một mép) không đo được bằng thống kê toàn ảnh; việc đó do prompt `b0g_v1` của
VLM đảm nhiệm (xem README ở thư mục này).

Ngưỡng hiệu chỉnh trên ảnh TỔNG HỢP (tập huấn luyện `ai/finetune`): độ tối và độ mờ tách rất rộng (xem báo cáo
`ai/evaluation/reports/capture_gate_*.md`). Ảnh chụp thật có thể cần chỉnh lại ngưỡng; các ngưỡng nằm trong
`Thresholds` để chỉnh mà không sửa logic.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image, ImageFilter, ImageStat

# Gợi ý chụp lại (nguồn duy nhất; bộ sinh dữ liệu huấn luyện cũng dùng lại các câu này).
CAPTURE_GUIDANCE = {
    "blur": [
        "Ảnh bị mờ nên mình chưa đọc rõ được nội dung. Bạn giữ điện thoại thật chắc tay, lùi ra một chút để cả trang vào khung, rồi chụp lại nhé.",
        "Ảnh này mờ quá, mình không đọc được chữ và số. Bạn giữ yên điện thoại vài giây trước khi chụp, rồi thử lại nhé.",
    ],
    "dark": [
        "Ảnh quá tối nên mình không đọc được. Bạn bật đèn hoặc đưa trang sách ra chỗ sáng hơn rồi chụp lại nhé.",
        "Trang sách đang bị thiếu sáng, mình chưa nhìn rõ. Bạn thử chụp lại ở nơi có ánh sáng tốt hơn nhé.",
    ],
    "glare": [
        "Ảnh bị chói sáng che mất một phần nên mình không đọc đủ. Bạn nghiêng nhẹ điện thoại hoặc tránh ánh đèn rọi thẳng vào trang rồi chụp lại nhé.",
        "Có một vùng bị loá sáng trên ảnh. Bạn đổi góc cầm điện thoại một chút để hết loá rồi chụp lại nhé.",
    ],
    "cropped_left": ["Hình bị cắt mất phần bên trái. Bạn dịch điện thoại sang trái một chút và lùi ra xa hơn để thấy đủ cả hình rồi chụp lại nhé."],
    "cropped_right": ["Hình bị cắt mất phần bên phải. Bạn dịch điện thoại sang phải một chút và lùi ra xa hơn để thấy đủ cả hình rồi chụp lại nhé."],
    "cropped_top": ["Hình bị cắt mất phần phía trên. Bạn nâng điện thoại lên một chút và lùi ra xa hơn để thấy đủ cả hình rồi chụp lại nhé."],
    "cropped_bottom": ["Hình bị cắt mất phần phía dưới. Bạn hạ điện thoại xuống một chút và lùi ra xa hơn để thấy đủ cả hình rồi chụp lại nhé."],
}


@dataclass(frozen=True)
class Thresholds:
    dark_mean: float = 60.0      # độ sáng trung bình (0-255) dưới mức này là quá tối
    blur_laplacian: float = 40.0  # phương sai bộ lọc Laplace (ảnh đã thu về cạnh dài 640) dưới mức này là mờ
    overexposed_mean: float = 235.0  # cháy sáng: sáng trung bình cao...
    overexposed_std: float = 15.0    # ...và gần như không còn tương phản
    analysis_size: int = 640     # cạnh dài khi phân tích; làm cho số đo ít phụ thuộc độ phân giải máy ảnh


@dataclass(frozen=True)
class CaptureReport:
    ok: bool
    issues: tuple[str, ...] = ()
    metrics: dict = field(default_factory=dict)

    @property
    def guidance_vi(self) -> str | None:
        """Lời hướng dẫn chụp lại (ưu tiên lỗi đầu tiên); None nếu ảnh đạt."""
        return guidance_for(self.issues)


_LAPLACE = ImageFilter.Kernel((3, 3), [0, 1, 0, 1, -4, 1, 0, 1, 0], scale=1, offset=128)


def guidance_for(issues, variant: int = 0) -> str | None:
    """Câu hướng dẫn cho lỗi đầu tiên có trong CAPTURE_GUIDANCE; `variant` chọn biến thể câu chữ."""
    for issue in issues:
        options = CAPTURE_GUIDANCE.get(issue)
        if options:
            return options[variant % len(options)]
    return None


def measure(image: Image.Image, analysis_size: int = 640) -> dict:
    gray = image.convert("L")
    gray.thumbnail((analysis_size, analysis_size))
    stat = ImageStat.Stat(gray)
    # PIL không lọc các điểm ảnh ngoài cùng (giữ nguyên giá trị gốc), nên bỏ viền 1 điểm trước khi tính phương sai
    w, h = gray.size
    lap = gray.filter(_LAPLACE).crop((1, 1, w - 1, h - 1))
    return {
        "mean": round(stat.mean[0], 2),
        "std": round(stat.stddev[0], 2),
        "laplacian_var": round(ImageStat.Stat(lap).var[0], 2),
    }


def check_image(source, thresholds: Thresholds = Thresholds()) -> CaptureReport:
    """Kiểm tra ảnh (đường dẫn hoặc `PIL.Image`). Không ném lỗi với ảnh đọc được; ảnh hỏng ném `OSError`."""
    if isinstance(source, (str, Path)):
        with Image.open(source) as im:
            return check_image(im.copy(), thresholds)
    m = measure(source, thresholds.analysis_size)
    issues = []
    if m["mean"] < thresholds.dark_mean:
        issues.append("dark")
    elif m["laplacian_var"] < thresholds.blur_laplacian:
        issues.append("blur")
    elif m["mean"] > thresholds.overexposed_mean and m["std"] < thresholds.overexposed_std:
        issues.append("glare")
    return CaptureReport(ok=not issues, issues=tuple(issues), metrics=m)
