# Hợp đồng API v1 — SgBe

Người viết và giữ: Nam. Nội dung trường `description`/`answer`: Toàn. Người dùng: Phúc (app Flutter).
Mọi thay đổi hợp đồng phải qua pull request có cả ba người duyệt.

Tài liệu tương tác (thử gọi ngay trên trình duyệt): `http://<máy chủ>:8000/docs`

## Quy ước chung

- Mọi phản hồi đều có dạng:
  ```json
  { "data": { ... } | null, "error": null | { "code": "MA_LOI", "message": "Câu tiếng Việt" } }
  ```
- App đọc `data` khi `error == null`. Khi có lỗi, app **đọc thẳng `error.message` bằng giọng nói** (đã viết sẵn cho người dùng), dùng `error.code` để quyết định hành động.
- `description` và `answer` là **văn nói thuần**: không markdown, đưa thẳng vào TTS.
- Timeout phía app nên đặt **≥ 130 giây** cho `/v1/describe` và `/v1/ask` (máy chủ chờ mô hình tối đa 120 giây).

## POST /v1/describe

Gửi `multipart/form-data`:

| Trường | Kiểu | Bắt buộc | Ghi chú |
|---|---|---|---|
| `image` | file (jpg/png/webp) | có | tối đa 10 MB, máy chủ tự xoay và thu nhỏ |
| `page_type` | chuỗi | không | `auto` (mặc định), `text`, `map`, `chart`, `table`, `figure`, `mixed` |

`mixed` = trang vừa có chữ vừa có hình (đề xuất thêm so với lộ trình, cần cả nhóm duyệt).
`auto` = để mô hình tự nhận loại trang.

Kết quả `data`:

```json
{
  "image_id": "667874ee73cca351",
  "description": "Trang có một lược đồ vùng Tây Nguyên. Phía trên lược đồ là hướng Bắc. ...",
  "page_type": "map",
  "unreadable": false,
  "model": "qwen/qwen3-vl-30b-a3b-instruct",
  "prompt_version": "v1",
  "latency_ms": 8421,
  "cached": false
}
```

- Giữ `image_id` để hỏi tiếp ở `/v1/ask`.
- `unreadable = true`: có chỗ mô hình không đọc được → app có thể gợi ý "Bạn có muốn chụp lại không?".
- `cached = true`: ảnh giống hệt đã gửi trước đó, trả ngay, không tốn tiền gọi mô hình.

## POST /v1/ask

Gửi JSON:

```json
{
  "image_id": "667874ee73cca351",
  "question": "Sông nào chảy qua vùng này?",
  "history": [
    { "question": "Có mấy tỉnh?", "answer": "Lược đồ có năm tỉnh." }
  ]
}
```

`history` là các lượt hỏi đáp trước trên cùng ảnh, cũ nhất trước (máy chủ dùng 6 lượt gần nhất).
Kết quả `data`: `{ "image_id", "answer", "model", "prompt_version", "latency_ms" }`.

## POST /v1/stt

`multipart/form-data`, trường `audio` (WAV/M4A, tối đa 10 MB). Kết quả `data`: `{ "text", "latency_ms" }`.
Hiện đang ở chế độ giả (luôn trả một câu cố định). Toàn sẽ nối PhoWhisper, hợp đồng giữ nguyên.

## GET /v1/library

Kết quả `data`: danh sách `{ "book", "title", "page_count" }`.

## GET /v1/library/{book}/pages

Kết quả `data`: `{ "book", "title", "pages": [ ... ] }`, mỗi trang:

```json
{
  "book": "demo", "page": 2, "page_type": "map",
  "description": "...", "image_sha256": "...",
  "model": "mock", "prompt_version": "v1", "reviewed": false
}
```

App tải về và lưu máy để nghe offline. Nên ưu tiên đọc trang có `reviewed = true` (đã có người kiểm tra).

## GET /health

Kiểm tra máy chủ sống, đang ở chế độ nào: `{ "status", "vlm_mode", "model", "prompt_version", "stt_mode" }`.
App nên gọi khi mở hoặc khi đổi địa chỉ máy chủ trong Cài đặt.

## Bảng mã lỗi

| HTTP | `code` | Khi nào | Gợi ý xử lý ở app |
|---|---|---|---|
| 400 | `INVALID_IMAGE` | file không phải ảnh | đọc message, mở lại camera |
| 413 | `IMAGE_TOO_LARGE` | ảnh > 10 MB | nén ảnh trước khi gửi |
| 422 | `INVALID_REQUEST` | thiếu trường, `page_type` sai | lỗi lập trình, ghi log |
| 404 | `IMAGE_NOT_FOUND` | `image_id` không còn | đọc message, mời chụp lại |
| 404 | `BOOK_NOT_FOUND` | mã sách sai | làm mới thư viện |
| 400 | `INVALID_AUDIO` | ghi âm rỗng | mời nói lại |
| 413 | `AUDIO_TOO_LARGE` | ghi âm quá dài | giới hạn thời gian ghi |
| 503 | `STT_UNAVAILABLE` | STT chưa bật | ẩn nút hỏi bằng giọng |
| 504 | `VLM_TIMEOUT` | mô hình quá 120 giây | đọc message, cho thử lại |
| 502 | `VLM_ERROR` | mô hình lỗi, hết credit, mất mạng | đọc message, cho thử lại |
| 500 | `INTERNAL` | lỗi khác | đọc message |

## Ghi chú cho Phúc khi kết nối từ điện thoại

- Máy chủ chạy trên laptop: `uvicorn app.main:app --host 0.0.0.0 --port 8000` (phải có `--host 0.0.0.0`).
- Điện thoại thật cùng Wi-Fi: dùng IP LAN của laptop, ví dụ `http://192.168.1.15:8000`. Trên Windows có thể phải mở cổng 8000 trong Windows Firewall.
- Máy ảo Android: dùng `http://10.0.2.2:8000`.
- Vì dùng `http://`, AndroidManifest cần `android:usesCleartextTraffic="true"`.
- Chế độ mock có độ trễ giả 1 giây (`MOCK_DELAY_SECONDS`) để thử âm báo "đang xử lý"; đặt 15 để thử trường hợp chậm.
