# Kịch bản tương tác bằng lời — app SgBe

Người phụ trách: Toàn (Mảng C). Bản giao diện mới ngày 18/11/2026 (nhánh `toan/frontend`), thay bản MVP 19/10.

Người dùng không nhìn màn hình. Mỗi bước ghi rõ người dùng **làm** gì, app **nói** gì, **âm báo** và **rung** nào phát ra. Câu nói nằm trong `lib/strings.dart`; sửa văn phong ở đó. Ảnh chụp màn hình: `docs/anh-giao-dien/`.

## Quy ước thao tác (giống nhau trên mọi màn hình)

| Thao tác | Kết quả | Âm | Rung |
|---|---|---|---|
| **Chạm một lần** vào một nút | Nghe tên nút và việc nó làm; nút được viền trắng | tách nhẹ | ngắn |
| **Chạm hai lần liền** (cách nhau ≤ 0,5 giây) vào cùng nút | Dùng nút đó | hai nốt đi lên | vừa |
| **Giữ và rê ngón tay** | Đi qua nút nào nghe tên nút đó; không dùng nút nào | tách nhẹ | ngắn |
| **Chạm bất kỳ khi app đang đọc** | Dừng đọc ngay, rồi nghe tên chỗ vừa chạm | tách nhẹ | ngắn |
| **Nút âm lượng** (chỉ ở màn hình chính) | Đang đọc thì dừng; còn lại thì **chụp ngay**, không cần chạm hai lần | chụp | mạnh |
| **Bật TalkBack** | App tắt lớp "chạm nghe" của riêng mình; TalkBack đọc nhãn, chạm hai lần để dùng như mọi app | của TalkBack | của TalkBack |

Âm báo trạng thái: **chụp** (một tiếng ngắn, cao), **chờ** (hai nhịp nhẹ, lặp mỗi 3 giây), **xong** (hai nốt đi lên), **lỗi** (hai nốt đi xuống, rung ba nhịp). Tắt được âm báo và rung trong Cài đặt.

## Bố cục: ba vùng, không bao giờ đổi chỗ

```
┌──────────────┬──────────────┐
│   Cài đặt    │   Trợ giúp   │  ← hai góc trên
├──────────────┴──────────────┤
│                             │
│     VÙNG CHỤP (camera)      │  ← giữa, chiếm phần lớn màn hình;
│  kết quả hiện ngay ở đây    │    chụp xong, mô tả hiện tại chỗ
│                             │
├─────────────────────────────┤
│  phụ đề: câu app đang nói   │
├─────────┬─────────┬─────────┤
│ Đọc lại │   Hỏi   │Thư viện │  ← mép dưới
└─────────┴─────────┴─────────┘
```

Ở các màn hình con (Hỏi, Thư viện, Cài đặt), cả dải mép dưới là nút **Quay lại**. Phím quay lại của Android cũng dùng được.

## Kịch bản 1 — Mở app lần đầu

| Bước | Người dùng | App nói | Âm |
|---|---|---|---|
| 1 | Mở app | Màn hình chờ nền tối (không chớp trắng), rồi vào thẳng camera | — |
| 2 | — | Lần đầu: lời hướng dẫn đầy đủ ("Chào bạn, đây là SgBe… Chạm một lần để nghe tên nút. Chạm hai lần để dùng…"). Từ lần hai: "SgBe sẵn sàng. Bấm nút âm lượng, hoặc chạm hai lần vào giữa màn hình để chụp trang sách." | — |
| 3 | (Android hỏi quyền camera) Từ chối, rồi chụp | "SgBe chưa được phép dùng camera…"; vùng chụp hiện thẻ lỗi | lỗi |

Nghe lại hướng dẫn: chạm hai lần **Trợ giúp** (góc trên phải), hoặc Cài đặt → Cho người hỗ trợ → Nghe lại hướng dẫn.

Máy chưa có giọng tiếng Việt: app nói một câu tiếng Anh hướng dẫn cài giọng, màn hình hiện cảnh báo đỏ kèm nút "Mở cài đặt giọng đọc".

## Kịch bản 2 — Chụp và nghe một trang (luồng chính)

| Bước | Người dùng | App nói / hiện | Âm |
|---|---|---|---|
| 1 | Cầm máy cao khoảng 30 cm trên trang sách | Camera tràn màn hình, bốn góc vàng ôm trang | — |
| 2 | Bấm nút âm lượng (hoặc chạm hai lần giữa màn hình) | Màn hình nháy sáng. "Đang đọc trang, xin chờ." Ảnh vừa chụp đứng yên, vạch vàng quét dọc trang | chụp |
| 3 | Chờ | Sau 20 giây nếu chưa xong: "Vẫn đang đọc trang này, xin chờ thêm." | chờ, mỗi 3 giây |
| 4 | — | Thẻ kết quả hiện trong vùng chụp: ảnh nhỏ của trang, loại hình (vd "Biểu đồ cột"), mô tả. App đọc **từng câu**, câu đang đọc được tô vàng và tự cuộn theo | xong |
| 5 | Nghe xong | Về trạng thái sẵn sàng, thẻ kết quả vẫn ở đó | — |

Ảnh đọc được một phần: sau mô tả app nói thêm "Có chỗ mình không đọc được…". Ảnh hỏng hẳn: app giải thích rồi hướng dẫn chụp lại.

## Kịch bản 3 — Dừng, nghe lại, chụp trang mới

| Bước | Người dùng | App nói | Âm |
|---|---|---|---|
| 1 | Đang nghe, chạm bất kỳ đâu (hoặc bấm nút âm lượng) | Dừng đọc ngay | tách |
| 2 | Chạm hai lần **Đọc lại** | Đọc lại mô tả từ đầu, tô câu đang đọc | mở |
| 3 | Chạm hai lần vào thẻ kết quả | "Camera sẵn sàng…" — về camera để chụp trang mới | mở |
| 3' | Hoặc bấm nút âm lượng | Chụp trang mới luôn | chụp |

Chạm khi app đang chờ máy chủ: "Đang đọc trang, xin chờ.", không gửi thêm ảnh.

## Kịch bản 4 — Hỏi thêm về trang vừa chụp

| Bước | Người dùng | App nói / hiện |
|---|---|---|
| 1 | Chạm hai lần **Hỏi** (chưa chụp trang nào) | "Hãy chụp một trang trước khi hỏi." (âm lỗi), không mở màn hình |
| 2 | Chạm hai lần **Hỏi** (đã chụp) | Mở màn hình Hỏi: "Hỏi về trang vừa chụp. Có ba câu hỏi gợi ý…" |
| 3 | Rê ngón qua ba câu gợi ý, chạm hai lần một câu | "Đang hỏi, xin chờ." → câu hỏi hiện thành bong bóng xanh, câu trả lời đọc từng câu, tô vàng |
| 4 | Chạm hai lần thẻ câu trả lời | Nghe lại câu trả lời |
| 5 | Chạm hai lần **Quay lại** | Về màn hình chụp: "Màn hình chụp." |

Mỗi câu hỏi gửi `/v1/ask` kèm `image_id` và các lượt hỏi trước. Hỏi bằng giọng nói sẽ thêm khi xong STT của Mảng A.

## Kịch bản 5 — Thư viện (bản mẫu)

| Bước | Người dùng | App nói |
|---|---|---|
| 1 | Chạm hai lần **Thư viện** | "Thư viện, bản mẫu. Có hai cuốn sách…" |
| 2 | Chạm hai lần một cuốn | Mở sách, đọc ngay: "Tự nhiên và Xã hội 3. Trang 42. Cây đậu lớn lên như thế nào." rồi đọc lời mô tả trang |
| 3 | Chạm hai lần **Trang sau** / **Trang trước** | Đọc trang kế; ở trang cuối: "Đây là trang cuối." |
| 4 | Chạm hai lần **Đọc trang** hoặc thẻ trang | Đọc lại trang hiện tại |

Sách và lời mô tả hiện là dữ liệu mẫu do nhóm tự viết (`assets/library/sach_mau.json`), màn hình ghi rõ "Bản mẫu". Thay bằng kho của Mảng B (`/v1/library`) khi có.

## Kịch bản 6 — Cài đặt

| Mục | Chạm hai lần để | App nói |
|---|---|---|
| Tốc độ đọc | Đổi vòng: Chậm → Bình thường → Nhanh → Rất nhanh | "Tốc độ đọc: Nhanh. Đây là tốc độ đọc hiện tại." (ở tốc độ mới) |
| Âm báo | Bật / tắt | "Âm báo: Tắt." |
| Rung | Bật / tắt | "Rung: Bật." (kèm một lần rung) |
| Đọc ảnh có sẵn | Về màn hình chính, mở thư viện ảnh, đọc ảnh đã chọn | như kịch bản 2 |
| Cho người hỗ trợ | Mở biểu mẫu: địa chỉ máy chủ, kiểm tra kết nối, tốc độ chỉnh tinh 0,3–1,0, loại trang, chế độ demo, giọng đọc của máy, nghe lại hướng dẫn | đọc kết quả từng thao tác |

Ở các màn hình con, nút âm lượng chỉnh âm lượng như bình thường.

## Kịch bản 7 — Lỗi

Mọi lỗi đều báo bằng giọng nói kèm âm **lỗi** và rung ba nhịp; vùng chụp hiện thẻ "Có lỗi" kèm câu giải thích.

| Tình huống | App nói |
|---|---|
| Máy chủ trả lỗi | Đọc nguyên câu `error.message` của máy chủ |
| Mất Wi-Fi, sai địa chỉ máy chủ | "Không kết nối được máy chủ. Bạn kiểm tra Wi-Fi và địa chỉ máy chủ trong Cài đặt." |
| Máy chủ quá 130 giây không trả lời | "Máy chủ trả lời quá lâu. Bạn thử chụp lại nhé." |
| Máy chủ trả dữ liệu không đúng hợp đồng | "Máy chủ trả về dữ liệu lạ. Bạn thử lại sau nhé." |

Sau lỗi: bấm nút âm lượng là chụp lại ngay; hoặc chạm hai lần thẻ lỗi để về camera.
