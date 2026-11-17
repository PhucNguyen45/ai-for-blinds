"""Kho chủ đề cho dữ liệu HUẤN LUYỆN. CỐ Ý tách khỏi chủ đề/tiêu đề của benchmark dev/test.

Quy tắc: không tiêu đề, chủ đề (nước, bướm, cây đậu, sách thư viện...) hay bộ nhãn nào trùng với benchmark.
`FORBIDDEN_TITLES` liệt kê tiêu đề của benchmark; bộ sinh còn đối chiếu động với benchmark cục bộ (nếu có).
"""

# Tiêu đề đang dùng trong benchmark dev/test (tĩnh, để kiểm tra ngay cả khi máy không có benchmark).
FORBIDDEN_TITLES = {
    "Số sách thư viện cho mượn trong tuần", "Lượng mưa trung bình các tháng mùa mưa",
    "Số học sinh tham gia các câu lạc bộ", "Số quả cam thu hoạch của các tổ",
    "Số huy chương của các đội", "Số thùng rác phân loại ở các khu",
    "Nhiệt độ trung bình các tháng đầu năm", "Số học sinh đến thư viện mỗi ngày",
    "Số cuốn sách đọc được qua các tuần", "Số cây xanh của trường qua các năm",
    "Chiều cao của cây đậu theo ngày", "Phương tiện học sinh đến trường",
    "Môn học yêu thích của lớp", "Cơ cấu sử dụng đất của xã", "Nguồn điện của một quốc gia",
    "Điểm kiểm tra giữa kì", "Số sản phẩm bán được theo tuần", "Số ngày có mưa trong tháng",
    "Kết quả thi đấu của các đội", "Khối lượng rác thu gom trong tuần (kg)",
    "Quy trình xử lý rác tái chế", "Chuẩn bị trước khi đi học", "Các bước chấm và trả bài kiểm tra",
    "Quy trình làm một bài toán", "Kiểm tra sức khỏe đầu giờ", "Vòng tuần hoàn của nước",
    "Vòng đời của bướm", "Vòng đời của cây đậu", "Sơ đồ khu phố", "Tam giác ABC vuông tại A",
    "Hình chữ nhật ABCD", "Đường tròn tâm O", "Tam giác ABC với hai góc cho trước",
    "Số cây trồng được của các lớp",
}

CATSETS = {
    "lop": [f"Lớp {g}{c}" for g in (1, 2, 3, 4, 5) for c in "ABC"],
    "to": [f"Tổ {i}" for i in range(1, 9)],
    "ngay": ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7"],
    "thang": [f"Tháng {i}" for i in range(1, 13)],
    "nam": [str(y) for y in range(2014, 2026)],
    "tuan": [f"Tuần {i}" for i in range(1, 9)],
    "mon": ["Toán", "Tiếng Việt", "Tiếng Anh", "Khoa học", "Lịch sử", "Địa lí", "Âm nhạc", "Mỹ thuật"],
    "dongvat": ["Gà", "Vịt", "Lợn", "Bò", "Trâu", "Dê", "Ngỗng"],
    "traicay": ["Cam", "Bưởi", "Xoài", "Chuối", "Dưa hấu", "Ổi", "Nhãn"],
    "dodung": ["Bút", "Vở", "Thước", "Cặp", "Tẩy", "Màu vẽ"],
    "doi": [f"Đội {c}" for c in "ABCDEFG"],
    "khu": [f"Khu {c}" for c in "ABCDEFG"],
    "ban": ["An", "Bình", "Chi", "Dũng", "Hà", "Lan", "Minh", "Nam"],
    "thanhpho": ["Hà Nội", "Huế", "Đà Nẵng", "Cần Thơ", "Đà Lạt", "Hải Phòng"],
    "truong": [f"Trường {c}" for c in "ABCDEF"],
}
SEQUENTIAL = {"ngay", "thang", "nam", "tuan"}  # chọn một đoạn liên tiếp, đúng thứ tự thời gian

# (tiêu đề, nhãn trục đứng, đơn vị, bộ nhãn, giá trị nhỏ nhất, lớn nhất)
BAR_THEMES = [
    ("Số cây hoa trồng được của các tổ", "Số cây", "cây", "to", 4, 40),
    ("Số bạn đi tham quan bảo tàng theo lớp", "Số bạn", "bạn", "lop", 8, 45),
    ("Số quyển truyện được mượn theo ngày", "Số quyển", "quyển", "ngay", 3, 40),
    ("Lượng nước đo được ở bể chứa theo tháng", "Lượng nước (m³)", "mét khối", "thang", 5, 45),
    ("Số điểm mười của các môn học", "Số điểm mười", "điểm mười", "mon", 2, 35),
    ("Số vật nuôi của một trang trại", "Số con", "con", "dongvat", 4, 45),
    ("Khối lượng trái cây bán được trong ngày", "Khối lượng (kg)", "kg", "traicay", 5, 45),
    ("Số đồ dùng học tập đã quyên góp", "Số cái", "cái", "dodung", 5, 45),
    ("Số bàn thắng của các đội trong giải", "Số bàn thắng", "bàn thắng", "doi", 1, 30),
    ("Số thùng quần áo quyên góp ở các khu", "Số thùng", "thùng", "khu", 3, 40),
    ("Số lượt khách tham quan theo năm", "Số lượt (trăm)", "trăm lượt", "nam", 5, 45),
    ("Số bạn đạt học sinh giỏi theo lớp", "Số bạn", "bạn", "lop", 2, 35),
]

LINE_THEMES = [
    ("Nhiệt độ ngoài trời trong tuần", "Nhiệt độ (°C)", "°C", "ngay", 10, 40),
    ("Số bạn đến phòng đọc sách theo tuần", "Số bạn", "bạn", "tuan", 5, 40),
    ("Số xe đạp gửi ở sân trường theo ngày", "Số xe", "xe", "ngay", 5, 40),
    ("Số cây xanh của xã qua các năm", "Số cây (trăm)", "trăm cây", "nam", 5, 40),
    ("Lượng sữa thu được mỗi tháng", "Lượng sữa (lít)", "lít", "thang", 5, 40),
    ("Chiều cao của cây chuối theo tuần", "Chiều cao (cm)", "cm", "tuan", 5, 40),
    ("Số bạn tham gia câu lạc bộ theo năm", "Số bạn", "bạn", "nam", 5, 40),
    ("Quãng đường đi bộ mỗi ngày của bạn Nam", "Quãng đường (km)", "ki lô mét", "ngay", 5, 40),
]

PIE_THEMES = [
    ("Loại quả học sinh thích nhất", ["Cam", "Xoài", "Chuối", "Dưa hấu", "Ổi"]),
    ("Nơi học sinh đọc sách", ["Ở nhà", "Ở thư viện", "Ở lớp"]),
    ("Nơi học sinh đi chơi cuối tuần", ["Công viên", "Rạp chiếu phim", "Nhà ông bà", "Siêu thị"]),
    ("Món ăn sáng được chọn nhiều", ["Phở", "Bánh mì", "Xôi", "Cháo"]),
    ("Rác thải trong một tuần", ["Giấy", "Nhựa", "Thức ăn thừa", "Thủy tinh"]),
    ("Thời gian trong một ngày của bạn Lan", ["Học", "Ngủ", "Chơi", "Giúp mẹ", "Ăn uống"]),
    ("Vật nuôi trong làng", ["Gà", "Vịt", "Lợn", "Trâu", "Chó"]),
    ("Cơ cấu cây trồng của hợp tác xã", ["Lúa", "Ngô", "Khoai", "Rau"]),
    ("Phương tiện của các gia đình trong xóm", ["Xe đạp", "Xe máy", "Ô tô"]),
    ("Bộ môn thể thao được yêu thích", ["Bóng đá", "Cầu lông", "Bơi lội", "Chạy", "Cờ vua"]),
]

# (tiêu đề, tiêu đề cột đầu, bộ nhãn hàng, nhãn cột, kiểu, nhỏ nhất, lớn nhất, đơn vị)
TABLE_SCHEMAS = [
    ("Số sách của thư viện các lớp", "Lớp", "lop", ["Truyện", "Khoa học", "Thơ"], "int", 5, 60, "quyển"),
    ("Điểm thi các môn của các bạn", "Bạn", "ban", ["Toán", "Tiếng Việt", "Khoa học", "Tiếng Anh"], "dec", 5, 10, "điểm"),
    ("Nhiệt độ cao nhất của các thành phố", "Thành phố", "thanhpho", ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5"], "int", 18, 38, "°C"),
    ("Số huy chương của các trường", "Trường", "truong", ["Vàng", "Bạc", "Đồng"], "int", 0, 9, "huy chương"),
    ("Lượng hàng bán được theo tháng", "Tháng", "thang", ["Gạo", "Đường", "Muối"], "int", 10, 90, "ki lô gam"),
    ("Số ngày nghỉ của các lớp", "Lớp", "lop", ["Học kì 1", "Học kì 2"], "int", 0, 12, "ngày"),
    ("Thời gian chạy của các bạn", "Bạn", "ban", ["Lần 1", "Lần 2", "Lần 3"], "int", 9, 20, "giây"),
]

# Quy trình tuyến tính: (tiêu đề, các bước)
CHAINS = [
    ("Các bước rửa tay đúng cách", ["Làm ướt tay", "Xoa xà phòng", "Chà kĩ hai tay", "Xả nước sạch", "Lau khô tay"]),
    ("Quy trình trồng rau", ["Làm đất", "Gieo hạt", "Tưới nước", "Nhổ cỏ", "Thu hoạch"]),
    ("Các bước nấu cơm", ["Vo gạo", "Cho nước", "Bật nồi", "Chờ cơm chín"]),
    ("Đường đi của lá thư", ["Viết thư", "Bỏ vào hòm thư", "Phân loại ở bưu điện", "Chuyển đi", "Giao cho người nhận"]),
    ("Các bước làm bài văn", ["Đọc đề", "Lập dàn ý", "Viết bài", "Đọc lại"]),
    ("Quy trình làm giấy", ["Thu gom giấy cũ", "Nghiền thành bột", "Ép mỏng", "Sấy khô", "Cắt thành tờ"]),
    ("Các bước đánh răng", ["Lấy kem", "Chải mặt ngoài", "Chải mặt trong", "Súc miệng"]),
    ("Đường đi của thức ăn", ["Miệng", "Thực quản", "Dạ dày", "Ruột non", "Ruột già"]),
    ("Các bước may một chiếc áo", ["Đo người", "Cắt vải", "May ráp", "Đính cúc"]),
]

# Rẽ nhánh: (tiêu đề, bắt đầu, câu hỏi, việc nếu có, việc nếu không, kết thúc)
BRANCHES = [
    ("Quyết định mang dù", "Bắt đầu", "Trời có mưa?", "Mang dù", "Đội mũ", "Ra khỏi nhà"),
    ("Chọn cách đến trường", "Xuất phát", "Nhà có gần trường?", "Đi bộ", "Đi xe buýt", "Đến trường"),
    ("Xử lí khi bút hết mực", "Viết bài", "Còn bút khác không?", "Dùng bút khác", "Xin bạn mượn", "Viết tiếp"),
    ("Qua đường an toàn", "Đến vạch kẻ", "Đèn có màu xanh?", "Đi qua đường", "Đứng chờ", "Sang bên kia"),
]
# Rẽ nhánh một phía: (tiêu đề, bắt đầu, việc chung, câu hỏi, nếu có, nếu không)
SIDES = [
    ("Kiểm tra bài trước khi nộp", "Bắt đầu", "Làm xong bài", "Còn sai chỗ nào?", "Sửa lại", "Nộp bài"),
    ("Chuẩn bị bữa trưa", "Bắt đầu", "Mở tủ lạnh", "Còn rau không?", "Nấu canh rau", "Đi chợ mua rau"),
    ("Kiểm tra pin đồ chơi", "Bắt đầu", "Bật công tắc", "Đèn có sáng?", "Chơi tiếp", "Thay pin mới"),
]
# Vòng lặp: (tiêu đề, bước 1, bước 2, câu hỏi, bước khi có)
LOOPS = [
    ("Học thuộc một bài thơ", "Đọc bài thơ", "Đọc nhẩm", "Đã thuộc chưa?", "Đọc cho cô nghe"),
    ("Giải một bài toán đố", "Đọc đề", "Tóm tắt đề", "Đã hiểu đề chưa?", "Viết lời giải"),
    ("Luyện viết chữ đẹp", "Xem chữ mẫu", "Viết một dòng", "Chữ đã đều chưa?", "Viết sang dòng mới"),
]

# Chu trình: (tiêu đề, các giai đoạn)
CYCLES = [
    ("Vòng đời của ếch", ["Trứng ếch", "Nòng nọc", "Ếch con", "Ếch trưởng thành"]),
    ("Các mùa trong năm", ["Xuân", "Hạ", "Thu", "Đông"]),
    ("Vòng đời của gà", ["Trứng", "Gà con", "Gà choai", "Gà trưởng thành"]),
    ("Ngày và đêm", ["Bình minh", "Buổi trưa", "Hoàng hôn", "Ban đêm"]),
    ("Vòng đời của muỗi", ["Trứng", "Bọ gậy", "Cung quăng", "Muỗi trưởng thành"]),
    ("Chu trình của rác thải", ["Thải rác", "Thu gom", "Xử lí", "Tái sử dụng"]),
    ("Chu trình trồng lúa", ["Gieo mạ", "Cấy lúa", "Lúa chín", "Thu hoạch", "Phơi thóc"]),
    ("Một vòng quay của đồng hồ nước", ["Mở vòi", "Nước chảy qua", "Số đếm tăng", "Đóng vòi"]),
    ("Các giai đoạn của mặt trăng", ["Trăng non", "Trăng lưỡi liềm", "Trăng tròn", "Trăng khuyết"]),
]

MAP_TITLES = ["Sơ đồ khu dân cư", "Sơ đồ khu vực quanh trường", "Sơ đồ làng em", "Sơ đồ thị trấn nhỏ"]
MAP_PLACES = ["Trường học", "Bệnh viện", "Công viên", "Chợ", "Thư viện", "Bưu điện", "Nhà văn hóa",
              "Sân vận động", "Nhà ga", "Siêu thị", "Trạm y tế", "Sân chơi"]

# Gợi ý chụp lại theo lỗi chụp
CAPTURE_GUIDANCE = {
    "blur": [
        "Ảnh bị mờ nên mình chưa đọc rõ được nội dung. Bạn giữ điện thoại thật chắc tay, lùi ra một chút để cả trang vào khung, rồi chụp lại nhé.",
        "Ảnh này mờ quá, mình không đọc được chữ và số. Bạn giữ yên điện thoại vài giây trước khi chụp, rồi thử lại nhé.",
    ],
    "dark": [
        "Ảnh quá tối nên mình không đọc được. Bạn bật đèn hoặc đưa trang sách ra chỗ sáng hơn rồi chụp lại nhé.",
        "Trang sách đang bị thiếu sáng, mình chưa nhìn rõ. Bạn thử chụp lại ở nơi có ánh sáng tốt hơn nhé.",
    ],
    "glare": [
        "Ảnh bị chói sáng che mất một phần nên mình không đọc đủ. Bạn nghiêng nhẹ điện thoại hoặc tránh ánh đèn rọi thẳng vào trang rồi chụp lại nhé.",
        "Có một vùng bị loá sáng trên ảnh. Bạn đổi góc cầm điện thoại một chút để hết loá rồi chụp lại nhé.",
    ],
    "cropped_left": ["Hình bị cắt mất phần bên trái. Bạn dịch điện thoại sang trái một chút và lùi ra xa hơn để thấy đủ cả hình rồi chụp lại nhé."],
    "cropped_right": ["Hình bị cắt mất phần bên phải. Bạn dịch điện thoại sang phải một chút và lùi ra xa hơn để thấy đủ cả hình rồi chụp lại nhé."],
    "cropped_top": ["Hình bị cắt mất phần phía trên. Bạn nâng điện thoại lên một chút và lùi ra xa hơn để thấy đủ cả hình rồi chụp lại nhé."],
    "cropped_bottom": ["Hình bị cắt mất phần phía dưới. Bạn hạ điện thoại xuống một chút và lùi ra xa hơn để thấy đủ cả hình rồi chụp lại nhé."],
}


# ---------------------------------------------------------------- sinh theo thủ tục (mở rộng không gian nội dung)
# Chỉ dùng từ vựng thường ngày, KHÔNG dùng chủ đề của benchmark (nước, bướm, cây đậu...).
VERBS = ["Gấp", "Lau", "Xếp", "Rửa", "Cắt", "Dán", "Tưới", "Quét", "Gọt", "Vẽ", "Đọc", "Viết", "Nấu", "Phơi",
         "Nhặt", "Đo", "Cân", "Đếm", "Chép", "Tô", "Sắp", "Mở", "Đóng", "Bọc", "Buộc", "May", "Nặn", "Kiểm tra",
         "Chuẩn bị", "Lấy"]
OBJECTS = ["sách vở", "bút chì", "bảng đen", "khăn mặt", "rau xanh", "cặp sách", "áo khoác", "bát đĩa",
           "giấy màu", "bàn học", "tranh vẽ", "sân trường", "bài tập", "chậu hoa", "đèn học", "ghế đá", "gạo",
           "vải", "thước kẻ", "hộp bút", "tủ sách", "rổ rau", "quả cam", "khăn quàng"]
GOALS = ["làm thiệp tặng mẹ", "dọn dẹp lớp học", "chăm sóc vườn rau", "chuẩn bị bữa ăn", "làm bài tập về nhà",
         "trang trí góc học tập", "tổ chức buổi liên hoan", "làm đồ chơi từ giấy", "sắp xếp cặp sách",
         "chuẩn bị đi dã ngoại", "gói quà sinh nhật", "dọn dẹp bàn ăn"]
QUESTIONS = ["Đã xong chưa?", "Còn thời gian không?", "Trời có nắng?", "Bạn có đói không?", "Đèn đã sáng chưa?",
             "Có đủ dụng cụ không?", "Đã làm đúng chưa?", "Cô giáo có đồng ý không?", "Có ai giúp không?"]
STARTS = ["Bắt đầu", "Xuất phát", "Mở đầu"]
CYCLE_STAGES = ["Thu hoạch", "Chế biến", "Đóng gói", "Vận chuyển", "Bán hàng", "Sử dụng", "Thải bỏ", "Thu gom",
                "Phân loại", "Tái chế", "Sản phẩm mới", "Học bài", "Làm bài", "Chấm bài", "Sửa lỗi", "Ôn tập",
                "Kiểm tra", "Thức dậy", "Ăn sáng", "Đi học", "Về nhà", "Làm việc nhà", "Nghỉ ngơi", "Đi ngủ"]
CYCLE_TOPICS = ["học tập", "sản xuất", "tái chế", "một ngày", "luân chuyển hàng hóa", "ôn luyện", "sinh hoạt"]


def _act(rng, used=()):
    while True:
        a = f"{rng.choice(VERBS)} {rng.choice(OBJECTS)}"
        if a not in used:
            return a


def proc_chain(rng):
    steps = []
    for _ in range(rng.randint(4, 5)):
        steps.append(_act(rng, steps))
    return f"Các bước {rng.choice(GOALS)}", steps


def proc_branch(rng):
    y = _act(rng)
    return (f"Quyết định khi {rng.choice(GOALS)}", rng.choice(STARTS), rng.choice(QUESTIONS), y,
            _act(rng, [y]), rng.choice(["Hoàn thành", "Nghỉ ngơi", "Xong việc"]))


def proc_side(rng):
    common = _act(rng)
    y = _act(rng, [common])
    return (f"Kiểm tra khi {rng.choice(GOALS)}", rng.choice(STARTS), common, rng.choice(QUESTIONS), y,
            _act(rng, [common, y]))


def proc_loop(rng):
    a = _act(rng)
    b = _act(rng, [a])
    return (f"Lặp lại khi {rng.choice(GOALS)}", a, b, rng.choice(QUESTIONS), _act(rng, [a, b]))


def proc_cycle(rng):
    k = rng.randint(3, 6)
    return f"Chu trình {rng.choice(CYCLE_TOPICS)}", rng.sample(CYCLE_STAGES, k)
