# PROJECT CONTEXT — AI FOR BLINDS

> **Mục đích tài liệu:** cung cấp cho Claude bối cảnh thống nhất về đề tài, nhóm thực hiện, phạm vi công việc, tiến độ, định hướng nghiên cứu và trạng thái bằng chứng. Đây là tài liệu tổng hợp từ hồ sơ nội bộ được cung cấp; không thay thế các tài liệu gốc.
>
> **Nguyên tắc đọc:** phân biệt rõ (1) thông tin chính thức trong phiếu đăng ký, (2) kế hoạch/lộ trình, (3) đề xuất nghiên cứu, (4) công việc đã thực hiện và (5) kết quả đã được kiểm chứng. Không biến mục tiêu hoặc kế hoạch thành kết quả.

## 1. Thông tin chính thức về đề tài

### 1.1. Tên đề tài

**“Nghiên cứu, phát triển hệ thống nhận dạng, diễn giải hình ảnh ứng dụng mô hình ngôn ngữ thị giác, hỗ trợ học sinh khiếm thị học tập kiến thức trực quan.”**

Đây là tên ghi trong Phiếu đăng ký đề tài NCKH của học viên năm học 2026–2027, ngày 08/08/2026. Khi viết báo cáo hoặc mô tả dự án, giữ nguyên tên này, không tự ý đổi tên hay thu hẹp thành đề tài chỉ về đọc sách giáo khoa.

### 1.2. Mục tiêu chính thức

Nghiên cứu và phát triển hệ thống trí tuệ nhân tạo có khả năng nhận dạng, phân tích và diễn giải nội dung hình ảnh bằng ngôn ngữ tự nhiên, hỗ trợ học sinh khiếm thị tiếp cận các kiến thức trực quan trong học tập như hình minh họa, biểu đồ, sơ đồ, bản đồ, hình học, thí nghiệm khoa học và tài liệu giáo dục số.

### 1.3. Nội dung nghiên cứu chính thức

- Tìm hiểu các đặc điểm, khó khăn của học sinh khiếm thị trong tiếp cận nội dung học tập trực quan.
- Nghiên cứu các mô hình ngôn ngữ thị giác (Vision-Language Models — VLM).
- Xây dựng hệ thống trợ lý ảo.

### 1.4. Sản phẩm dự kiến

Phần mềm demo và/hoặc bài báo khoa học (theo cách ghi trong phiếu đăng ký: “Phần mềm demo/bài báo”).

### 1.5. Thành viên và cán bộ hướng dẫn

- Cán bộ hướng dẫn: TS. Phan Việt Anh, Bộ môn Khoa học máy tính, Khoa V4.
- Đào Việt Toàn.
- Nguyễn Hoàng Phúc.
- Nguyễn Công Nam.

Phiếu đăng ký ghi lớp của từng học viên tại thời điểm đăng ký; không cần sử dụng các thông tin điểm số trong hoạt động nghiên cứu nếu không có yêu cầu cụ thể.

## 2. Bối cảnh và bài toán nghiên cứu

Đề tài hướng đến việc hỗ trợ học sinh khiếm thị tiếp cận kiến thức vốn được truyền đạt qua hình ảnh và các biểu diễn trực quan. Hệ thống cần chuyển nội dung thị giác thành thông tin ngôn ngữ có thể tiếp nhận bằng âm thanh, đồng thời giữ được những dữ kiện và quan hệ quan trọng của hình ảnh.

**Không đồng nhất các khái niệm sau:**

- **Nhận dạng (recognition):** xác định thành phần, đối tượng, ký hiệu hoặc loại nội dung xuất hiện.
- **Mô tả (description):** trình bày những gì quan sát được trong ảnh.
- **Diễn giải (interpretation):** làm rõ cấu trúc, quan hệ và ý nghĩa có thể suy ra có căn cứ từ nội dung ảnh.
- **Giải thích (explanation):** có thể bao gồm kiến thức bổ sung hoặc giải thích nguyên nhân; phải phân biệt phần nào được thể hiện trong ảnh và phần nào đến từ kiến thức bên ngoài.
- **Hỏi đáp theo hình (Visual Question Answering — VQA):** trả lời câu hỏi cụ thể dựa trên ảnh và ngữ cảnh hợp lệ.

Một hệ thống chỉ đọc chữ hoặc liệt kê vật thể chưa chắc đã giải quyết được bài toán diễn giải hình ảnh. Với biểu đồ, sơ đồ, bản đồ, hình học và hình minh họa khoa học, các quan hệ, thứ tự, số liệu và cấu trúc có thể quan trọng không kém tên đối tượng.

### 2.1. Phạm vi hình ảnh

Phiếu đăng ký nêu các ví dụ học liệu: hình minh họa, biểu đồ, sơ đồ, bản đồ, hình học, thí nghiệm khoa học và tài liệu giáo dục số.

Một số tài liệu lộ trình nhóm sử dụng năm nhóm trang để tổ chức công việc: `text`, `map`, `chart`, `table`, `figure`. Đây là cách phân nhóm phục vụ triển khai ban đầu, **chưa phải một hệ phân loại khoa học đã được chứng minh hoặc được chốt chính thức**. Không mặc định mọi nhóm đều có cùng mức ưu tiên. Cần khảo sát, thử nghiệm và thống nhất phạm vi trọng tâm dựa trên dữ liệu và yêu cầu của đề tài.

### 2.2. Định hướng chất lượng đầu ra

Các tài liệu Mảng A đề xuất lời diễn giải tiếng Việt:

- Chính xác, có căn cứ từ ảnh.
- Có cấu trúc, trình bày ý chính trước rồi đến thành phần và quan hệ quan trọng.
- Dễ nghe, phù hợp chuyển thành giọng nói.
- Nêu rõ phần không chắc chắn, bị mờ, thiếu hoặc không thể xác định.
- Không tự suy đoán tên riêng, số liệu, quan hệ hoặc nội dung không có bằng chứng.
- Phân biệt dữ kiện quan sát được với kiến thức nền bổ sung.

Các nguyên tắc “Conciseness, Continuity, Calibrated Honesty” xuất hiện trong lộ trình nhóm như định hướng thiết kế prompt; cần xem là nguyên tắc đề xuất để kiểm tra, không tự động coi là kết quả nghiên cứu.

## 3. Định hướng hệ thống ở cấp nhóm

Lộ trình nhóm ngày 15/10/2026 mô tả hướng xây dựng ứng dụng Android hỗ trợ học sinh khiếm thị chụp học liệu và nghe nội dung bằng tiếng Việt. Kiến trúc dự kiến gồm ba khối:

1. **Ứng dụng di động Flutter/Android:** tương tác với người dùng, chụp ảnh, điều khiển bằng chạm/giọng nói và phát nội dung âm thanh.
2. **Backend FastAPI:** tiếp nhận yêu cầu, quản lý luồng xử lý và kết nối thành phần AI.
3. **Thành phần AI/VLM và dữ liệu học liệu:** nhận dạng, phân tích, diễn giải hình ảnh; có định hướng xây dựng kho mô tả học liệu để hỗ trợ truy cập lại/offline.

Lộ trình nhóm ban đầu đề cập mô hình mã nguồn mở chạy on-premise và Qwen3-VL. Tuy nhiên, lộ trình cá nhân Mảng A cập nhật sau đó nhấn mạnh phải lựa chọn mô hình dựa trên bằng chứng, khả năng triển khai, chi phí, độ trễ và tài nguyên thực tế. Vì vậy:

- On-premise là định hướng/đích triển khai trong tài liệu nhóm, không được tuyên bố là đã khả thi nếu chưa xác minh cấu hình máy chủ.
- Qwen3-VL là ứng viên được khảo sát, không phải kết luận lựa chọn cuối cùng.
- Có thể dùng API trong giai đoạn nghiên cứu/benchmark nếu cần; phải ghi rõ mô hình, endpoint, chi phí và điều kiện thử nghiệm.
- Không được khẳng định đổi backend chỉ bằng cấu hình sẽ chắc chắn không cần sửa các lớp khác nếu hợp đồng API và kiểm thử tích hợp chưa chứng minh điều đó.

## 4. Phân công hiện hành

Tài liệu lộ trình nhóm ngày 15/10/2026 có phân công ban đầu khác với phân công trong lộ trình cá nhân Mảng A và báo cáo cập nhật ngày 22–23/10/2026. Các tài liệu cập nhật ghi nhận việc Phúc và Toàn đã đổi mảng. Khi làm việc theo trạng thái cập nhật, sử dụng phân công sau:

### 4.1. Nguyễn Hoàng Phúc — Mảng A: AI và giọng nói

Phúc phụ trách nghiên cứu và kiểm chứng phương pháp chuyển nội dung hình ảnh học tập thành diễn giải tiếng Việt chính xác, có cấu trúc và dễ tiếp cận bằng âm thanh; phát triển phần xử lý AI để bàn giao cho backend và ứng dụng tích hợp.

Phạm vi chính:

- Nghiên cứu VLM, nhận dạng và diễn giải hình ảnh.
- Phân tích bài toán, thuật ngữ, câu hỏi nghiên cứu và giả thuyết.
- Prompt Engineering và thiết kế pipeline diễn giải.
- Xây dựng/chuẩn hóa dữ liệu, ground truth, rubric và công cụ đánh giá.
- Benchmark mô hình, phân tích lỗi và báo cáo kết quả.
- Logic hỏi đáp theo hình và duy trì ngữ cảnh ở tầng AI.
- Nghiên cứu/tích hợp STT, quy tắc văn nói và yêu cầu TTS.
- Định nghĩa schema/contract đầu ra AI và phối hợp kiểm thử tích hợp.

**Không phải chủ sở hữu chính:** phát triển toàn bộ ứng dụng Flutter/Android; xây dựng và duy trì backend FastAPI, endpoint chính thức, cơ sở dữ liệu, triển khai máy chủ GPU hoặc hạ tầng Docker. Những phần này thuộc các thành viên khác, dù Phúc phải phối hợp để bảo đảm module AI tích hợp được.

### 4.2. Nguyễn Công Nam — Mảng B: Backend, dữ liệu và triển khai

Theo lộ trình nhóm, Nam phụ trách xương sống backend, API, kho dữ liệu/mô tả học liệu và triển khai. Các đầu việc được nêu gồm FastAPI, hợp đồng API, lưu/nhận ảnh, cơ sở dữ liệu, Docker Compose, nhật ký yêu cầu, endpoint thư viện và hỏi đáp, khảo sát triển khai VLM trên GPU/on-premise.

Đây là phân công theo lộ trình nhóm; các thay đổi sau đó cần được xác nhận trực tiếp với nhóm.

### 4.3. Đào Việt Toàn — Mảng C: Ứng dụng Flutter

Theo lộ trình nhóm sau khi đổi mảng, Toàn phụ trách ứng dụng Android/Flutter, camera, trải nghiệm trợ năng, TalkBack, điều hướng âm thanh, gọi API, lịch sử và giao diện hỏi đáp.

### 4.4. Quy tắc phối hợp

- Phúc xác định ngữ nghĩa và cấu trúc dữ liệu đầu ra AI; Nam phụ trách API/backend; Toàn sử dụng kết quả ở ứng dụng.
- Schema/API phải được thống nhất và quản lý phiên bản; thay đổi ảnh hưởng liên mảng cần được các bên liên quan xem xét.
- Không tự ý gán việc thuộc backend hoặc Flutter cho Phúc chỉ vì các công việc đó có liên quan đến tích hợp AI.
- Nếu tài liệu mới hoặc xác nhận của nhóm cập nhật phân công, ghi rõ ngày và thay thế trạng thái cũ; không âm thầm hợp nhất hai bản phân công mâu thuẫn.

## 5. Phạm vi sản phẩm và đầu ra của Mảng A

Lộ trình cá nhân của Phúc xác định bảy nhóm thành phẩm:

| Mã | Thành phẩm | Tiêu chuẩn hoàn thành theo lộ trình |
|---|---|---|
| A-01 | Hồ sơ nghiên cứu | Tổng quan tài liệu có bảng đối chiếu; định nghĩa bài toán; 1–2 câu hỏi nghiên cứu; giả thuyết có thể bác bỏ. |
| A-02 | Bộ dữ liệu chuẩn | Bộ 30 ảnh thí điểm và từ 100 mẫu đánh giá trở lên; có nguồn gốc, loại hình, chú thích, thông tin tham chiếu và tách tập. |
| A-03 | VLM baseline và báo cáo chọn mô hình | Benchmark với cấu hình cố định; đối chiếu chất lượng, chi phí, độ trễ và giới hạn mô hình. |
| A-04 | Phương pháp diễn giải đề xuất | Sơ đồ pipeline, lược đồ dữ liệu, prompt phiên bản hóa, cách xử lý quan hệ và thông tin không chắc chắn. |
| A-05 | Module AI bàn giao được | Mã nguồn có thể import/gọi; đầu vào/đầu ra chuẩn hóa; xử lý lỗi; hướng dẫn chạy; dữ liệu kiểm thử. |
| A-06 | Hỏi đáp theo hình và hỗ trợ tiếng nói | Logic Q&A có ngữ cảnh và kiểm soát trả lời; STT tiếng Việt được đánh giá; chuẩn văn nói/TTS có tài liệu. |
| A-07 | Thực nghiệm và báo cáo | So sánh baseline/phương pháp; bảng chỉ số; ví dụ đúng/sai; giới hạn; tài liệu bàn giao và đóng góp báo cáo. |

Các tiêu chuẩn trên là mục tiêu/tiêu chí hoàn thành trong kế hoạch, không phải khẳng định rằng các sản phẩm đã hoàn tất.

## 6. Nghiên cứu khoa học và phương pháp đang được đề xuất

### 6.1. Câu hỏi nghiên cứu và giả thuyết

Báo cáo Mảng A đề xuất làm rõ bài toán trước khi chốt phương pháp; viết 1–2 câu hỏi nghiên cứu và giả thuyết có thể bác bỏ. Một ví dụ được nêu trong lộ trình là kiểm tra liệu biểu diễn quan hệ trung gian có làm giảm tỷ lệ diễn giải sai quan hệ so với mô tả trực tiếp trong cùng điều kiện hay không.

Đây là ví dụ giả thuyết, **không phải câu hỏi nghiên cứu đã được giảng viên phê duyệt**. Claude phải hỗ trợ Phúc phân tích và kiểm chứng, không tự ghi thành quyết định chính thức.

### 6.2. Các phương án phương pháp

Báo cáo đề cập so sánh các cách tiếp cận như:

- **B0 — Direct:** VLM diễn giải trực tiếp từ ảnh bằng văn bản.
- **B1 — Structured extraction:** trích xuất thành phần/dữ kiện và quan hệ thành cấu trúc trung gian, sau đó tạo diễn giải.
- **B2 — Phương án có bước kiểm chứng/pipeline bổ sung:** chỉ sử dụng nếu đặc tả cụ thể và có thể kiểm nghiệm.

Tên gọi, thành phần và giao thức B0/B1/B2 cần bám theo bản báo cáo và phiên bản thí nghiệm thực tế. Không giả định B1/B2 tốt hơn B0. So sánh phải công bằng, dùng cùng tập dữ liệu/điều kiện tương đương và có phân tích trade-off chất lượng, độ trễ, chi phí.

### 6.3. Khung mức độ diễn giải

Các tài liệu Mảng A sử dụng khung làm việc A–D và đặc biệt đặt vấn đề kiểm chứng “mức C”. Khung này được dùng để phân tích mức độ từ nhận dạng/mô tả đến diễn giải/giải thích. Báo cáo nêu rõ đây là **khung làm việc cần đối chiếu tài liệu khoa học, chưa phải chuẩn đã được công bố hoặc thống nhất**.

Không tự gán định nghĩa chính thức cho từng mức nếu chưa trích đúng từ tài liệu gốc. Khi thảo luận mức C, phải xác định thao tác cụ thể, ví dụ dương/âm, ranh giới bằng chứng và tiêu chí chấm.

### 6.4. Tài liệu khoa học được báo cáo Mảng A đề cập

Báo cáo Mảng A tổng hợp các hướng tham khảo gồm:

- Lundgard & Satyanarayan — mô hình bốn mức nội dung ngữ nghĩa trong biểu diễn trực quan.
- VisText — dữ liệu/phương pháp liên quan đến mô tả biểu đồ.
- Sightation Counts — nghiên cứu liên quan đến hỗ trợ tiếp cận thông tin thị giác cho người khiếm thị.
- W3C WAI — hướng dẫn về hình ảnh phức tạp.
- ChartCap và ChartQA — mô tả/hiểu biểu đồ và hỏi đáp trên biểu đồ.
- Nghiên cứu về giới hạn VLM trong hiểu quan hệ thị giác.
- ASSETS 2024 — các vấn đề khi AI hỗ trợ người khuyết tật tiếp cận nội dung.
- VMMU — benchmark hiểu đa phương thức tiếng Việt.

Đây là danh sách các nguồn được báo cáo nêu, không phải khẳng định mọi nguồn đã được đọc/đối chiếu đầy đủ hoặc đã chứng minh tính mới của đề tài. Khi trích dẫn trong báo cáo chính thức, phải kiểm tra lại bài gốc, tác giả, năm, venue, nội dung và giới hạn.

### 6.5. Nguyên tắc thực nghiệm

- Có baseline và tập kiểm thử độc lập.
- Không điều chỉnh prompt theo từng ảnh test rồi dùng chính ảnh đó để kết luận.
- Lưu model ID, phiên bản, prompt version, tham số suy luận, ảnh/hash, timestamp, request/response và độ trễ.
- Tách các chiều đánh giá: OCR/chữ-số, nhận dạng thành phần, quan hệ, tính có căn cứ, độ đầy đủ, dễ nghe, từ chối hợp lý, STT và hiệu năng.
- Không gộp mọi khía cạnh thành một điểm duy nhất nếu điều đó che khuất lỗi quan trọng.
- Phân tích theo loại hình, độ khó và chất lượng ảnh; nêu ví dụ đúng/sai và trường hợp thất bại.
- Nếu phương pháp đề xuất không tốt hơn baseline, báo cáo kết quả âm tính và giới hạn; không sửa test sau khi xem đáp án.

## 7. Dữ liệu, công cụ và trạng thái đã ghi nhận trong báo cáo

### 7.1. PILOT30

Báo cáo Mảng A ngày 23/10/2026 ghi nhận đã chuẩn bị bộ thí điểm PILOT30 gồm 30 ảnh giả lập, chia thành ba loại, có 196 mệnh đề chuẩn và 60 câu hỏi. Báo cáo cũng ghi nhận đã xây dựng schema đầu ra AI, prompt đối chứng và công cụ chấm mệnh đề.

**Trạng thái cần giữ chính xác:** PILOT30 tại thời điểm báo cáo là bộ thí điểm/kiểm tra pipeline; dữ liệu cần được rà soát, gán nhãn và bổ sung ảnh học liệu thực tế có quyền sử dụng phù hợp. Không được mô tả PILOT30 là benchmark đại diện cho toàn bộ học liệu hoặc dữ liệu đã được xác nhận độc lập.

### 7.2. Kiểm tra kỹ thuật đã thực hiện

Báo cáo nêu đã chạy kiểm tra công cụ chấm bằng cách đối chiếu đáp án gốc với bản sao đáp án để xác minh pipeline đánh giá hoạt động. Đây là smoke test của công cụ, không phải đánh giá chất lượng mô hình.

Tại thời điểm báo cáo 23/10/2026:

- Chưa chạy VLM thật trên bộ dữ liệu để có kết quả benchmark.
- Chưa có căn cứ kết luận mô hình nào tốt hơn.
- Chưa được tuyên bố chất lượng diễn giải hoặc hiệu quả hỗ trợ học tập đã được chứng minh.
- Các số liệu kiểm tra công cụ không được trình bày như điểm chất lượng của VLM.

Nếu có kết quả thực nghiệm mới hơn, phải cập nhật trạng thái dựa trên log và artefact thực tế, không tiếp tục dùng trạng thái cũ.

### 7.3. Schema đầu ra AI bản nháp

Báo cáo nêu schema nội bộ phiên bản 0.1 với các trường:

- `schema_version`: phiên bản schema.
- `image_type`: loại hình dự đoán, ví dụ `bar_chart`, `line_chart`, `flow_diagram`, `unknown`.
- `status`: trạng thái như `ok`, `partial`, `unreadable`, `unsupported`.
- `summary_vi`: phần tóm tắt tiếng Việt để phát trước.
- `facts`: các dữ kiện có cấu trúc, gồm `subject`, `predicate`, `object`, `evidence`.
- `interpretation_vi`: lời diễn giải đầy đủ, dễ đọc.
- `uncertainties`: thông tin chưa xác định hoặc không chắc chắn.
- `question_answering_ready`: cho biết dữ liệu có đủ căn cứ cho hỏi đáp hay không.

Đây là **hợp đồng đầu ra nội bộ bản nháp 0.1**, chưa phải API cuối. Báo cáo cũng lưu ý rằng trường `evidence` do VLM tự sinh không tự động chứng minh dữ kiện là đúng; cần cơ chế đánh giá/xác minh riêng.

Các điểm tích hợp còn cần thống nhất gồm `image_id`, session/conversation state cho hỏi đáp nhiều lượt, timeout, lỗi nhận ảnh, nội dung nhạy cảm và chính sách lưu/xóa dữ liệu.

### 7.4. Ứng viên mô hình và công nghệ được nêu

Các tài liệu đề cập những ứng viên/giải pháp sau:

- Qwen3-VL 8B.
- Qwen3-VL-30B-A3B-Instruct.
- Vintern-1B.
- PhoWhisper-base cho STT tiếng Việt.
- OpenRouter để gọi mô hình API trong thử nghiệm.
- vLLM và máy chủ GPU như một hướng khảo sát triển khai.

Đây là các ứng viên được đề xuất hoặc nhắc đến trong kế hoạch; không phải tất cả đã được chạy benchmark. Cần kiểm tra phiên bản, giấy phép, điều kiện sử dụng, tài nguyên, chi phí và hiệu năng tại thời điểm thử nghiệm.

### 7.5. Môi trường cá nhân

Lộ trình cá nhân mô tả môi trường làm việc của Phúc gồm Ubuntu trên WSL2, Python, `uv`, Git/GitHub, LM Studio và OpenRouter. Báo cáo phần cứng thử nghiệm cục bộ ghi nhận RTX 2070 Max-Q 8GB VRAM và RAM 32GB. Đây là thông tin môi trường tại thời điểm tài liệu được lập; xác nhận lại trước khi đưa ra tư vấn cấu hình hoặc benchmark mới.

## 8. STT, TTS và tương tác bằng giọng nói

Mảng A có trách nhiệm nghiên cứu và cung cấp yêu cầu/logic AI liên quan đến giọng nói, phối hợp với ứng dụng và backend.

Các hạng mục được nêu trong lộ trình:

- STT tiếng Việt, có ứng viên PhoWhisper-base.
- Bộ lệnh giọng nói dự kiến như “chụp”, “đọc lại”, “chậm hơn”, “nhanh hơn”, “hỏi”.
- Chuẩn hóa văn bản để tính WER và đánh giá độ chính xác nhận dạng ý định (intent accuracy).
- Quy tắc văn nói/TTS: ngắt câu, cách đọc số, đơn vị và ký hiệu; tránh đầu ra Markdown/JSON hoặc cú pháp kỹ thuật trong phần văn bản phát trực tiếp.
- Tương tác hỏi đáp nhiều lượt theo ảnh/ngữ cảnh, không mô tả lại toàn bộ ảnh khi người dùng chỉ hỏi một chi tiết.

Các yêu cầu này là hạng mục nghiên cứu/triển khai trong kế hoạch. Không coi STT/TTS hoặc Q&A đã hoàn tất nếu chưa có kiểm thử và kết quả được lưu.

## 9. Lộ trình và các mốc kế hoạch

### 9.1. Mốc nhóm trong lộ trình cá nhân cập nhật

| Giai đoạn | Thời gian | Đầu ra/cổng dự kiến |
|---|---|---|
| 0. Căn chỉnh | 22–31/10/2026 | SRS phần AI v0; 30 ảnh có hồ sơ; khung tiêu chí; hợp đồng AI–backend sơ bộ. |
| 1. Cơ sở lý thuyết | 01–15/11/2026 | Bảng tài liệu; ranh giới diễn giải; RQ/giả thuyết dự thảo; prompt baseline v1. |
| 2. Baseline VLM | 16/11–06/12/2026 | Chạy ít nhất 30 ảnh trên ứng viên khả thi; báo cáo lựa chọn baseline. |
| 3. MVP tích hợp | 07–13/12/2026 | Module mô tả ảnh tối thiểu chạy với API của Nam và app của Toàn trên điện thoại thật. |
| 4. Phương pháp v2 | 14/12/2026–31/01/2027 | Pipeline đề xuất; bộ từ 100 mẫu; hỏi đáp nhiều lượt; STT/TTS; output API v2. |
| 5. Đánh giá so sánh | 15–28/02/2027 | So sánh baseline/phương pháp, ablation nếu phù hợp, báo cáo lỗi. Lộ trình ghi không xếp việc bắt buộc 01–14/02. |
| 6. Hoàn thiện | 01–31/03/2027 | Đóng băng module trước 14/03; phối hợp thử nghiệm; kết quả định lượng và số đo đến 31/03. |
| 7. Báo cáo/bàn giao | 01–30/04/2027 | Bản nháp dự kiến 15/04; mã, benchmark, tài liệu và báo cáo chốt. |

### 9.2. Lộ trình nhóm bản 15/10/2026

Lộ trình nhóm cũ nêu các mốc chính: 31/10/2026, 13/12/2026, 31/01/2027, 31/03/2027 và 30/04/2027. Bản lộ trình cá nhân sau đó bổ sung các cổng trung gian như 06/12, 14/03 và 15/04.

Hai tài liệu có thể khác nhau về người phụ trách và chi tiết công việc do phân công đã được điều chỉnh. Khi lập kế hoạch hiện hành, ưu tiên bản cá nhân cập nhật cho công việc của Phúc và xác nhận lại với nhóm/giảng viên khi có xung đột.

### 9.3. Tình trạng chính thức của lịch

Lộ trình cá nhân ghi rõ đây là bản đề xuất điều chỉnh từ lộ trình nhóm, chờ thống nhất với Nam, Toàn và giảng viên. Tài liệu cũng nêu hạn nghiệm thu chính thức cấp trường/khoa chưa được xác nhận. Do đó, không trình bày các mốc trên như lịch nghiệm thu chính thức của Học viện.

## 10. Các tiêu chí đánh giá được đề xuất

Báo cáo Mảng A gợi ý tách các chiều đánh giá thay vì dùng một điểm tổng hợp duy nhất:

| Khía cạnh | Đơn vị/ý tưởng đo lường được nêu |
|---|---|
| Đọc chữ và số | CER/WER cho vùng chữ; exact match hoặc sai số giá trị số. |
| Nhận dạng thành phần | Precision, Recall, F1; lỗi bỏ sót, hợp nhất hoặc sai loại. |
| Nhận dạng quan hệ | Relation F1; đúng hướng, thứ tự và đích của mũi tên. |
| Diễn giải có căn cứ | Tỷ lệ mệnh đề đúng, thiếu căn cứ, sai quan hệ; mức độ nghiêm trọng. |
| Độ đầy đủ | Recall thông tin thiết yếu hoặc rubric theo ground truth. |
| Dễ tiếp nhận | Rubric văn nói và đánh giá hiểu thông tin với người nghe phù hợp. |
| Từ chối hợp lý | Precision/Recall trên ảnh mờ, thiếu thông tin hoặc không đọc được. |
| STT | WER có quy tắc chuẩn hóa và intent accuracy. |
| Hiệu năng | p50/p95, thời gian tới kết quả đầu tiên, token, bộ nhớ hoặc chi phí. |

Lộ trình nhóm ban đầu còn nêu mục tiêu ≥100 trang, chia theo năm loại, ba người chấm độc lập theo thang 5 cho các tiêu chí đúng, đủ, dễ nghe; đếm riêng tỷ lệ trang có nội dung bịa. Các mục tiêu KPI này cần được kiểm tra tính khả thi và chốt giao thức trước khi dùng làm tiêu chí chính thức.

## 11. Tích hợp và bàn giao giữa các mảng

Các mốc bàn giao trong báo cáo/lộ trình gồm:

- 31/10: schema/API bản nháp và ví dụ response; Nam có thể dựng mock endpoint, Toàn có thể dựng luồng client.
- 22/11: baseline mô tả khả dụng, có model/prompt ID để tích hợp thử.
- 13/12: MVP AI chạy qua API và ứng dụng trên thiết bị thật.
- 31/01: method v2, Q&A nhiều lượt, đặc tả STT/TTS và kiểm thử.
- 14/03: AI release candidate và contract/regression test.
- 31/03: kết quả đánh giá và bản build cuối theo kế hoạch.
- 30/04: mã nguồn, README, benchmark, dữ liệu hợp pháp và đóng góp báo cáo.

Các mốc này là kế hoạch bàn giao, không phải xác nhận đã bàn giao. Module AI chỉ được xem là sẵn sàng tích hợp khi có mã chạy được, đầu vào/đầu ra chuẩn hóa, xử lý trạng thái lỗi, kiểm thử schema, cấu hình/phiên bản, hướng dẫn chạy và dữ liệu kiểm thử.

## 12. Rủi ro và vấn đề chưa được chốt

Các tài liệu Mảng A nêu những rủi ro/điểm mở sau:

1. **Định nghĩa mức diễn giải C:** cần đối chiếu lý thuyết, ví dụ đúng/sai và xác nhận với giảng viên; chưa coi là chuẩn đã chốt.
2. **Dữ liệu thí điểm:** dữ liệu giả lập chỉ giúp kiểm tra pipeline; cần ảnh học liệu thực tế, quyền sử dụng và gán nhãn được rà soát.
3. **Chưa có kết quả VLM thật tại thời điểm báo cáo:** cần benchmark theo giao thức cố định, lưu log.
4. **Thiếu máy chủ GPU:** phải kiểm tra VRAM/tài nguyên; nếu không đủ, cân nhắc mô hình nhỏ hoặc API và báo cáo rõ khác biệt.
5. **Bản quyền học liệu:** cần kiểm tra quyền sử dụng và điều kiện phát tán dữ liệu trước khi tạo thư viện/chia sẻ bộ dữ liệu. Không tự suy diễn rằng mọi thao tác đều được miễn trừ pháp lý.
6. **Thiếu người dùng mục tiêu:** nếu không tiếp cận được học sinh khiếm thị, chỉ kết luận về hiệu quả kỹ thuật/chuyên gia trong phạm vi đã đánh giá; không tuyên bố hiệu quả giáo dục hoặc trải nghiệm người dùng đã được chứng minh.
7. **Không thống nhất schema giữa các thành viên:** cần contract, versioning và kiểm thử tích hợp.
8. **Phương pháp mới không tốt hơn baseline:** báo cáo kết quả âm tính, phân tích lỗi và trade-off; không điều chỉnh tập test sau khi biết kết quả.
9. **Mốc nghiệm thu:** hạn chính thức cấp khoa/trường chưa được xác nhận trong tài liệu lộ trình.

## 13. Quy tắc về trạng thái thông tin trong Project

Claude phải gắn đúng trạng thái khi nhắc đến nội dung dự án:

- **Chính thức:** thông tin trong phiếu đăng ký đề tài hoặc quyết định được nhóm/giảng viên xác nhận.
- **Kế hoạch:** nhiệm vụ, KPI, thời hạn hoặc sản phẩm dự kiến trong lộ trình.
- **Đề xuất:** giả thuyết, phương pháp, kiến trúc, schema hoặc giải pháp đang được cân nhắc.
- **Đã thực hiện:** có ghi nhận trong báo cáo hoặc artefact cụ thể cho thấy công việc đã làm.
- **Đã kiểm chứng:** có dữ liệu, log, biên bản hoặc kết quả thực nghiệm hỗ trợ kết luận.
- **Chưa xác nhận:** có mâu thuẫn hoặc thiếu xác nhận từ nhóm/giảng viên.

Không được dùng từ “đã hoàn thành”, “đã chứng minh”, “đạt KPI” nếu tài liệu hoặc kết quả hiện có không hỗ trợ.

## 14. Thứ tự ưu tiên khi tài liệu mâu thuẫn

1. Phiếu đăng ký đề tài và quyết định chính thức được giảng viên/đơn vị xác nhận: ưu tiên cho tên, mục tiêu và nội dung đăng ký.
2. Tài liệu/lệnh điều chỉnh mới nhất đã được nhóm và giảng viên xác nhận: ưu tiên cho phân công, phạm vi và tiến độ cập nhật.
3. Lộ trình cá nhân Mảng A: dùng để theo dõi công việc và sản phẩm Phúc phụ trách, nhưng tài liệu tự ghi là đề xuất chờ thống nhất; không coi toàn bộ nội dung là quyết định chính thức.
4. Lộ trình nhóm ngày 15/10/2026: dùng làm lịch sử và căn cứ kế hoạch chung ban đầu; lưu ý phân công A/B/C đã khác sau khi Phúc và Toàn đổi mảng.
5. Báo cáo Mảng A ngày 23/10/2026: dùng để hiểu trạng thái nghiên cứu, artefact và các đề xuất tại thời điểm báo cáo; không tự động thay thế phiếu đăng ký hoặc quyết định chính thức.

Nếu không xác định được tài liệu nào mới hơn hoặc có thẩm quyền cao hơn, hãy nêu rõ điểm mâu thuẫn và hỏi người dùng; không tự ý chọn một phương án rồi trình bày như sự thật.

## 15. Hướng dẫn Claude khi hỗ trợ dự án

- Luôn đặt câu hỏi nghiên cứu và mục tiêu chính thức làm trung tâm; không biến dự án thành một ứng dụng OCR/đọc sách đơn thuần.
- Tập trung đúng phần việc Mảng A khi người dùng yêu cầu hỗ trợ công việc cá nhân; vẫn hiểu các ranh giới tích hợp với backend và Flutter.
- Khi đề xuất công nghệ hoặc mô hình, phân tích bài toán, bằng chứng, tài nguyên, chi phí, độ trễ, giấy phép và khả năng tái lập trước khi khuyến nghị.
- Khi viết báo cáo khoa học, phân biệt nội dung từ tài liệu gốc, kết quả thực nghiệm, diễn giải và đề xuất.
- Khi nghiên cứu tài liệu bên ngoài, ưu tiên bài báo gốc/tài liệu chính thức; kiểm tra trích dẫn và không bịa nguồn.
- Khi phân tích code hoặc thiết kế, trước hết xác định phần nào thuộc AI, backend hay ứng dụng; không mở rộng phạm vi trách nhiệm một cách tùy tiện.
- Hỗ trợ Phúc hiểu bản chất vấn đề và tự đánh giá phương án; không thay thế việc học và tư duy nghiên cứu bằng kết luận có sẵn.
- Trao đổi mặc định bằng tiếng Việt; giữ thuật ngữ chuyên ngành tiếng Anh khi cần và giải thích ở lần xuất hiện đầu tiên.
- Không tự cập nhật trạng thái hoàn thành, quyết định hoặc phân công nếu người dùng chưa cung cấp bằng chứng/xác nhận.

---

## Phụ lục A — Tài liệu nguồn đã dùng để tổng hợp

1. `đăng ký đề tài - phúc - toàn - nam.doc` — Phiếu đăng ký đề tài NCKH học viên năm học 2026–2027, ngày 08/08/2026.
2. `LO-TRINH-NCKH.docx` — Lộ trình NCKH nhóm, ngày 15/10/2026.
3. `Lo_trinh_NCKH_ca_nhan_Phuc_Mang_A_2026-2027.docx` — Lộ trình cá nhân Phúc, Mảng A, cập nhật 22/10/2026.
4. `BAO_CAO_NCKH_MANG_A_NGUYEN_HOANG_PHUC.docx` — Báo cáo tiến độ Mảng A, cập nhật 23/10/2026.

**Lưu ý cập nhật:** Tài liệu này phản ánh nội dung của các file nguồn nói trên tại thời điểm chúng được lập. Khi có báo cáo, quyết định, kết quả benchmark hoặc thay đổi phân công mới, cần cập nhật các mục tương ứng và ghi ngày cập nhật, đồng thời giữ lại lịch sử thay đổi quan trọng.
