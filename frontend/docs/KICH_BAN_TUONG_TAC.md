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

## Kịch bản 2a — Hướng dẫn chụp (thêm 27/11/2026, chưa kiểm trên máy thật)

Bật sẵn; tắt ở Cài đặt → Cho người hỗ trợ → Hướng dẫn chụp.

| Tình huống | App nói | Âm / rung |
|---|---|---|
| Đang ngắm, tối kéo dài | "Hơi tối. Bạn đưa ra chỗ sáng hơn." | — |
| Đang ngắm, chói kéo dài | "Bị chói. Bạn nghiêng máy một chút." | — |
| Đang ngắm, mờ kéo dài | "Ảnh đang mờ. Bạn đưa máy ra xa một chút." | — |
| Đang ngắm, máy rung kéo dài | "Bạn giữ yên máy." | — |
| Khung hình đã ổn | (không nói) | âm tách + rung nhẹ, một lần |
| Ảnh vừa chụp hỏng rõ (ví dụ tối) | "Ảnh vừa chụp quá tối. Bạn bật đèn hoặc đưa ra chỗ sáng hơn, rồi chụp lại. Nếu lần chụp tới vẫn vậy, mình sẽ cứ gửi đi đọc." | lỗi |
| Chụp lại vẫn vậy | Gửi đi như bình thường | như kịch bản 2 |

Lưu ý: âm "khung hình ổn" đang dùng chung âm tách với "chạm một lần"; cần nghe thử xem có lẫn không.

## Kịch bản 3 — Dừng, nghe lại, chụp trang mới

| Bước | Người dùng | App nói | Âm |
|---|---|---|---|
| 1 | Đang nghe, chạm bất kỳ đâu (hoặc bấm nút âm lượng) | Dừng đọc ngay | tách |
| 2 | Chạm hai lần **Đọc lại** | Đọc lại mô tả từ đầu, tô câu đang đọc | mở |
| 3 | Chạm hai lần vào thẻ kết quả | "Camera sẵn sàng…" — về camera để chụp trang mới | mở |
| 3' | Hoặc bấm nút âm lượng | Chụp trang mới luôn | chụp |

Chạm khi app đang chờ máy chủ: "Đang đọc trang, xin chờ.", không gửi thêm ảnh.

## Kịch bản 4 — Hỏi thêm về trang vừa chụp (bằng giọng nói)

| Bước | Người dùng | App nói / hiện |
|---|---|---|
| 1 | Chạm hai lần **Hỏi** (chưa chụp trang nào) | "Hãy chụp một trang trước khi hỏi." (âm lỗi), không mở màn hình |
| 2 | Chạm hai lần **Hỏi** (đã chụp) | Mở màn hình Hỏi: "Hỏi về trang vừa chụp. Bấm nút âm lượng, hoặc chạm hai lần nút Nói câu hỏi…" |
| 3 | Bấm nút âm lượng (hoặc chạm hai lần **Nói câu hỏi**, ngay trên Quay lại) | "Mời bạn nói." rồi tiếng mở micro; thẻ giữa màn hình hiện micro vàng, chữ nghe được hiện dần |
| 4 | Nói câu hỏi, ví dụ "Hình vẽ có mấy phần?" | Ngừng nói thì app tự dừng nghe; câu hỏi hiện thành bong bóng xanh; "Đang hỏi, xin chờ." rồi đọc câu trả lời, tô vàng từng câu |
| 5 | Muốn hỏi tiếp | Bấm nút âm lượng lần nữa; câu hỏi sau gửi kèm các lượt trước |
| 6 | Chạm hai lần **Quay lại** | Về màn hình chụp: "Màn hình chụp." |

- Lần đầu nghe, Android hỏi quyền micro.
- Đang nghe mà chạm bất kỳ đâu: dừng nghe ngay (app không đọc tên nút lúc này để giọng app không lọt vào micro).
- Không nghe rõ: "Mình chưa nghe rõ. Bạn bấm nút âm lượng rồi nói lại nhé." Mạng yếu, dịch vụ không trả lời: sau 12 giây tự dừng, thêm 8 giây thì báo lỗi mạng, không bao giờ kẹt ở "Đang nghe".
- Nhận giọng nói dùng dịch vụ có sẵn của Android (Google), tiếng Việt. Có mạng là chạy; muốn chạy không cần mạng thì tải gói "Nhận dạng giọng nói ngoại tuyến" tiếng Việt trong cài đặt Google của điện thoại.
- Máy không có dịch vụ nhận giọng nói: màn hình hiện ba câu hỏi gợi ý thay cho nút nói.

## Kịch bản 5 — Thư viện

| Bước | Người dùng | App nói |
|---|---|---|
| 1 | Chạm hai lần **Thư viện** | "Thư viện, bản mẫu. Có hai cuốn sách…" |
| 2 | Chạm hai lần một cuốn | Mở sách, đọc ngay: "Tự nhiên và Xã hội 3. Trang 42. Cây đậu lớn lên như thế nào." rồi đọc lời mô tả trang |
| 3 | Chạm hai lần **Trang sau** / **Trang trước** | Đọc trang kế; ở trang cuối: "Đây là trang cuối." |
| 4 | Chạm hai lần **Đọc trang** hoặc thẻ trang | Đọc lại trang hiện tại |

App tải theo ba tầng: kho của máy chủ (`/v1/library`) → bản đã lưu lần trước (nghe được khi mất mạng) → sách mẫu trong app (`assets/library/sach_mau.json`). Màn hình và câu giới thiệu nói rõ nguồn: "Máy chủ", "Đã lưu" hoặc "Bản mẫu". Bảng trên là ví dụ với sách mẫu.

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

## Lịch sử cập nhật

Ai sửa file này, theo lịch sử git. "(AI hỗ trợ)" là commit có ghi trợ lý AI trong lời nhắn; commit cũ không ghi thì không suy ra là không dùng.

| Ngày | Người | Việc | Commit |
|---|---|---|---|
| 27/11/2026 | Phúc (AI hỗ trợ) | feat(app): hướng dẫn chụp trên máy (nhắc khi đang ngắm, kiểm ảnh vừa chụp); cập nhật tài liệu app | `17c38f6` |
| 19/11/2026 | Toàn (AI hỗ trợ) | feat(frontend): hỏi bằng giọng nói (nhận giọng nói có sẵn của Android) | `c897839` |
| 18/11/2026 | Toàn (AI hỗ trợ) | feat(frontend): giao diện mới cho học sinh khiếm thị, chuẩn bị đưa lên điện thoại | `947fe22` |
| 17/11/2026 | Đào Việt Toàn (AI hỗ trợ) | feat(frontend): đưa app Flutter vào frontend/, đọc hợp đồng AI v0.1 | `d2d80a7` |
