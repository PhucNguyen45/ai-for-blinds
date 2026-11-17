# Ảnh ứng viên (ảnh thật) — CHƯA thuộc benchmark

Ảnh tải từ Wikimedia Commons bằng `ai/evaluation/generators/fetch_commons_candidates.py`
(chỉ CC0 / Public domain / CC BY / CC BY-SA). Ảnh được lưu ở độ rộng ≤1400 px (đã thu nhỏ).
Metadata đầy đủ (tác giả, giấy phép, trang nguồn, sha256) ở `candidates.json`.

**Quy tắc:** một ứng viên chỉ vào `manifest.json` khi có ground truth đã được **người** đối chiếu
với ảnh gốc và (lý tưởng) người thứ hai rà soát. Các file `drafts/*_DRAFT.json` do AI soạn từ nội dung
nhìn thấy trực tiếp (nhãn/cấu trúc/thứ tự), **chưa kiểm chứng**; không dùng làm đáp án chuẩn khi chưa duyệt.

**Khi phát hành/trích ảnh:** phải ghi tác giả + giấy phép (CC BY-SA: bản chỉnh sửa giữ cùng giấy phép).
Nếu chỉ dùng nội bộ để đánh giá, vẫn nên giữ bảng nguồn này trong hồ sơ.

Đã loại 25/37 ảnh: ảnh nền trong suốt bị đen, ảnh chụp người/đồ vật, đồ thị lịch sử, bản đồ cổ quá phức
tạp hoặc chứa nội dung tranh chấp lãnh thổ. Truy vấn "map of Vietnam" chưa cho bản đồ phù hợp.

| ID | Trạng thái | Loại | Tác giả | Giấy phép | Nguồn |
|---|---|---|---|---|---|
| cand_005 | shortlisted_needs_ground_truth | line_chart | EdoDodo | CC BY-SA 3.0 | [Graph showing the monthly uploads of Com](https://commons.wikimedia.org/wiki/File:Graph_showing_the_monthly_uploads_of_Commons.png) |
| cand_006 | shortlisted_needs_ground_truth | line_chart | CoffeeWithMarkets | CC0 | [U.S. Households By Total Yearly Income (](https://commons.wikimedia.org/wiki/File:U.S._Households_By_Total_Yearly_Income_(Line_Graph).png) |
| cand_009 | draft_ground_truth_unverified | pie_chart | Shmorple | CC BY-SA 4.0 | [Pie Chart of Israeli Australian Location](https://commons.wikimedia.org/wiki/File:Pie_Chart_of_Israeli_Australian_Locations.png) |
| cand_010 | shortlisted_needs_ground_truth | pie_chart | Mikael Häggström, M.D. Author info - Reusing image | CC0 | [Pie chart of colorectal polyp etiologies](https://commons.wikimedia.org/wiki/File:Pie_chart_of_colorectal_polyp_etiologies.png) |
| cand_012 | shortlisted_needs_ground_truth | cycle_diagram | Ehud Tal | CC BY-SA 4.0 | [Diagram of the Water Cycle.jpg](https://commons.wikimedia.org/wiki/File:Diagram_of_the_Water_Cycle.jpg) |
| cand_013 | shortlisted_needs_ground_truth | cycle_diagram | NASA's Scientific Visualization Studio - Marit Jen | Public domain | [The Water Cycle (SVS30580).png](https://commons.wikimedia.org/wiki/File:The_Water_Cycle_(SVS30580).png) |
| cand_014 | shortlisted_needs_ground_truth | cycle_diagram | LangeLeslie | CC BY-SA 4.0 | [Water Cycle Diagram.jpeg](https://commons.wikimedia.org/wiki/File:Water_Cycle_Diagram.jpeg) |
| cand_015 | draft_ground_truth_unverified | cycle_diagram | Water_Cycle_-_blank.svg: *Wasserkreislauf.png: de: | CC BY-SA 3.0 | [Water Cycle-en.png](https://commons.wikimedia.org/wiki/File:Water_Cycle-en.png) |
| cand_016 | shortlisted_needs_ground_truth | cycle_diagram | Cyanocorax - https://openclipart.org/artist/Cyanoc | CC0 | [Butterfly life cycle diagram in English ](https://commons.wikimedia.org/wiki/File:Butterfly_life_cycle_diagram_in_English_as.png) |
| cand_018 | draft_ground_truth_unverified | cycle_diagram | Ana Mª Fuentes | CC BY-SA 4.0 | [Ciclo de vida mariposa Ilustración Ana M](https://commons.wikimedia.org/wiki/File:Ciclo_de_vida_mariposa_Ilustraci%C3%B3n_Ana_M%C2%AA_Fuentes_Vectorial.png) |
| cand_020 | shortlisted_needs_ground_truth | flow_diagram | RoRo | CC BY-SA 3.0 | [Photosynthesis-gl.png](https://commons.wikimedia.org/wiki/File:Photosynthesis-gl.png) |
| cand_028 | draft_ground_truth_unverified | geometry | Castle Queens | CC BY-SA 4.0 | [Pythagorean theorem (Isosceles Triangle)](https://commons.wikimedia.org/wiki/File:Pythagorean_theorem_(Isosceles_Triangle).jpg) |
