# Cổng chất lượng ảnh (`capture/quality.py`) trên ảnh thật

> **Ngày:** 2026-11-27 · **Kết luận ngắn:** ngưỡng cũ (chỉnh trên ảnh tổng hợp) chặn nhầm 15,1% ảnh tốt do người khiếm thị
> tự chụp, trong khi chỉ bắt 19% ảnh tối và 37% ảnh mờ. Ngưỡng mới chỉ chặn ảnh gần như đen hoặc nhòe nặng: chặn nhầm
> còn 1,3%. Ảnh nằm giữa hai mức chuyển sang `warnings` (không chặn) để VLM tự quyết.

## 1. Dữ liệu và cách đo

- **VizWiz-VQA train**: 20.523 ảnh người khiếm thị tự chụp bằng điện thoại. Nhãn "tốt" là các câu người gán nhãn trả lời
  được; "tối", "mờ", "chói" lấy từ lý do không trả lời được. Đây là nhãn của người gán nhãn, không phải số đo chất lượng.
- **SGK Kết nối tri thức lớp 1–5**: 6.774 trang bản quét (ảnh sạch, mọi lần chặn đều là chặn nhầm).
- Chỉ tính thống kê ảnh (`measure`), không gọi mô hình. Dữ liệu chỉ để ở máy (bản quyền), không đưa vào repo.
  Script đo: `E:\dataset_khiem_thi\danh_gia\cham_cong.py` (máy Toàn).

## 2. Kết quả

| Luật | Chặn nhầm VizWiz tốt (10.400) | Bắt ảnh "tối" (136) | Bắt ảnh "mờ" (326) | Chặn nhầm SGK (tối/mờ) |
| --- | --- | --- | --- | --- |
| Cũ: tối < 60, mờ < 40 | 1.574 (15,1%) | 26 (19,1%) | 119 (36,5%) | 0 |
| Mới: tối < 30 hoặc phân vị 95 < 40, mờ < 10 | 1,3% | 18 (13,2%) | 35 (10,7%) | 0 |

Ảnh tốt bị chặn nhầm theo ngưỡng cũ: 1.246 vì "mờ" (ảnh điện thoại hơi nhòe vẫn đọc được), 328 vì "tối" (màn hình số
trên nền đen, áo, lon nước tối màu). Đây là lỗi "chặn nhầm ảnh nền tối" đã biết.

12 trang SGK bị chặn vì "chói" ở cả hai luật đều là trang gần như trắng (trang lót sau bìa), không ảnh hưởng.

Kiểm chứng: `check_image` mới cho kết quả trùng với luật tính từ bảng số đo trên 200 ảnh lấy ngẫu nhiên (200/200).

## 3. Thay đổi

- `Thresholds`: `dark_mean` 60 → 30, thêm `dark_p95` = 40 (cả vùng sáng nhất vẫn tối thì mới là thiếu sáng, phân biệt
  với trang/vật có nền tối), `blur_laplacian` 40 → 10. Thêm `warn_dark_mean` = 60, `warn_blur_laplacian` = 40.
- `measure` trả thêm `p95`. `CaptureReport` có thêm `warnings`. `ok` chỉ còn `False` ở mức chặn.
- `pipeline.py` không đổi: ảnh có `warnings` vẫn được gửi cho VLM; prompt mô tả đã có bước tự kiểm tra ảnh.

## 4. Giới hạn

- Thống kê toàn ảnh tách ảnh xấu khỏi ảnh tốt rất kém ở cả hai luật. Ngưỡng mới chủ ý chọn "ít chặn nhầm" và để VLM
  xử lý phần còn lại; tỉ lệ bắt ảnh xấu giảm theo.
- Chưa có ảnh bảng đen, màn hình chụp bằng điện thoại của nhóm (kịch bản D9). Nên bổ sung khoảng 20 ảnh để kiểm lại.
