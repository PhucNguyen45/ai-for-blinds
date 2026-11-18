# Cổng kiểm tra chất lượng ảnh — đo trên tập huấn luyện tổng hợp

- Ngưỡng: Thresholds(dark_mean=60.0, blur_laplacian=40.0, overexposed_mean=235.0, overexposed_std=15.0, analysis_size=640)
- Tập: `v1`, 1200 ảnh (tổng hợp, cục bộ)

| Nhãn thật | Số ảnh | Cổng báo `dark` | `blur` | `glare` | Cho qua (`ok`) | Bắt đúng |
|---|---|---|---|---|---|---|
| blur | 21 | 0 | 21 | 0 | 0 | 21/21 (100%) |
| cropped_bottom | 16 | 0 | 0 | 0 | 16 | 0/16 (0%) |
| cropped_left | 12 | 0 | 0 | 0 | 12 | 0/12 (0%) |
| cropped_right | 26 | 0 | 0 | 0 | 26 | 0/26 (0%) |
| cropped_top | 20 | 0 | 0 | 0 | 20 | 0/20 (0%) |
| dark | 33 | 33 | 0 | 0 | 0 | 33/33 (100%) |
| glare | 27 | 0 | 0 | 10 | 17 | 10/27 (37%) |
| ok | 683 | 0 | 0 | 0 | 683 | 683/683 (100%) |
| ok_mild | 362 | 0 | 0 | 0 | 362 | 362/362 (100%) |

**Báo nhầm trên ảnh đạt:** 0/1045 (0.0%).

Các loại `cropped_*` và phần lớn `glare` cổng KHÔNG bắt (0% ở cột Bắt đúng là đúng thiết kế, không phải lỗi): lỗi cắt mép phụ thuộc nội dung nên giao cho VLM (prompt `b0g_v1`).

Giới hạn: ảnh tổng hợp với lỗi rõ rệt; ngưỡng cần hiệu chỉnh lại trên ảnh chụp thật.
