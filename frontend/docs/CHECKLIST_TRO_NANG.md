# Checklist trợ năng — app SgBe

Người phụ trách: Toàn. Mỗi bản phát hành phải qua hết các mục. Cột **Cách kiểm** cho biết mục nào máy tự kiểm (`flutter test`) và mục nào phải kiểm tay trên điện thoại thật.

Trạng thái các mục A1–A12 và B1–B11 ghi theo bản giao diện ngày 18/11/2026. Ngày 27/11/2026 `flutter test`: 124 đạt, 3 bỏ qua.

## A. Máy tự kiểm — chạy `flutter test`

| # | Yêu cầu | Test | Trạng thái |
|---|---|---|---|
| A1 | Mọi nút có nhãn đọc được bằng TalkBack | `labeledTapTargetGuideline`; tìm nhãn từng nút | Đạt |
| A2 | Vùng chạm ≥ 48 dp (chuẩn Android) | `androidTapTargetGuideline` | Đạt |
| A3 | Nút chính cao ≥ 80 dp (chuẩn của nhóm, cao hơn chuẩn Android) | "mọi nút cao ít nhất 80…" | Đạt |
| A4 | Tương phản chữ đạt chuẩn WCAG | `textContrastGuideline` trên màn hình chính, Hỏi, Thư viện, đọc sách, Cài đặt, Cho người hỗ trợ | Đạt |
| A5 | Chạm hai lần vùng chụp thì chụp, gửi, đọc và hiện mô tả; chạm một lần chỉ đọc tên | "chạm hai lần vùng chụp…", "chạm một lần vùng chụp…" | Đạt |
| A6 | Nút âm lượng cũng chụp được | "bấm nút âm lượng cũng chụp" | Đạt |
| A7 | Lỗi được báo bằng giọng nói, không chỉ hiện chữ | test lỗi trong `reader_controller_test.dart`, "camera bị từ chối quyền…" | Đạt |
| A8 | Thiếu giọng tiếng Việt thì có cảnh báo và nút mở cài đặt giọng | "thiếu giọng tiếng Việt…" | Đạt |
| A9 | Không tràn bố cục khi chữ to hoặc màn hình nhỏ | "phóng chữ hệ thống 200%…", "màn hình nhỏ 360×640…" đi qua mọi màn hình | Đạt |
| A10 | Rê ngón tay đọc tên từng nút, không dùng nút | "rê ngón tay qua ba nút…" | Đạt |
| A11 | TalkBack bật thì app nhường, không tự đọc tên nút | "TalkBack bật thì app nhường…" | Đạt |
| A12 | Bản release mở được (không treo ở màn hình chờ) | `tool/kiem_va_build.ps1 -CaiLenMay` rồi mở app trên máy ảo | Đạt (18/11, sau khi thêm `android/app/proguard-rules.pro`) |

## B. Kiểm tay trên điện thoại thật — làm trước mỗi buổi demo

| # | Yêu cầu | Cách kiểm | Trạng thái |
|---|---|---|---|
| B1 | Dùng được trọn kịch bản 2 khi **bật TalkBack** | Bật TalkBack, nhắm mắt, làm từ mở app tới nghe xong một trang | Chưa kiểm |
| B2 | Dùng được trọn kịch bản 2 khi **tắt hẳn màn hình** (độ sáng 0 hoặc che màn hình) | Như B1 | Chưa kiểm |
| B3 | TalkBack và giọng của app không đọc chồng lên nhau | Bật TalkBack, chụp một trang, nghe có hai giọng cùng lúc không | Chưa kiểm |
| B4 | Nút âm lượng chụp được khi TalkBack bật | Bật TalkBack, bấm nút giảm âm lượng ở màn hình chính | Chưa kiểm |
| B5 | Ở màn hình Cài đặt, nút âm lượng chỉnh âm lượng bình thường | Mở Cài đặt, bấm nút âm lượng | Chưa kiểm |
| B6 | Phóng chữ hệ thống lên 200% không tràn, không mất chữ | Cài đặt Android → Cỡ chữ lớn nhất, mở từng màn hình | Chưa kiểm |
| B7 | Rung khi chạm mọi nút; chạm một lần rung nhẹ, chạm hai lần rung vừa, lỗi rung ba nhịp | Chạm từng nút | Chưa kiểm |
| B11 | Học sinh tự dò được ba vùng bằng chạm nghe / rê ngón mà không ai chỉ | Nhờ người dùng khiếm thị thử, không giải thích trước | Chưa kiểm |
| B8 | Âm báo nghe rõ, phân biệt được 6 loại (tách, mở, chụp, chờ, xong, lỗi) | Nhờ một người nghe thử, không nhìn màn hình | Chưa kiểm |
| B9 | Tốc độ đọc mặc định không quá chậm với người quen dùng trình đọc màn hình | Hỏi người dùng khiếm thị ở buổi thử nghiệm | Chưa kiểm |
| B10 | Ảnh chụp trong nhà, ánh đèn thường, vẫn đọc được chữ SGK | Chụp 5 trang SGK, so mô tả với trang thật | Chưa kiểm |
| B12 | Lời nhắc ngắm máy đúng lúc, không trễ đến mức vô ích, không nhắc dồn | Điện thoại thật: chụp trong chỗ tối, chỗ chói, cố ý rung tay | Chưa kiểm |
| B13 | Lời nhắc ngắm máy không đọc chồng lên TalkBack | Bật TalkBack, đứng ở màn hình chụp trong chỗ tối | Chưa kiểm |
| B14 | Âm "khung hình ổn" không lẫn với âm chạm một lần | Nhờ một người nghe, không nhìn màn hình | Chưa kiểm |
| B15 | Camera chụp được bình thường khi bật hướng dẫn; xem trước không giật, máy không nóng bất thường sau 5 phút | Bật và tắt hướng dẫn, so sánh | Chưa kiểm |
| B16 | Ngưỡng không chặn nhầm bảng đen, tivi, trang nền đen | Chụp mỗi loại 5 ảnh, xem số liệu trong "Cho người hỗ trợ" | Chưa kiểm |

## C. Quy tắc thiết kế (rà khi review code)

- [x] Nền đen, chữ trắng, điểm nhấn vàng gạch dẫn đường; gradient chỉ dùng làm lớp tối dưới chữ nằm trên hình camera (tăng tương phản), không trang trí
- [x] Phông Be Vietnam Pro đóng gói trong app; chữ đọc ≥ 21, chữ nút ≥ 17, tự thu nhỏ khi phóng chữ hệ thống thay vì tràn
- [x] Không dùng màu làm kênh thông tin duy nhất: trạng thái lỗi có cả chữ "Có lỗi" và âm báo
- [x] Không dùng SnackBar hay hộp thoại chỉ có chữ để báo lỗi
- [x] Từ chỉ vị trí ("góc trên bên trái") chỉ dùng trong lời hướng dẫn, vì vị trí các nút cố định; câu báo trạng thái không dùng
- [x] Chữ trạng thái không đặt `liveRegion`, vì app đã tự đọc bằng TTS (tránh hai giọng chồng nhau)
- [x] Mọi câu nói tập trung ở `lib/strings.dart`
