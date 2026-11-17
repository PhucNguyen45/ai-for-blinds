# Kịch bản tương tác bằng lời — app SgBe

Người phụ trách: Toàn (Mảng C). Áp dụng cho bản MVP (Cổng 1, 13/12/2026).

Người dùng không nhìn màn hình. Mỗi bước dưới đây ghi rõ người dùng **làm** gì, app **nói** gì, và **âm báo** nào phát ra. Câu nói nằm trong `lib/strings.dart`; sửa văn phong ở đó.

## Quy ước

- **Chạm**: khi không bật TalkBack, chạm một lần. Khi bật TalkBack, chạm một lần để nghe nhãn, chạm hai lần để kích hoạt.
- **Nút âm lượng**: nút tăng hoặc giảm đều được, chỉ có tác dụng ở màn hình chính.
- Bốn âm báo: **chụp** (một tiếng ngắn, cao), **chờ** (hai nhịp nhẹ, lặp mỗi 3 giây), **xong** (hai nốt đi lên), **lỗi** (hai nốt đi xuống).

## Kịch bản 1 — Mở app lần đầu

| Bước | Người dùng | App nói | Âm |
|---|---|---|---|
| 1 | Mở app | "SgBe sẵn sàng. Chạm vào giữa màn hình hoặc bấm nút âm lượng để chụp trang sách." | — |
| 2 | (Android hỏi quyền camera) | — | — |
| 2a | Cho phép | Không nói gì thêm, camera bật | — |
| 2b | Từ chối, rồi chạm để chụp | "SgBe chưa được phép dùng camera. Bạn mở cài đặt điện thoại và cấp quyền camera cho SgBe." | lỗi |

Nếu máy chưa có giọng tiếng Việt: app nói một câu tiếng Anh hướng dẫn cài giọng (vì không có giọng Việt để nói), màn hình hiện cảnh báo đỏ kèm nút lớn "Mở cài đặt giọng đọc".

## Kịch bản 2 — Chụp và nghe một trang (luồng chính)

| Bước | Người dùng | App nói | Âm |
|---|---|---|---|
| 1 | Đặt sách lên bàn, cầm máy cao khoảng 30 cm | — | — |
| 2 | Chạm giữa màn hình hoặc bấm nút âm lượng | "Đang đọc trang, xin chờ." | chụp |
| 3 | Chờ | Sau 20 giây nếu chưa xong: "Vẫn đang đọc trang này, xin chờ thêm." | chờ, lặp mỗi 3 giây |
| 4 | — | Đọc mô tả trang (văn nói do máy chủ trả về) | xong |
| 5 | Nghe hết, app về trạng thái sẵn sàng | — | — |

Nếu máy chủ báo có chỗ không đọc được, sau mô tả app nói thêm: "Có chỗ mình không đọc được. Bạn có thể chụp lại, giữ máy thẳng và đủ sáng."

## Kịch bản 3 — Dừng giữa chừng và nghe lại

| Bước | Người dùng | App nói | Âm |
|---|---|---|---|
| 1 | Đang nghe mô tả, chạm giữa màn hình (hoặc nút âm lượng) | Dừng đọc ngay | — |
| 2 | Chạm nút "Đọc lại" | Đọc lại mô tả từ đầu | — |
| 3 | Chạm giữa màn hình lần nữa | Chụp trang mới (như kịch bản 2) | chụp |

Chạm khi app đang chờ máy chủ: app nói "Đang đọc trang, xin chờ." và không gửi thêm ảnh.

## Kịch bản 4 — Lỗi

Mọi lỗi đều báo bằng giọng nói kèm âm **lỗi**, không dùng thông báo chỉ hiện trên màn hình.

| Tình huống | App nói |
|---|---|
| Máy chủ trả lỗi | Đọc nguyên câu `error.message` của máy chủ (đã viết sẵn cho người dùng, theo hợp đồng AI v0.1 và API v1) |
| Mất Wi-Fi, sai địa chỉ máy chủ | "Không kết nối được máy chủ. Bạn kiểm tra Wi-Fi và địa chỉ máy chủ trong Cài đặt." |
| Máy chủ quá 130 giây không trả lời | "Máy chủ trả lời quá lâu. Bạn thử chụp lại nhé." |
| Máy chủ trả dữ liệu không đúng hợp đồng | "Máy chủ trả về dữ liệu lạ. Bạn thử lại sau nhé." |

Sau lỗi, chạm giữa màn hình là chụp lại ngay.

## Kịch bản 5 — Cài đặt (thường do người hỗ trợ làm lần đầu)

| Bước | Người dùng | App nói |
|---|---|---|
| 1 | Chạm "Cài đặt" | (mở màn hình Cài đặt; nút âm lượng trở lại chỉnh âm lượng) |
| 2 | Nhập địa chỉ máy chủ, chạm "Kiểm tra kết nối" | "Đã kết nối máy chủ." hoặc câu lỗi. Nếu máy chủ ở chế độ thử: thêm "Máy chủ đang ở chế độ thử, câu trả lời chưa phải từ mô hình thật." |
| 3 | Kéo thanh "Tốc độ đọc" rồi thả | "Đây là tốc độ đọc hiện tại." ở tốc độ mới |
| 4 | Chọn "Loại trang" | "Loại trang: Bản đồ. Đã lưu." |
| 5 | Bật "Chế độ demo" | "Chế độ demo bật." Từ đó app trả lời mẫu, không gửi ảnh đi đâu |
| 6 | Quay lại | Về màn hình chính, nút âm lượng lại là nút chụp |

## Chưa có trong MVP (Giai đoạn 2)

- Hỏi tiếp bằng giọng nói trên cùng ảnh (`/v1/ask`, cần STT của Phúc).
- Thư viện offline: duyệt sách → bài → trang bằng cử chỉ vuốt.
- Lịch sử, sao chép, chia sẻ mô tả.
