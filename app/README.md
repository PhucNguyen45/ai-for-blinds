# SgBe — app Android

App Flutter cho học sinh khiếm thị: chụp trang sách, nghe mô tả bằng giọng tiếng Việt. Người phụ trách: Toàn (Mảng C). Gọi máy chủ theo hợp đồng `../docs/API_v1.md`.

## Chạy thử nhanh nhất (không cần điện thoại, không cần máy chủ)

```
flutter pub get
flutter test
```

25 test, gồm kiểm tra trợ năng tự động (nhãn TalkBack, vùng chạm, tương phản) và đọc phản hồi thật của backend lưu trong `test/fixtures/`.

## Chạy trên máy ảo hoặc điện thoại

1. Chạy máy chủ ở chế độ thử (xem `../README.md`):
   ```
   cd ../backend
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```
2. Chạy app:
   ```
   flutter run
   ```
3. Trong app, mở **Cài đặt**:
   - Máy ảo Android: giữ địa chỉ mặc định `http://10.0.2.2:8000`.
   - Điện thoại thật cùng Wi-Fi: nhập IP LAN của laptop, ví dụ `http://192.168.1.15:8000`. Có thể phải mở cổng 8000 trên Windows Firewall.
   - Chạm **Kiểm tra kết nối**: app đọc to kết quả.
   - Không có máy chủ: bật **Chế độ demo**.

Điện thoại phải có dữ liệu giọng tiếng Việt: Cài đặt → Trợ năng → Chuyển văn bản thành giọng nói → Google → tải Tiếng Việt. Thiếu giọng, app báo bằng tiếng Anh và hiện nút mở cài đặt giọng.

Hướng dẫn bật gỡ lỗi USB, chạy không dây, build APK: `Desktop\NCKH\HUONG-DAN-BUILD-APP.md`.

## Thao tác

| Làm gì | Kết quả |
|---|---|
| Chạm vùng camera (TalkBack: chạm hai lần) hoặc bấm nút âm lượng | Chụp và đọc trang |
| Làm lại thao tác trên khi đang đọc | Dừng đọc |
| Nút **Đọc lại** | Đọc lại mô tả gần nhất |
| Nút **Chọn ảnh** | Đọc một ảnh có sẵn trong máy |
| Nút **Cài đặt** | Máy chủ, tốc độ đọc, loại trang, chế độ demo |

Kịch bản đầy đủ: `docs/KICH_BAN_TUONG_TAC.md`.

## Cấu trúc

```
lib/
  main.dart                 khởi động: nạp cài đặt, giọng đọc, lời chào
  strings.dart              MỌI câu app nói và chữ hiển thị — sửa văn phong ở đây
  api/
    api_client.dart         gọi API v1, đọc {data, error}, đổi lỗi mạng thành câu nói
    demo_api.dart           trả lời mẫu cho chế độ demo
    models.dart             kiểu dữ liệu theo hợp đồng
  reader/
    reader_controller.dart  luồng chụp → gửi → nghe, không phụ thuộc giao diện
  services/
    capture_source.dart     camera trong app + chọn ảnh
    speech.dart             giọng đọc (flutter_tts, vi-VN)
    earcons.dart            4 âm báo trạng thái
    settings_store.dart     cài đặt lưu trên máy
    platform_bridge.dart    nút âm lượng, mở cài đặt giọng đọc (nối sang MainActivity.kt)
  ui/
    home_screen.dart        màn hình chính
    settings_screen.dart    cài đặt
    big_button.dart, theme.dart
android/app/src/main/kotlin/vn/nckh/sgbe/MainActivity.kt   bắt nút âm lượng
assets/audio/               âm báo, sinh bằng tool/tao_am_bao.py
test/                       test tự động + phản hồi thật của backend
docs/                       kịch bản tương tác, checklist trợ năng, yêu cầu giao diện (SRS)
```

## Các quyết định thiết kế

- **Camera trong app** (gói `camera`), không mở app camera hệ thống: bước "Đồng ý / Chụp lại" của camera hệ thống khó dùng khi không nhìn.
- **Nút âm lượng chụp ảnh** chỉ ở màn hình chính. Sang Cài đặt, nút trở lại chỉnh âm lượng.
- **App tự đọc bằng TTS**, không nhờ TalkBack, để người không bật TalkBack cũng nghe được. Vì vậy chữ trạng thái không đặt `liveRegion`, tránh hai giọng đọc chồng nhau.
- **Lỗi luôn đọc thành tiếng**, không dùng SnackBar. Lỗi của máy chủ đọc nguyên `error.message`, vì câu đó đã được viết sẵn cho người dùng.
- **Ảnh 1920×1080**: đủ nét cho chữ SGK, thường dưới giới hạn 10 MB của máy chủ. Đổi ở `DeviceCaptureSource.resolution` nếu mô hình đọc sót chữ nhỏ.

## Chưa làm (Giai đoạn 2)

- Hỏi tiếp bằng giọng nói (`/v1/ask`): chờ STT PhoWhisper của Phúc.
- Thư viện offline (`/v1/library`).
- Lịch sử, sao chép, chia sẻ mô tả.
