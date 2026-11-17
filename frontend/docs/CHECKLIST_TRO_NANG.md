# Checklist trợ năng — app SgBe

Người phụ trách: Toàn. Mỗi bản phát hành phải qua hết các mục. Cột **Cách kiểm** cho biết mục nào máy tự kiểm (`flutter test`) và mục nào phải kiểm tay trên điện thoại thật.

Trạng thái ghi theo bản ngày 19/10/2026 (nhánh `toan/app-mvp`).

## A. Máy tự kiểm — chạy `flutter test`

| # | Yêu cầu | Test | Trạng thái |
|---|---|---|---|
| A1 | Mọi nút có nhãn đọc được bằng TalkBack | `labeledTapTargetGuideline`; tìm nhãn từng nút | Đạt |
| A2 | Vùng chạm ≥ 48 dp (chuẩn Android) | `androidTapTargetGuideline` | Đạt |
| A3 | Nút chính cao ≥ 80 dp (chuẩn của nhóm, cao hơn chuẩn Android) | "nút lớn cao ít nhất 80 điểm ảnh logic" | Đạt |
| A4 | Tương phản chữ đạt chuẩn WCAG | `textContrastGuideline`, cả màn hình chính và Cài đặt | Đạt |
| A5 | Chạm vùng camera thì chụp, gửi, đọc mô tả | "chạm vùng camera…" | Đạt |
| A6 | Nút âm lượng cũng chụp được | "bấm nút âm lượng cũng chụp" | Đạt |
| A7 | Lỗi được báo bằng giọng nói, không chỉ hiện chữ | test lỗi trong `reader_controller_test.dart`, "camera bị từ chối quyền…" | Đạt |
| A8 | Thiếu giọng tiếng Việt thì có cảnh báo và nút mở cài đặt giọng | "thiếu giọng tiếng Việt…" | Đạt |
| A9 | Không tràn bố cục khi chữ to | Mọi test giao diện (Flutter báo lỗi nếu tràn) | Đạt ở cỡ chữ mặc định |

## B. Kiểm tay trên điện thoại thật — làm trước mỗi buổi demo

| # | Yêu cầu | Cách kiểm | Trạng thái |
|---|---|---|---|
| B1 | Dùng được trọn kịch bản 2 khi **bật TalkBack** | Bật TalkBack, nhắm mắt, làm từ mở app tới nghe xong một trang | Chưa kiểm |
| B2 | Dùng được trọn kịch bản 2 khi **tắt hẳn màn hình** (độ sáng 0 hoặc che màn hình) | Như B1 | Chưa kiểm |
| B3 | TalkBack và giọng của app không đọc chồng lên nhau | Bật TalkBack, chụp một trang, nghe có hai giọng cùng lúc không | Chưa kiểm |
| B4 | Nút âm lượng chụp được khi TalkBack bật | Bật TalkBack, bấm nút giảm âm lượng ở màn hình chính | Chưa kiểm |
| B5 | Ở màn hình Cài đặt, nút âm lượng chỉnh âm lượng bình thường | Mở Cài đặt, bấm nút âm lượng | Chưa kiểm |
| B6 | Phóng chữ hệ thống lên 200% không tràn, không mất chữ | Cài đặt Android → Cỡ chữ lớn nhất, mở từng màn hình | Chưa kiểm |
| B7 | Rung khi chạm mọi nút | Chạm từng nút | Chưa kiểm |
| B8 | Âm báo nghe rõ, phân biệt được 4 loại | Nhờ một người nghe thử, không nhìn màn hình | Chưa kiểm |
| B9 | Tốc độ đọc mặc định không quá chậm với người quen dùng trình đọc màn hình | Hỏi người dùng khiếm thị ở buổi thử nghiệm | Chưa kiểm |
| B10 | Ảnh chụp trong nhà, ánh đèn thường, vẫn đọc được chữ SGK | Chụp 5 trang SGK, so mô tả với trang thật | Chưa kiểm |

## C. Quy tắc thiết kế (rà khi review code)

- [x] Nền đen, chữ trắng, điểm nhấn vàng; không gradient, không bóng đổ
- [x] Chữ thân ≥ 20, chữ nút ≥ 20 (nút hẹp) hoặc 24
- [x] Không dùng màu làm kênh thông tin duy nhất: trạng thái lỗi có cả chữ "Có lỗi" và âm báo
- [x] Không dùng SnackBar hay hộp thoại chỉ có chữ để báo lỗi
- [x] Không dùng từ chỉ vị trí thị giác trong câu nói ("bên trái", "phía trên")
- [x] Chữ trạng thái không đặt `liveRegion`, vì app đã tự đọc bằng TTS (tránh hai giọng chồng nhau)
- [x] Mọi câu nói tập trung ở `lib/strings.dart`
