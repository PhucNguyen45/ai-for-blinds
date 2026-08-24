# Bộ ảnh SGK để đo mô hình

Đây là bộ đo quan trọng nhất của đề tài. Các bộ dữ liệu tải trên mạng đều là
ảnh sạch, chụp thẳng; học sinh khiếm thị chụp thì nghiêng, loá đèn, có bóng
tay, mất góc trang. Chỉ bộ này phản ánh đúng cảnh dùng thật.

## Cách thêm ảnh

1. Chép file ảnh vào `images/`, đặt tên đúng như trường `file` trong
   `annotations.json`. Năm trang đầu cần:

   ```
   images/ldl4_bia.png
   images/ldl4_tacgia.png
   images/ldl4_tr06_07.png
   images/ldl4_tr08_09.png
   images/ldl4_tr10_11.png
   ```

2. Thêm trang mới thì chép một khối trong `annotations.json` rồi điền tay.

## Cách đặt tên

`<ma_sach>_tr<so_trang>.png` — ví dụ `ldl4_tr08_09.png` là sách Lịch sử và Địa
lí 4, trang 8 và 9 chụp chung một ảnh.

Mã sách hiện dùng: `ldl4` = Lịch sử và Địa lí 4, Kết nối tri thức.

## Cấu trúc một mục trong annotations.json

| Trường | Nghĩa |
|---|---|
| `loai` | Loại nội dung trên trang, để tính điểm theo từng loại |
| `kho` | `de`, `trung_binh`, `kho` — trang khó mà điểm thấp thì bình thường |
| `phai_co` | Thông tin bắt buộc đọc đúng. Thiếu là trừ điểm |
| `nen_co` | Có thì tốt, không có không trừ. Dùng để phân biệt model tốt và rất tốt |

Viết `phai_co` theo nguyên tắc: **chỉ những gì học sinh cần nghe để hiểu
trang sách**. Không liệt kê mọi chữ trên trang — mục tiêu là đo tính hữu ích,
không phải đo OCR thuần.

## Chạy đo

```
.venv\Scripts\python.exe scripts\eval_sgk.py
.venv\Scripts\python.exe scripts\eval_sgk.py --model qwen/qwen3-vl-30b-a3b-instruct
.venv\Scripts\python.exe scripts\eval_sgk.py --che-do doc   # chế độ đọc chữ
```

Kết quả ghi ra `data/eval/sgk_results.json`.

## Chụp ảnh thế nào cho đúng mục tiêu

Bộ hiện tại là ảnh quét sạch — dùng làm mốc trần, tức là điểm cao nhất model
có thể đạt. Muốn có số thật thì phải bổ sung ảnh chụp trong điều kiện thật:

- Chụp bằng đúng điện thoại sẽ dùng, không phải máy quét.
- Ánh sáng lớp học, có cả trường hợp thiếu sáng.
- Nghiêng 10 đến 20 độ, vì người không nhìn thấy khó canh thẳng.
- Có ngón tay giữ trang lọt vào khung hình.
- Chụp thiếu một góc trang.

Đặt tên kèm hậu tố điều kiện: `ldl4_tr08_09_nghieng.png`,
`ldl4_tr08_09_thieu_sang.png`. Cùng một trang, nhiều điều kiện — nhờ vậy đo
được model tụt bao nhiêu khi ảnh xấu đi, đó mới là con số đáng đưa vào báo cáo.
