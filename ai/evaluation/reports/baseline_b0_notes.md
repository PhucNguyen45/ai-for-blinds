# Nhật ký thực nghiệm VLM — B0-001: Sơ đồ vòng tuần hoàn nước

> **Trạng thái:** Thử nghiệm thăm dò (exploratory baseline); chưa phải kết quả đánh giá định lượng chính thức.  
> **Ngày thực nghiệm:** 24/10/2026 (giờ Việt Nam, UTC+7).  
> **Người phụ trách:** Mảng A — AI/VLM và giọng nói (Phúc).

## 1. Mục tiêu và bối cảnh

- Kiểm tra luồng **ảnh học liệu → OpenRouter API → VLM → lời diễn giải tiếng Việt**.
- Quan sát khả năng nêu chủ đề, thành phần, quan hệ/mũi tên và ý nghĩa chung cho học sinh khiếm thị.
- Phát hiện lỗi kỹ thuật, lỗi thuật ngữ và thông tin cần kiểm chứng trước khi tạo bộ đánh giá chính thức.

## 2. Cấu hình có thể tái lập

| Trường | Giá trị |
|---|---|
| Model | `nvidia/nemotron-3.5-super-vl:free` |
| Provider phản hồi | `Nvidia` (theo JSON OpenRouter) |
| API | OpenRouter `/api/v1/chat/completions` |
| Mã thử nghiệm | `ai/vlm/test_openrouter.py` |
| Ảnh đầu vào | `data/local/test.png` (trong repo; không commit) |
| Chủ đề ảnh | Sơ đồ vòng tuần hoàn nước (*Water Cycle Flowchart*) |
| Nguồn ảnh tham khảo | https://commons.wikimedia.org/wiki/File:Water_cycle_flowchart.png |
| SHA-256 của ảnh | *Chưa ghi — cần tính từ file gốc trên WSL* |
| Temperature | `0.2` |
| Tiêu chí đầu ra | Tiếng Việt, bốn mục, tránh suy đoán |

**Prompt đã sử dụng (giữ nguyên):**

> Hãy giải thích hình này bằng tiếng Việt thật ngắn gọn cho học sinh khiếm thị theo đúng 4 mục: (1) Chủ đề của hình, (2) Các thành phần chính, (3) Chiều mũi tên và quan hệ giữa các giai đoạn, (4) Ý nghĩa tổng quát. Nếu không chắc thì nói không chắc.

**Lưu ý phương pháp:** Prompt đã quy định sẵn bốn mục và yêu cầu không suy đoán; vì thế đây là **B0 thăm dò với prompt có hướng dẫn**, không phải đối chứng “mô tả tự do không tối ưu”. Khi thiết kế thí nghiệm chính thức, cần định nghĩa lại các nhóm B0/B1/B2 và giữ điều kiện so sánh nhất quán.

## 3. Kết quả các lần chạy

| Chỉ số | B0-001a: reasoning bật | B0-001b: reasoning tắt |
|---|---:|---:|
| Timestamp (UTC+7) | `24/10/2026 07:47:25 +07` | `24/10/2026 07:54:10 +07` |
| HTTP | 200 | 200 |
| Thời gian đo phía client | 12,05 giây | 3,47 giây |
| `max_tokens` | 400 | 600 |
| `finish_reason` | `length` | `stop` |
| Prompt tokens | 799 | 799 |
| Completion tokens | 400 | 254 |
| Reasoning tokens | 400 | 0 |
| Total tokens | 1199 | 1053 |
| Chi phí phản hồi | $0 | $0 |
| Nội dung trả về | `null` | Có, hoàn chỉnh |
| File JSON đầu vào của nhật ký | `last_response.json` (đính kèm lần 1) | `last_response(1).json` (đính kèm lần 2) |

**Diễn giải:** Lần 1 tiêu hết token vào `reasoning` và kết thúc bởi `length`, nên **không sinh phần trả lời thông thường**. Lần 2 tắt reasoning, trả lời hoàn chỉnh và `finish_reason=stop`. Không được diễn giải chênh lệch độ trễ 12,05 → 3,47 giây như mức tăng tốc đã chứng minh: giới hạn token, chế độ reasoning, tải provider và thời điểm gọi đều có thể ảnh hưởng.

## 4. Đầu ra nguyên văn — lần B0-001b

Dưới đây là giải thích ngắn gọn cho học sinh khiếm thị:

1. **Chủ đề của hình:** Chu trình nước trên Trái Đất.

2. **Các thành phần chính:** Hình có bốn giai đoạn chính: hơi nước (Water Vapor), mưa/tuyết rơi (Precipitation), nước và băng (Water & Ice), và quá trình bốc hơi,昇華, hơi nạp (Evaporation, Sublimation, & Transpiration). Các biểu tượng đi kèm như mây, cốc nước, người tuyết, nhà igloo và vòi nước phun.

3. **Chiều mũi tên và quan hệ giữa các giai đoạn:** Các mũi tên màu đen tạo thành một vòng tròn, cho thấy các giai đoạn diễn ra liên tục và liên tiếp theo chiều kim đồng hồ: từ hơi nước → mưa/tuyết → nước và băng → bốc hơi → trở lại hơi nước.

4. **Ý nghĩa tổng quát:** Hình minh họa nước di chuyển liên tục trên Trái Đất qua các trạng thái khác nhau, tạo thành chu trình tự nhiên không ngừng.

## 5. Nhận xét sơ bộ của người nghiên cứu

### Quan sát đã xác nhận từ output

- Mô hình nêu đúng **chủ đề vòng tuần hoàn nước** theo nhãn sơ đồ.
- Câu trả lời có đủ bốn mục theo yêu cầu prompt.
- Mô hình nhắc tới hơi nước, giáng thủy, nước/băng và các quá trình đưa nước trở lại dạng hơi.
- Có lỗi ngôn ngữ rõ ràng: ký tự `昇華` chen trong câu tiếng Việt và cụm **“hơi nạp”** không phù hợp với thuật ngữ *transpiration* (thoát hơi nước).
- Câu trả lời còn thiên về liệt kê nhãn và biểu tượng, chưa giải thích rõ cơ chế của từng chuyển tiếp để hỗ trợ người học hình dung hiện tượng.

### Cần kiểm chứng bằng ảnh gốc và đáp án tham chiếu

- Mô tả **chiều kim đồng hồ** có đúng với từng mũi tên hay không.
- Các biểu tượng được liệt kê như **vòi nước phun**, **cốc nước**, **igloo** có đúng/đáng đưa vào lời giải thích hay không.
- Bản diễn giải có thiếu thông tin bắt buộc, nhầm thuật ngữ hay thêm dữ kiện không được ảnh hỗ trợ hay không.
- Chưa chấm điểm định lượng vì chưa có bộ đáp án tham chiếu, rubric và người chấm độc lập.

### Lỗi/giới hạn cần ghi nhận

1. **Kỹ thuật:** `max_tokens=400` không đủ khi reasoning bật; `message.content=null`, `finish_reason=length`.
2. **Ngôn ngữ:** Có trộn ký tự Hán và dịch thuật chưa đúng tự nhiên đối với học sinh Việt Nam.
3. **Trợ năng:** Trình bày bốn mục có thể có ích khi đọc bằng TTS, nhưng vẫn cần kiểm nghiệm với người dùng khiếm thị; chưa thể kết luận tính dễ hiểu.
4. **Độ tin cậy:** Một ảnh và một lần trả lời thành công không chứng minh chất lượng chung của model.

## 6. Bước nghiên cứu tiếp theo

- [ ] Tạo bản mô tả tham chiếu của ảnh, có kiểm duyệt các nhãn, hướng mũi tên, thuật ngữ khoa học.
- [ ] Ghi SHA-256 của ảnh để những lần chạy sau dùng đúng một đầu vào.
- [ ] Tách **B0 (prompt tối thiểu)** và **B1 (prompt chuyên biệt trợ năng)**, cố định các cấu hình còn lại.
- [ ] Chạy ít nhất 3 loại học liệu: sơ đồ, biểu đồ và hình minh họa khoa học/hình học.
- [ ] Xây rubric rõ nghĩa cho: chính xác dữ kiện, đúng quan hệ, đầy đủ, diễn giải sư phạm, dễ nghe và nội dung không có căn cứ.
- [ ] Lưu mỗi lần chạy với mã, ngày, model, prompt version, image hash, reasoning config, token, latency, finish reason và raw JSON (kiểm tra thông tin nhạy cảm trước khi commit).

## 7. Tái lập lần B0-001b

Chạy tại `ai/` (yêu cầu `../data/local/test.png` tồn tại và `.env` có key):

```bash
uv run python vlm/test_openrouter.py \
  --image ../data/local/test.png \
  --prompt "Hãy giải thích hình này bằng tiếng Việt thật ngắn gọn cho học sinh khiếm thị theo đúng 4 mục: (1) Chủ đề của hình, (2) Các thành phần chính, (3) Chiều mũi tên và quan hệ giữa các giai đoạn, (4) Ý nghĩa tổng quát. Nếu không chắc thì nói không chắc." \
  --max-tokens 600
```

**Lưu ý:** File `evaluation/last_response.json` đang bị ghi đè bởi mỗi lần chạy. Nên đặt tên kết quả theo từng mã thí nghiệm về sau; không commit `.env`, dữ liệu nhạy cảm hoặc raw response chưa được rà soát.
