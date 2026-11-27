# Rubric v1 — Đánh giá khả năng diễn giải hình ảnh của VLM

> **Ghi chú 27/11/2026:** v1 chưa chấm việc tuân thủ [Quy cách đầu ra](../../README.md#quy-cách-đầu-ra-chốt-ngày-27112026) (không lộ đáp án bài tập, không nói điều không được hỏi). C3 có chấm phép tính và C4 chấm "giá trị học tập", cần xem lại. Thang điểm v1 giữ nguyên để không làm đổi nghĩa điểm đã chấm; thay đổi sẽ nằm ở phiên bản mới.

## 1. Mục đích

Đánh giá chất lượng câu trả lời của VLM khi diễn giải
học liệu trực quan cho học sinh khiếm thị.

Rubric này dùng cho thử nghiệm ban đầu, chưa được kiểm định.

## 2. Nguyên tắc

- Chấm dựa trên ảnh gốc, đáp án chuẩn và câu trả lời.
- Không đánh đồng câu trả lời dài với câu trả lời tốt.
- Không tự động coi một câu trả lời trôi chảy là chính xác.
- Không dùng chính câu trả lời của VLM làm đáp án chuẩn.
- Giá trị ước lượng phải được đánh giá theo sai số cho phép
  đã xác định trước từng bài thử.
- Các thử nghiệm so sánh phải kiểm soát mô hình, prompt,
  tham số và điều kiện thực nghiệm.

## 3. Thang điểm

Mỗi tiêu chí được chấm 0, 1 hoặc 2 điểm.

### C1. Nhận diện chủ đề và cấu trúc

- 0: Sai chủ đề hoặc loại hình.
- 1: Nhận diện đúng một phần, thiếu thông tin quan trọng.
- 2: Đúng chủ đề, loại hình và đơn vị nếu có.

### C2. Trích xuất dữ kiện

- 0: Phần lớn dữ kiện sai hoặc thiếu.
- 1: Có cả dữ kiện đúng và dữ kiện sai/thiếu.
- 2: Các dữ kiện được yêu cầu đều chính xác theo đáp án.

### C3. Quan hệ trực quan và suy luận

- 0: Hiểu sai quan hệ chính hoặc tính toán sai nghiêm trọng.
- 1: Nêu đúng một phần quan hệ hoặc phép tính.
- 2: Quan hệ, thứ tự, so sánh và phép tính liên quan đều đúng.

### C4. Diễn giải kiến thức

- 0: Không giải thích được ý nghĩa hoặc giải thích sai.
- 1: Diễn giải cơ bản đúng nhưng còn thiếu hoặc khó hiểu.
- 2: Diễn giải đúng, rõ ràng và có giá trị học tập.

### C5. Kiểm soát thông tin không có căn cứ

- 0: Có thông tin bịa đặt hoặc suy diễn sai nghiêm trọng.
- 1: Có suy diễn chưa đủ căn cứ hoặc diễn đạt quá chắc chắn.
- 2: Không phát hiện thông tin bịa; thể hiện bất định phù hợp.

### C6. Chất lượng tiếng Việt và khả năng đọc bằng TTS

- 0: Nhiều lỗi ngôn ngữ, khó hiểu khi nghe.
- 1: Hiểu được nhưng có lỗi thuật ngữ hoặc trình bày.
- 2: Tiếng Việt rõ ràng, đúng thuật ngữ, phù hợp đọc thành tiếng.

## 4. Tổng điểm

Tối đa: 12 điểm.

Điểm số chỉ phản ánh chất lượng trong bài thử được chấm,
không đại diện cho độ chính xác tổng quát của mô hình.

## 5. Thông tin cần ghi khi chấm

- Run ID
- Mã ảnh kiểm thử
- Người đánh giá
- Điểm C1 đến C6
- Tổng điểm
- Bằng chứng cho các lỗi phát hiện
- Ghi chú về giới hạn của kết quả

## 6. Giới hạn

Rubric hiện tại chưa thay thế đánh giá thực tế với
học sinh khiếm thị, đặc biệt đối với khả năng tiếp thu
kiến thức và trải nghiệm nghe bằng TTS.
