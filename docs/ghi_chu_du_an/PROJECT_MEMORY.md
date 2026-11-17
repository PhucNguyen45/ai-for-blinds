# PROJECT_MEMORY --- AI FOR BLINDS

> **Mục đích:** Ghi nhớ trạng thái làm việc hiện tại của đề tài, các
> quyết định đã xác nhận, kết quả thực tế, vấn đề còn tồn tại và công
> việc tiếp theo.
>
> **Phân biệt với `PROJECT_CONTEXT.md`:** Context mô tả kiến thức nền và
> định hướng tương đối ổn định của dự án. Memory ghi nhận những gì đã
> thay đổi trong quá trình nghiên cứu và triển khai.
>
> **Nguyên tắc quan trọng:** Tài liệu này không phải nhật ký hội thoại.
> Chỉ lưu thông tin có giá trị cho các công việc tiếp theo. Không biến
> đề xuất thành quyết định, kế hoạch thành kết quả hoặc suy đoán thành
> sự thật.

------------------------------------------------------------------------

## 0. Metadata

  -----------------------------------------------------------------------
  Trường                              Giá trị
  ----------------------------------- -----------------------------------
  Dự án                               AI for Blinds

  Đề tài                              Nghiên cứu, phát triển hệ thống
                                      nhận dạng, diễn giải hình ảnh ứng
                                      dụng mô hình ngôn ngữ thị giác, hỗ
                                      trợ học sinh khiếm thị học tập kiến
                                      thức trực quan

  Người phụ trách phần việc được ghi  Phúc Nguyễn --- Mảng A (AI và giọng
  nhận                                nói)

  Phiên bản tài liệu                  1.0 --- Khởi tạo

  Ngày khởi tạo                       14/11/2026

  Lần cập nhật trạng thái gần nhất    23/10/2026 (theo báo cáo Mảng A
  theo tài liệu nguồn                 được cung cấp)

  Trạng thái xác minh                 Cần đối chiếu tiến độ thực tế sau
                                      ngày 23/10/2026
  -----------------------------------------------------------------------

------------------------------------------------------------------------

## 1. Current Status --- Trạng thái hiện tại

### 1.1. Phạm vi phụ trách

Theo phân công đã điều chỉnh được ghi nhận trong Context:

-   **Phúc:** Mảng A --- AI và giọng nói.
-   **Nam:** Backend, dữ liệu và triển khai.
-   **Toàn:** Ứng dụng Flutter và trợ năng.

Tài liệu lộ trình nhóm ban đầu có phân công khác. Khi có mâu thuẫn, sử
dụng phân công mới đã được nhóm xác nhận; không diễn giải tài liệu cũ
thành phân công hiện tại.

### 1.2. Trạng thái Mảng A theo báo cáo hiện có

Các tài liệu được cung cấp ghi nhận những hướng công việc sau:

-   Nghiên cứu VLM cho bài toán nhận dạng và diễn giải hình ảnh.
-   Nghiên cứu phương pháp diễn giải hình ảnh và thiết kế prompt.
-   Xây dựng định hướng đánh giá, bao gồm PILOT30 và bộ đánh giá dự kiến
    100 mẫu.
-   Quan tâm đến JSON Schema và cấu trúc đầu ra.
-   Nghiên cứu hướng tích hợp OCR, STT và TTS.
-   Xem xét benchmark và đánh giá chất lượng diễn giải.

**Giới hạn của thông tin hiện có:** Báo cáo Mảng A ngày 23/10/2026 ghi
nhận PILOT30 đã được tạo nhưng chưa duyệt; chưa có benchmark VLM thực tế
tại thời điểm báo cáo. Không được coi các nội dung dự kiến, đang nghiên
cứu hoặc đang xây dựng là kết quả đã hoàn thành.

### 1.3. Cần cập nhật ngay khi tiếp tục dự án

-   Tiến độ thực tế của từng đầu việc sau ngày 23/10/2026.
-   Trạng thái PILOT30: đã duyệt/chưa duyệt, nội dung thay đổi và người
    xác nhận.
-   Bộ dữ liệu đánh giá 100 mẫu: đã xây dựng đến đâu, tiêu chí chọn mẫu
    và trạng thái kiểm tra.
-   Benchmark VLM: đã chạy hay chưa; mô hình, phiên bản, prompt, cấu
    hình, dữ liệu và kết quả.
-   Trạng thái prompt, JSON Schema, OCR, STT/TTS và tích hợp với các
    mảng khác.
-   Các sản phẩm đã bàn giao và bằng chứng tương ứng.

------------------------------------------------------------------------

## 2. Research Decisions --- Quyết định nghiên cứu

Chỉ ghi tại đây những quyết định đã được người nghiên cứu hoặc nhóm xác
nhận. Những đề xuất chưa được chấp thuận phải nằm ở mục 6.

  --------------------------------------------------------------------------
  ID             Quyết định     Căn cứ/lý do   Ngày xác nhận  Trạng thái
  -------------- -------------- -------------- -------------- --------------
  RD-001         Phúc phụ trách Phân công đã   Chưa ghi ngày  Đã xác nhận
                 Mảng A --- AI  điều chỉnh                    theo thông tin
                 và giọng nói;  được ghi nhận                 dự án
                 Toàn phụ trách trong Context                 
                 Mảng C --- Ứng                               
                 dụng; Nam phụ                                
                 trách Backend,                               
                 dữ liệu và                                   
                 triển khai                                   

  --------------------------------------------------------------------------

Khi bổ sung quyết định mới, ghi rõ nội dung, người xác nhận, thời điểm,
lý do và những quyết định cũ bị thay thế (nếu có).

------------------------------------------------------------------------

## 3. Technical Decisions --- Quyết định kỹ thuật

Không tự động xem các công nghệ hoặc mô hình được nhắc trong tài liệu
khảo sát là công nghệ đã chốt.

### 3.1. Các lựa chọn kỹ thuật đã được ghi nhận

  ---------------------------------------------------------------------------
  Hạng mục                    Thông tin được ghi nhận Phân loại
  --------------------------- ----------------------- -----------------------
  Môi trường thử nghiệm cục   LM Studio               Công cụ đã được sử
  bộ                                                  dụng/thử nghiệm

  Gọi mô hình qua API         OpenRouter              Công cụ đã được sử
                                                      dụng/thử nghiệm

  Phần cứng thử nghiệm        RTX 2070 Max-Q 8GB      Ràng buộc môi trường
                              VRAM, RAM 32GB          

  Định hướng giao tiếp mô     OpenAI-compatible API   Định hướng kỹ thuật
  hình                                                

  Mô hình Qwen3-VL-4B Q4_K_M  Được nêu là lựa chọn    Lựa chọn thử nghiệm,
                              thử nghiệm cục bộ       không mặc định là mô
                                                      hình cuối cùng

  Qwen3-VL-30B-A3B-Instruct   Được nêu là baseline    Baseline dự kiến/được
  qua OpenRouter              thử nghiệm ban đầu      định hướng; cần xác
                                                      minh đã chạy thực tế
                                                      hay chưa
  ---------------------------------------------------------------------------

### 3.2. Nhật ký quyết định kỹ thuật

  -----------------------------------------------------------------------
  ID          Hạng mục    Quyết định  Lý do       Ngày        Trạng thái
  ----------- ----------- ----------- ----------- ----------- -----------
  TD-001      ---         Chưa ghi    Cần xác     ---         Chưa cập
                          nhận quyết  nhận từ                 nhật
                          định kỹ     nhóm                    
                          thuật cuối                          
                          cùng trong                          
                          tài liệu                            
                          khởi tạo                            

  -----------------------------------------------------------------------

Với mỗi quyết định, cần ghi cả phương án thay thế đã cân nhắc và lý do
không lựa chọn nếu thông tin đó có giá trị.

------------------------------------------------------------------------

## 4. Completed Work --- Công việc đã hoàn thành

Chỉ đưa vào mục này công việc có bằng chứng xác nhận như tài liệu, mã
nguồn, dữ liệu, log, kết quả chạy hoặc xác nhận của người phụ trách.

  --------------------------------------------------------------------------
  ID             Công việc/sản  Bằng chứng     Ngày hoàn      Ghi chú
                 phẩm                          thành          
  -------------- -------------- -------------- -------------- --------------
  CW-001         Tạo bản        Được báo cáo   Không rõ       Tại thời điểm
                 PILOT30        Mảng A ngày                   báo cáo,
                                23/10/2026 ghi                PILOT30 chưa
                                nhận                          được duyệt

  CW-002         ---            Chưa có thông  ---            Bổ sung khi có
                                tin xác nhận                  bằng chứng
  --------------------------------------------------------------------------

**Không ghi "benchmark VLM đã hoàn thành"** nếu chưa có log hoặc kết quả
thực nghiệm thực tế. Việc chuẩn bị benchmark, xây dựng tập mẫu và chạy
benchmark là các trạng thái khác nhau.

------------------------------------------------------------------------

## 5. Pending Tasks --- Công việc đang làm và chưa hoàn thành

Các mục dưới đây là những điểm cần xác minh hoặc tiếp tục theo dõi từ
tài liệu hiện có, không phải khẳng định rằng tất cả vẫn đang được thực
hiện ở thời điểm hiện tại.

  -----------------------------------------------------------------------
  ID                Công việc         Trạng thái theo   Điều kiện để đóng
                                      thông tin gần     
                                      nhất              
  ----------------- ----------------- ----------------- -----------------
  PT-001            Duyệt PILOT30     Chưa duyệt tại    Có phiên bản được
                                      23/10/2026        rà soát và xác
                                                        nhận

  PT-002            Xây dựng/hoàn     Được nêu trong kế Có bộ mẫu, tiêu
                    thiện bộ đánh giá hoạch; cần xác    chí và trạng thái
                    dự kiến 100 mẫu   minh tiến độ      kiểm tra rõ ràng

  PT-003            Benchmark VLM     Chưa có benchmark Có cấu hình, log,
                    thực tế           thực tế tại       kết quả và phân
                                      23/10/2026        tích

  PT-004            Hoàn thiện prompt Có trong hướng    Có phiên bản được
                    và JSON Schema    công việc; cần    kiểm thử và quản
                                      xác minh phiên    lý
                                      bản hiện tại      

  PT-005            Nghiên cứu/tích   Có trong phạm vi  Có kết quả thử
                    hợp OCR, STT và   Mảng A; cần xác   nghiệm hoặc bàn
                    TTS               minh tiến độ từng giao được xác
                                      thành phần        nhận

  PT-006            Phối hợp tích hợp Cần xác minh      Có giao diện tích
                    với Backend và    trạng thái liên   hợp, hợp đồng API
                    ứng dụng          nhóm              và kiểm thử liên
                                                        thông
  -----------------------------------------------------------------------

Khi cập nhật, chuyển từng mục sang "Đang thực hiện", "Đã hoàn thành",
"Tạm hoãn" hoặc "Đã hủy", kèm ngày và lý do. Không xóa lịch sử trạng
thái quan trọng.

------------------------------------------------------------------------

## 6. Open Questions & Proposals --- Vấn đề mở và đề xuất

Ghi các câu hỏi chưa có kết luận, giả thuyết cần kiểm chứng và đề xuất
chưa được nhóm chấp thuận.

  --------------------------------------------------------------------------
  ID             Vấn đề         Điều đã biết   Điều chưa      Trạng thái
                                               biết/cần kiểm  
                                               chứng          
  -------------- -------------- -------------- -------------- --------------
  OQ-001         Chất lượng các Đã xác định là Mô hình nào    Chưa kết luận
                 mô hình VLM    trọng tâm khảo đáp ứng tốt    
                 đối với nội    sát            trên bộ dữ     
                 dung học tập                  liệu và tiêu   
                 trực quan                     chí của nhóm   

  OQ-002         Mức độ phù hợp Có hướng       Cần so sánh    Chưa kết luận
                 của phương     nghiên cứu     thực nghiệm,   
                 pháp diễn giải prompt và diễn phân tích lỗi  
                 và prompt      giải           và xác định    
                                               tiêu chí       

  OQ-003         Khả năng đáp   Đã có môi      Cần đo chất    Chưa kết luận
                 ứng của cấu    trường thử     lượng, độ trễ, 
                 hình chạy cục  nghiệm được    chi phí và tài 
                 bộ và API      ghi nhận       nguyên trong   
                                               điều kiện      
                                               tương đương    

  OQ-004         Cơ chế duy trì Nằm trong định Cần xác định   Chưa kết luận
                 ngữ cảnh và bộ hướng tổng thể yêu cầu, phạm  
                 nhớ thị giác   của hệ thống   vi và cách     
                                               đánh giá       
  --------------------------------------------------------------------------

Không tự trả lời các câu hỏi này bằng suy đoán. Khi có bằng chứng mới,
cập nhật kết quả và dẫn nguồn.

------------------------------------------------------------------------

## 7. Problems & Lessons Learned --- Vấn đề và kinh nghiệm

Chỉ ghi lỗi hoặc bài học đã thực sự gặp trong quá trình nghiên cứu, thử
nghiệm hay triển khai.

  --------------------------------------------------------------------------
  ID             Vấn đề         Nguyên nhân đã Cách xử lý     Kết quả/bài
                                xác định                      học
  -------------- -------------- -------------- -------------- --------------
  PL-001         ---            Chưa có thông  ---            Bổ sung khi
                                tin đủ căn cứ                 phát sinh và
                                trong tài liệu                được xác minh
                                khởi tạo                      

  --------------------------------------------------------------------------

Với mỗi lỗi kỹ thuật, nên lưu: môi trường, phiên bản, bước tái hiện,
log, nguyên nhân gốc, phương án đã thử và kết quả. Không ghi nguyên nhân
phỏng đoán như nguyên nhân đã xác định.

------------------------------------------------------------------------

## 8. Next Steps --- Việc tiếp theo

Ưu tiên trước mắt là làm rõ trạng thái thực tế, không mặc định tiếp tục
kế hoạch cũ mà chưa kiểm tra.

1.  **Cập nhật tiến độ sau 23/10/2026:** Đối chiếu từng đầu việc trong
    lộ trình Mảng A với công việc thực tế.
2.  **Xác nhận trạng thái PILOT30:** Xác định phiên bản hiện tại, trạng
    thái duyệt và các thay đổi.
3.  **Kiểm tra bộ dữ liệu đánh giá:** Xác nhận số lượng mẫu, tiêu chí
    lựa chọn, nhãn và chất lượng dữ liệu.
4.  **Xác nhận benchmark:** Kiểm tra đã chạy mô hình nào; thu thập
    prompt, cấu hình, log và kết quả.
5.  **Rà soát các thành phần AI và giọng nói:** Cập nhật riêng trạng
    thái VLM, OCR, STT, TTS, prompt và JSON Schema.
6.  **Rà soát tích hợp liên nhóm:** Xác nhận yêu cầu đầu vào/đầu ra và
    tiến độ phối hợp với Backend, ứng dụng.
7.  **Cập nhật Memory:** Chuyển các thông tin đã xác minh vào những mục
    tương ứng; giữ lại các câu hỏi chưa có kết luận.

------------------------------------------------------------------------

## 9. Update Protocol --- Quy tắc cập nhật bộ nhớ

### 9.1. Khi nào cần cập nhật?

Cập nhật sau một sự kiện có giá trị lâu dài, ví dụ:

-   Nhóm xác nhận hoặc thay đổi quyết định nghiên cứu.
-   Hoàn thành một mốc công việc hoặc sản phẩm.
-   Có kết quả thực nghiệm mới.
-   Thay đổi mô hình, prompt, cấu hình hoặc kiến trúc.
-   Phát hiện lỗi quan trọng và xác định được nguyên nhân.
-   Thay đổi phạm vi, phân công hoặc tiến độ.
-   Một vấn đề mở đã có kết luận.

Không cần cập nhật sau mọi câu hỏi, giải thích hoặc trao đổi thông
thường.

### 9.2. Quy tắc ghi nhận

Mỗi thông tin mới phải có trạng thái phù hợp:

-   `CONFIRMED`: Đã xác nhận.
-   `IN_PROGRESS`: Đang thực hiện.
-   `PLANNED`: Đã lên kế hoạch nhưng chưa thực hiện.
-   `PROPOSED`: Mới là đề xuất.
-   `BLOCKED`: Đang bị cản trở.
-   `CANCELLED`: Đã hủy.
-   `UNKNOWN`: Chưa đủ thông tin.

Nếu có thể, ghi ngày theo định dạng `YYYY-MM-DD`, người xác nhận, nguồn
bằng chứng và liên kết đến tài liệu hoặc kết quả.

### 9.3. Quy trình cập nhật

Khi được yêu cầu cập nhật Memory:

1.  Xác định thông tin mới và nguồn của nó.
2.  Đối chiếu với nội dung hiện có.
3.  Phân loại trạng thái thông tin.
4.  Chỉ sửa các mục liên quan, không viết lại lịch sử không cần thiết.
5.  Cập nhật ngày sửa đổi và ghi chú thay đổi.
6.  Trình bày nội dung Markdown hoàn chỉnh hoặc phần thay thế rõ ràng để
    người dùng kiểm tra.
7.  Không tuyên bố đã cập nhật Project Knowledge nếu người dùng chưa tải
    lên hoặc thay thế file.

### 9.4. Lịch sử cập nhật

  -----------------------------------------------------------------------
  Phiên bản               Ngày                    Nội dung
  ----------------------- ----------------------- -----------------------
  1.0                     2026-11-14              Khởi tạo bộ nhớ dự án
                                                  từ Context và các tài
                                                  liệu nghiên cứu đã cung
                                                  cấp; đánh dấu các trạng
                                                  thái cần xác minh lại
                                                  sau 23/10/2026

  -----------------------------------------------------------------------

------------------------------------------------------------------------

## 10. Quy tắc ưu tiên nguồn thông tin

Khi có mâu thuẫn, không tự động chọn thông tin mới hơn nếu chưa xác định
đó là quyết định chính thức. Hãy xem xét:

1.  Quyết định chính thức mới nhất đã được nhóm xác nhận.
2.  Tài liệu hoặc báo cáo được người phụ trách xác nhận.
3.  Kết quả thực nghiệm và bằng chứng kỹ thuật thực tế.
4.  Lộ trình và kế hoạch đã được phê duyệt.
5.  Bản tổng hợp Context và Memory.
6.  Đề xuất hoặc suy luận của Claude.

Thứ tự trên là hướng dẫn đánh giá độ tin cậy, không thay thế việc kiểm
tra nguồn, ngày tháng và phạm vi áp dụng. Khi không thể giải quyết mâu
thuẫn, phải ghi nhận là chưa xác định và hỏi người dùng.

------------------------------------------------------------------------

> **Nguyên tắc cốt lõi:** PROJECT_MEMORY.md phải phản ánh trung thực
> trạng thái thực tế của AI for Blinds. Tài liệu có thể chưa đầy đủ,
> nhưng tuyệt đối không được đầy đủ bằng cách bịa ra thông tin.
