# Yêu cầu giao diện — phần đóng góp cho SRS

Người viết: Toàn (Mảng C). Theo cấu trúc yêu cầu của ISO/IEC/IEEE 29148:2018: mỗi yêu cầu có mã, câu "phải", lý do, và cách kiểm chứng.

Mức ưu tiên: **B** = bắt buộc cho Cổng 1 (13/12/2026), **N** = nên có, làm ở Giai đoạn 2.

## 1. Thao tác chính

| Mã | Yêu cầu | Ưu tiên | Lý do | Kiểm chứng |
|---|---|---|---|---|
| UI-01 | App phải cho chụp trang bằng một thao tác: chạm vùng camera hoặc bấm nút âm lượng. | B | Người không nhìn khó tìm một nút nhỏ trên màn hình phẳng. | Test A5, A6; kiểm tay B4 |
| UI-02 | App phải chụp ngay trong app, không qua bước xác nhận của app camera hệ thống. | B | Bước "Đồng ý / Chụp lại" của camera hệ thống khó dùng khi không nhìn. | Kiểm tay B1 |
| UI-03 | Khi đang đọc, thao tác chụp phải dừng đọc thay vì chụp. | B | Người dùng cần một cách dừng giọng đọc mà không phải tìm nút. | Test "đang nói mà chạm" |
| UI-04 | Khi đang chờ máy chủ, app không được gửi thêm ảnh. | B | Tránh gửi trùng, tốn chi phí gọi mô hình. | Test "đang gửi: không gửi trùng" |
| UI-05 | App phải có nút "Đọc lại" mô tả gần nhất. | B | Nghe không kịp là chuyện thường xuyên. | Test "đọc lại mô tả gần nhất" |
| UI-06 | App phải cho chọn ảnh có sẵn trong máy. | N | Thử nghiệm trên máy ảo, đọc lại ảnh chụp trước. | Kiểm tay |

## 2. Phản hồi

| Mã | Yêu cầu | Ưu tiên | Lý do | Kiểm chứng |
|---|---|---|---|---|
| UI-10 | Mọi trạng thái phải có âm báo: chụp, đang chờ (lặp mỗi 3 giây), xong, lỗi. | B | Người dùng không thấy vòng quay "đang tải". | Test A5, A7; kiểm tay B8 |
| UI-11 | Nếu chờ quá 20 giây, app phải nói câu nhắc đang xử lý. | B | Im lặng lâu làm người dùng tưởng app treo. | Test "đang gửi…" |
| UI-12 | Mọi lỗi phải được đọc thành tiếng; lỗi của máy chủ đọc nguyên `error.message`. | B | Hợp đồng API v1; thông báo chỉ hiện chữ là vô dụng với người dùng. | Test A7 |
| UI-13 | Mỗi lần chạm nút phải có rung phản hồi. | B | Xác nhận đã chạm trúng. | Kiểm tay B7 |
| UI-14 | Nếu mô tả có chỗ không đọc được (`unreadable`), app phải gợi ý chụp lại kèm cách chụp. | B | Nghiên cứu cho thấy người khiếm thị khó tự phát hiện lỗi của AI. | Test "có chỗ không đọc được" |
| UI-15 | App phải tự đọc bằng TTS, kể cả khi không bật TalkBack. | B | Nhiều học sinh không dùng TalkBack thường xuyên. | Kiểm tay B2 |
| UI-16 | App không được để TalkBack và TTS của app đọc chồng lên nhau. | B | Hai giọng cùng lúc thì không nghe được gì. | Kiểm tay B3 |

## 3. Hiển thị và trợ năng

| Mã | Yêu cầu | Ưu tiên | Lý do | Kiểm chứng |
|---|---|---|---|---|
| UI-20 | Mọi phần tử bấm được phải có nhãn TalkBack bằng tiếng Việt. | B | Điều kiện tối thiểu để dùng với trình đọc màn hình. | Test A1 |
| UI-21 | Vùng chạm tối thiểu 80 dp; vùng chụp chiếm phần lớn màn hình. | B | Dễ chạm trúng khi không nhìn. | Test A2, A3 |
| UI-22 | Tương phản chữ phải đạt chuẩn WCAG; nền đen, chữ trắng, điểm nhấn vàng. | B | Hỗ trợ học sinh thị lực kém. | Test A4 |
| UI-23 | Bố cục không được tràn hay mất chữ khi phóng chữ hệ thống tới 200%. | B | Người thị lực kém thường phóng chữ. | Kiểm tay B6 |
| UI-24 | Màn hình phải hiện chữ của mô tả đang đọc. | B | Học sinh thị lực kém và người hỗ trợ đọc kèm. | Test A5 |
| UI-25 | App chỉ chạy ở chiều dọc. | B | Giữ vị trí các nút cố định để người dùng nhớ. | Kiểm tay |

## 4. Cấu hình

| Mã | Yêu cầu | Ưu tiên | Lý do | Kiểm chứng |
|---|---|---|---|---|
| UI-30 | Địa chỉ máy chủ phải sửa được trong Cài đặt, không phải build lại app. | B | IP của laptop đổi theo mạng Wi-Fi. | Kiểm tay |
| UI-31 | Cài đặt phải có nút kiểm tra kết nối, kết quả đọc thành tiếng. | B | Người hỗ trợ cài đặt biết ngay máy chủ có thông không. | Kiểm tay |
| UI-32 | Tốc độ đọc phải chỉnh được từ 0,3 tới 1,0 và nghe thử ngay. | B | Người quen trình đọc màn hình nghe rất nhanh. | Kiểm tay B9 |
| UI-33 | App phải có chế độ demo trả lời mẫu, không gửi ảnh đi. | N | Làm quen app và thử giao diện khi không có máy chủ. | Kiểm tay |
| UI-34 | Nếu máy thiếu giọng tiếng Việt, app phải báo và có nút mở cài đặt giọng đọc. | B | Thiếu giọng thì app im lặng hoàn toàn. | Test A8 |

## 5. Giao tiếp với máy chủ

| Mã | Yêu cầu | Ưu tiên | Lý do | Kiểm chứng |
|---|---|---|---|---|
| UI-40 | App phải gọi đúng hợp đồng API v1: `POST /v1/describe` (multipart `image`, `page_type`), đọc dạng `{data, error}`. | B | Hợp đồng chung giữa ba mảng. | `api_client_test.dart` với phản hồi thật của backend |
| UI-41 | App phải chờ tối đa 130 giây cho `/v1/describe` và `/v1/ask`. | B | Hợp đồng v1: máy chủ chờ mô hình tối đa 120 giây. | Test "quá giờ" |
| UI-42 | App phải giữ `image_id` của lần mô tả gần nhất. | B | Cần cho hỏi tiếp ở Giai đoạn 2. | Test "thành công…" |
| UI-43 | App phải hỏi tiếp bằng giọng nói trên cùng ảnh, gửi kèm lịch sử hỏi đáp. | N | Tính năng mạnh nhất của Be My AI mà đề tài cần có. | Giai đoạn 2 |
| UI-44 | App phải tải kho mô tả SGK về máy và đọc offline. | N | Học sinh ở nơi mạng yếu vẫn học được. | Giai đoạn 2 |
