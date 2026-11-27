# A-01 — Hồ sơ nghiên cứu (BẢN NHÁP, 2026-11-17)

> **Trạng thái:** bản nháp do AI hỗ trợ soạn để **Phúc đọc, phản biện và quyết định**. Không phải quyết định chính thức,
> chưa được giảng viên duyệt. Mọi câu hỏi nghiên cứu ở mục 5 là **đề xuất (PROPOSED)**.
> **Quy ước nguồn:** mỗi tài liệu ghi rõ *mức đã đọc*. Chỗ nào chỉ dựa trên tóm tắt/kết quả tìm kiếm thì ghi "cần đọc bản gốc trước khi trích dẫn".

> **Ghi chú 27/11/2026:** định hướng đã được làm rõ thêm sau bản nháp này, xem [Quy cách đầu ra](../../ai/README.md#quy-cách-đầu-ra-chốt-ngày-27112026): người dùng là học sinh lớp 1–12 và sinh viên; không giải bài tập; model riêng hướng Gemma, ưu tiên distill; nghiên cứu tách model-level và system-level. Phần dưới **chưa** viết lại: câu hỏi nghiên cứu ở mục 5 chưa có distill, kiến trúc teacher/student và tiêu chí tuân thủ; cần Phúc chọn lại.

## 1. Bài toán

Chuyển hình ảnh học liệu (biểu đồ, sơ đồ, hình học, bản đồ, bảng…) thành lời diễn giải **tiếng Việt** mà học sinh khiếm thị nghe được,
sao cho: (a) đúng và có căn cứ từ ảnh; (b) có cấu trúc, ý chính trước; (c) nêu rõ điều không chắc; (d) không trộn kiến thức nền với điều
nhìn thấy mà không nói rõ. Phân biệt: *nhận dạng* (có gì), *mô tả* (nhìn thấy gì), *diễn giải* (cấu trúc, quan hệ, ý nghĩa có căn cứ),
*giải thích* (thêm kiến thức ngoài ảnh), *hỏi đáp theo hình*.

## 2. Tổng quan tài liệu (đã kiểm tra nguồn)

| # | Tài liệu | Mức đã đọc | Nội dung chính (nêu đúng như nguồn) | Liên quan tới đề tài |
|---|---|---|---|---|
| 1 | Lundgard & Satyanarayan. *Accessible Visualization via Natural Language Descriptions: A Four-Level Model of Semantic Content.* IEEE TVCG (Proc. InfoVis) 2022; arXiv:2110.04406 (8/10/2021) | Tóm tắt + toàn văn HTML đến mục 5.3 (mục 5.4–6 chỉ qua bản tóm tắt) | Mô hình 4 mức nội dung ngữ nghĩa: **L1** thuộc tính cơ bản/mã hóa (vd trục, thang), **L2** khái niệm/quan hệ thống kê (cực trị, so sánh), **L3** hiện tượng tri giác/nhận thức (xu hướng, mẫu phức tạp), **L4** bối cảnh/kiến thức miền. Khảo sát 30 người khiếm thị + 90 người sáng: người khiếm thị xếp **L2 và L3** hữu ích nhất, **L1 và L4** kém hữu ích; người sáng xếp L3, L4 cao nhất. L1 có phân bố hai đỉnh (nhiều người xếp thấp nhất nhưng vẫn có người xếp cao nhất). Không khác biệt đáng kể theo loại biểu đồ/chủ đề/độ khó | Cơ sở lý thuyết để **định nghĩa "mức" diễn giải** và quyết định nội dung nào ưu tiên cho TTS |
| 2 | Tang, Boggust, Satyanarayan. *VisText: A Benchmark for Semantically Rich Chart Captioning.* ACL 2023; arXiv:2307.05356 | Tóm tắt + toàn văn HTML mục 1–4 (kết quả/hạn chế mục 5–6 qua bản tóm tắt) | 12.441 biểu đồ (cột 6.238, vùng 3.189, đường 3.014) kèm bảng dữ liệu, scene graph; chú thích mức L1 sinh bằng mẫu, L2/L3 do người viết (Prolific). Mô hình văn bản dựa trên scene graph/bảng dữ liệu ≈ nhau và không kém hơn mô hình dùng ảnh; theo bản tóm tắt, khoảng một nửa câu L2/L3 được lấy mẫu là đúng, lỗi gồm sai đối tượng, sai giá trị, sai chiều xu hướng | Gợi ý: **biểu diễn trung gian có cấu trúc** có giá trị; đồng thời cho thấy rủi ro **sai giá trị/chiều** (cần đọc bản gốc để trích số) |
| 3 | W3C WAI. *Complex Images* (Images Tutorial), cập nhật 08/04/2026 | Đọc toàn bộ trang | Ảnh phức tạp cần **mô tả ngắn** (nhận dạng ảnh) + **mô tả dài** (thông tin thiết yếu: thang đo, giá trị, quan hệ, xu hướng; có thể cả thành phần hình như thứ tự màu, độ cao cột). Trang **không** có danh sách kiểm riêng cho sơ đồ hay bản đồ | Ánh xạ tự nhiên: `summary_vi` ↔ mô tả ngắn, `interpretation_vi` ↔ mô tả dài *(ánh xạ này là cách hiểu của người soạn)* |
| 4 | Lim, Ahn, Kim. *ChartCap: Mitigating Hallucination of Dense Chart Captioning.* ICCV 2025 (Highlight); arXiv:2508.03164 | **Chỉ kết quả tìm kiếm**; cần đọc bản gốc | 565K biểu đồ thật; chú thích dày chỉ dựa trên thông tin chart hỗ trợ; đề xuất Visual Consistency Score (so ảnh dựng lại từ chú thích với ảnh gốc) | Liên quan **giảm bịa đặt** và cách đo mà không cần chú thích tham chiếu |
| 5 | Kang et al. *Sightation Counts: Leveraging Sighted User Feedback in Building a BLV-aligned Dataset of Diagram Descriptions.* ACL 2025 (long); arXiv:2503.13369 | **Chỉ kết quả tìm kiếm**; cần đọc bản gốc | Người sáng **đánh giá** mô tả do VLM sinh thay vì tự viết; bộ Sightation 5k sơ đồ, 137k mẫu; chuyên gia giáo dục khiếm thị đánh giá hữu ích | Liên quan **quy trình tạo dữ liệu/đánh giá** có người khiếm thị tham gia |
| 6 | Dang et al. *VMMU: A Vietnamese Multitask Multimodal Understanding and Reasoning Benchmark.* arXiv:2508.13680 (v1 8/2025, bản mới 1/2026) | **Chỉ kết quả tìm kiếm**; cần đọc bản gốc | 2,5 nghìn câu hỏi, 7 nhiệm vụ; mô hình độc quyền đạt khoảng 66% trung bình; tác giả nêu nguyên nhân lỗi chính **không phải OCR** mà là grounding và suy luận đa phương thức | Tham chiếu tiếng Việt. Cần đối chiếu với quan sát về sai dấu ở mục 4 (khác mô hình, khác nhiệm vụ) |

**Chưa đọc/chưa tìm:** "Nghiên cứu về giới hạn VLM trong hiểu quan hệ thị giác", ChartQA, bài ASSETS 2024 (báo cáo Mảng A có nhắc). Bảng này **không phải tổng quan hệ thống**; chưa đủ để khẳng định tính mới.

## 3. Điều tài liệu gợi ý cho thiết kế (nêu rõ là suy luận)

1. Nội dung nên ưu tiên **L2–L3** (so sánh, cực trị, xu hướng, quan hệ) hơn là liệt kê thuần thuộc tính mã hóa (L1) hay thêm bối cảnh (L4) — theo xếp hạng của 30 người khiếm thị trong nghiên cứu 1. Lưu ý: độ đồng thuận giữa người khiếm thị thấp hơn người sáng; phần tôi đọc được không nêu độ tuổi/trình độ người tham gia, trong khi đối tượng của đề tài là **học sinh**.
2. Yêu cầu của đề tài "phân biệt dữ kiện trong ảnh và kiến thức bổ sung" khớp với ranh giới **L1–L3 (từ ảnh/dữ liệu) và L4 (bối cảnh ngoài)**.
3. Cấu trúc **mô tả ngắn + dài** (W3C) khớp với hợp đồng đầu ra `summary_vi` + `interpretation_vi`.
4. Khoảng trống ghi nhận *trong các nguồn đã đọc* (không phải kết luận về tính mới): mô hình Lundgard nêu phạm vi tiếng Anh và biểu đồ chuẩn (theo bản tóm tắt mục 6.2); VisText chỉ gồm cột/vùng/đường đơn biến. Học liệu Việt Nam gồm sơ đồ, hình học, bản đồ, bảng chưa nằm trong phạm vi các nguồn này.

## 4. Quan sát sơ bộ từ thực nghiệm của nhóm (dev, ảnh tổng hợp, n=1, chỉ số từ khóa — KHÔNG phải kết luận)

Nguồn: `ai/evaluation/reports/so_sanh_phuong_phap_va_model_dev_20261117.md`. Một model miễn phí.
- Chép sai dấu/chữ tiếng Việt khi đọc nhãn ("Trống lúa", "Rau máu"); B1 không khắc phục.
- Bịa thành phần ở sơ đồ vòng (`cycle_03`: nút "Hạt mọc" không tồn tại), kể cả khi qua trích xuất có cấu trúc.
- Bảng: B1 đọc đủ giá trị, B0e đọc một phần, nhưng chỉ có 2 bảng.
- Ảnh không đọc được: B1 trả trạng thái từ chối có cấu trúc, B0/B0e chỉ nói trong văn bản.

## 5. Câu hỏi nghiên cứu ĐỀ XUẤT (Phúc chọn 1–2 và sửa lời)

> Mỗi câu có giả thuyết **bác bỏ được**. Ngưỡng số là đề xuất để thảo luận, chưa dựa trên ước lượng phương sai (cần chạy lặp trước khi chốt).

**RQ-A — Biểu diễn trung gian.** So với diễn giải trực tiếp có cùng yêu cầu nội dung (B0e), việc trích xuất dữ kiện có cấu trúc rồi mới diễn giải (B1) có giảm tỷ lệ sai về **giá trị và quan hệ** trên học liệu tiếng Việt không?
- H1: Trên tập test, tỷ lệ mệnh đề giá trị/quan hệ đúng của B1 cao hơn B0e (so sánh cặp theo từng ảnh, ≥3 lần chạy/ảnh).
- Bác bỏ nếu: khoảng tin cậy của hiệu số bao gồm 0 hoặc B1 thấp hơn.
- Ghi chú: đây là dạng giả thuyết trong lộ trình nhóm; kết quả sơ bộ của nhóm hiện **chưa** đủ để nghiêng về phía nào.

**RQ-B — Bịa đặt và xác minh.** Một bước xác minh đối chiếu `facts` với ảnh (B2) có giảm tỷ lệ dữ kiện **không có căn cứ** so với B1 không, và đánh đổi bao nhiêu độ đầy đủ/độ trễ?
- H2: tỷ lệ dữ kiện không có căn cứ giảm và độ đầy đủ không giảm quá [ngưỡng do nhóm chọn].
- Bác bỏ nếu: tỷ lệ không giảm hoặc độ đầy đủ giảm vượt ngưỡng.
- Cần: định nghĩa "không có căn cứ" và quy trình gán nhãn (ground truth hiện chỉ có mệnh đề *thiếu*, chưa có danh sách mệnh đề *thừa/bịa* — cần bổ sung).

**RQ-C — Chép nhãn tiếng Việt.** Lỗi chép sai dấu/chữ khi đọc nhãn thay đổi thế nào theo độ phân giải ảnh và cách cắt vùng chữ?
- H3: tỷ lệ lỗi ký tự (CER) vùng nhãn giảm khi tăng độ phân giải/cắt vùng chữ.
- Bác bỏ nếu: CER không giảm đáng kể.
- Ghi chú: đây là câu hỏi kỹ thuật hẹp, ít mới về lý thuyết nhưng có tác động thực tế lớn.

**RQ-D — Từ chối hợp lý.** Một trạng thái từ chối có cấu trúc có phân biệt được ảnh không đọc được với ảnh đọc được với độ chính xác/độ phủ chấp nhận được không?
- H4: Precision và Recall của trạng thái `unreadable` đạt [ngưỡng do nhóm chọn] trên tập có ảnh suy giảm có kiểm soát.
- Bác bỏ nếu: dưới ngưỡng. Cần nhiều ảnh suy giảm hơn (hiện chỉ có 3 ảnh `unreadable`).

**Khuyến nghị của người soạn (Phúc quyết định):** chọn **RQ-A + RQ-B** vì chúng nối tiếp nhau (có cấu trúc → có thể kiểm tra từng dòng), phù hợp lộ trình B0/B1/B2, và lỗi bịa đã quan sát được. RQ-C và RQ-D xử lý như thí nghiệm phụ.

## 6. Định nghĩa "mức C" — cần Phúc làm rõ

Báo cáo Mảng A dùng khung A–D và nói tới "mức C". Phần tôi đọc được **không cho biết khung A–D tương ứng thế nào** với mô hình L1–L4 của Lundgard. Nếu "mức C" nghĩa là L3 (hiện tượng tri giác/nhận thức), có thể thao tác hóa thành: *mệnh đề về xu hướng/mẫu phức tạp suy ra có căn cứ từ ảnh*, với ví dụ dương/âm và ranh giới bằng chứng. Việc này phải đối chiếu với thầy trước khi ghi vào hồ sơ.

## 7. Thiết kế thực nghiệm sơ bộ (để thảo luận)

- **Dữ liệu:** tập test (23 mẫu tổng hợp hiện có) + ảnh thật/SGK được duyệt ground truth; thêm nhãn mệnh đề *bịa* cho RQ-B.
- **Điều kiện:** B0e, B1, B2; cùng model, tham số, prompt đóng băng; ≥3 lần chạy/ảnh; so sánh cặp.
- **Chỉ số:** phủ mệnh đề critical (tách giá trị/quan hệ/cấu trúc), tỷ lệ mệnh đề không có căn cứ, CER vùng nhãn, độ trễ/token, precision/recall của `unreadable`; chấm rubric_v1 bằng người cho mẫu lỗi.
- **Mối đe dọa tính giá trị:** ảnh tổng hợp sạch; một model miễn phí; chỉ số từ khóa; người chấm duy nhất; dữ liệu SGK chưa có bản quyền văn bản; chưa có người khiếm thị đánh giá — **không được kết luận về hiệu quả học tập**, chỉ về chất lượng kỹ thuật theo tiêu chí đã định.

## 8. Câu hỏi cho Phúc và thầy

1. Chọn RQ nào làm trọng tâm? Có muốn đổi lời không?
2. "Mức C" trong khung A–D tương ứng L1–L4 thế nào?
3. Có tiếp cận được học sinh/giáo viên khiếm thị để đánh giá không? (quyết định phạm vi kết luận)
4. Hạn nghiệm thu chính thức của Học viện/khoa là khi nào?
5. Ảnh SGK dùng nội bộ: có cần văn bản ghi nhận của thầy không?

## 9. Tài liệu tham khảo (đã xác nhận bằng trang gốc hoặc kết quả tìm kiếm)

1. Lundgard, A., Satyanarayan, A. (2022). Accessible Visualization via Natural Language Descriptions: A Four-Level Model of Semantic Content. IEEE TVCG (Proc. InfoVis). https://arxiv.org/abs/2110.04406 — *đã đọc phần lớn*
2. Tang, B. J., Boggust, A., Satyanarayan, A. (2023). VisText: A Benchmark for Semantically Rich Chart Captioning. ACL 2023. https://arxiv.org/abs/2307.05356 — *đã đọc phần lớn*
3. W3C WAI. Complex Images (Images Tutorial). https://www.w3.org/WAI/tutorials/images/complex/ — *đã đọc*
4. Lim, J., Ahn, J., Kim, G. (2025). ChartCap: Mitigating Hallucination of Dense Chart Captioning. ICCV 2025. https://arxiv.org/abs/2508.03164 — *chưa đọc bản gốc*
5. Kang, W. J. et al. (2025). Sightation Counts. ACL 2025. https://arxiv.org/abs/2503.13369 — *chưa đọc bản gốc*
6. Dang, V. T. et al. (2025). VMMU: A Vietnamese Multitask Multimodal Understanding and Reasoning Benchmark. https://arxiv.org/abs/2508.13680 — *chưa đọc bản gốc*

**Việc cần làm trước khi dùng trong báo cáo chính thức:** đọc bản gốc (PDF/HTML đầy đủ) của 4–6 và các mục chưa đọc của 1–2; kiểm tra lại các con số p-value, tỷ lệ phần trăm; tìm thêm tài liệu về lỗi quan hệ thị giác của VLM và ASSETS 2024.
