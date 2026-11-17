/// Mọi câu app nói ra và chữ hiển thị đều nằm ở đây.
///
/// Người dùng không nhìn màn hình, nên câu nói quan trọng hơn chữ hiển thị.
/// Quy tắc viết: câu ngắn, không dùng từ chỉ vị trí thị giác ("bên trái",
/// "phía trên"), luôn nói việc người dùng làm được tiếp theo.
class S {
  S._();

  static const appName = 'SgBe';

  // Khởi động
  static const greeting =
      'SgBe sẵn sàng. Chạm vào giữa màn hình hoặc bấm nút âm lượng để chụp trang sách.';
  static const voiceMissingEnglish =
      'Vietnamese voice is not installed. Please install Vietnamese voice data '
      'in your phone text to speech settings.';
  static const voiceMissingShown =
      'Điện thoại chưa có giọng đọc tiếng Việt. Vào Cài đặt, Trợ năng, '
      'Chuyển văn bản thành giọng nói, tải dữ liệu giọng tiếng Việt.';

  // Chụp và đọc
  static const working = 'Đang đọc trang, xin chờ.';
  static const stillWorking = 'Vẫn đang đọc trang này, xin chờ thêm.';
  static const unreadableHint =
      'Có chỗ mình không đọc được. Bạn có thể chụp lại, giữ máy thẳng và đủ sáng.';
  static const retakeHint = 'Bạn thử chụp lại, giữ máy thẳng, cách trang sách khoảng ba mươi phân và đủ sáng.';
  static const nothingToRepeat = 'Chưa có trang nào. Hãy chụp một trang sách trước.';
  static const cameraNotReady = 'Camera chưa sẵn sàng. Bạn thử lại sau giây lát.';
  static const cameraDenied =
      'SgBe chưa được phép dùng camera. Bạn mở cài đặt điện thoại và cấp quyền camera cho SgBe.';
  static const noCamera = 'Không tìm thấy camera. Bạn có thể dùng nút Chọn ảnh.';
  static const pickCancelled = 'Đã huỷ chọn ảnh.';

  // Lỗi mạng (khi máy chủ không trả về được câu thông báo của nó)
  static const errTimeout = 'Máy chủ trả lời quá lâu. Bạn thử chụp lại nhé.';
  static const errOffline =
      'Không kết nối được máy chủ. Bạn kiểm tra Wi-Fi và địa chỉ máy chủ trong Cài đặt.';
  static const errBadData = 'Máy chủ trả về dữ liệu lạ. Bạn thử lại sau nhé.';

  // Màn hình chính
  static const captureLabel =
      'Chụp trang. Chạm hai lần để chụp. Có thể bấm nút âm lượng để chụp. '
      'Khi đang đọc, chạm một lần để dừng.';
  static const captureVisual = 'Chạm để chụp';
  static const repeat = 'Đọc lại';
  static const repeatHint = 'Đọc lại mô tả trang vừa chụp';
  static const pickImage = 'Chọn ảnh';
  static const pickImageHint = 'Chọn một ảnh có sẵn trong máy để đọc';
  static const settings = 'Cài đặt';
  static const settingsHint = 'Mở cài đặt máy chủ và tốc độ đọc';
  static const stateIdle = 'Sẵn sàng';
  static const stateSending = 'Đang đọc trang…';
  static const stateSpeaking = 'Đang nói';
  static const stateError = 'Có lỗi';

  // Cài đặt
  static const serverUrl = 'Địa chỉ máy chủ';
  static const serverUrlHint =
      'Máy ảo dùng http://10.0.2.2:8000. Điện thoại thật dùng địa chỉ IP của laptop, '
      'ví dụ http://192.168.1.15:8000';
  static const checkServer = 'Kiểm tra kết nối';
  static const serverOkPrefix = 'Đã kết nối máy chủ.';
  static const serverModeMock = 'Máy chủ đang ở chế độ thử, câu trả lời chưa phải từ mô hình thật.';
  static const speechRate = 'Tốc độ đọc';
  static const tryVoice = 'Nghe thử';
  static const tryVoiceSentence = 'Đây là tốc độ đọc hiện tại.';
  static const pageType = 'Loại trang';
  static const demoMode = 'Chế độ demo';
  static const demoModeHint = 'Không cần máy chủ, trả lời mẫu để thử giao diện';
  static const demoDescription =
      'Đây là chế độ demo, ảnh không được gửi đi đâu. Trang có một đoạn văn về cây xanh '
      'và một hình vẽ cái cây có rễ, thân và lá. Bạn có muốn chụp lại không?';
  static const openTtsSettings = 'Mở cài đặt giọng đọc';
  static const saved = 'Đã lưu.';

  static const pageTypes = <String, String>{
    'auto': 'Tự nhận',
    'text': 'Đoạn văn',
    'map': 'Bản đồ',
    'chart': 'Biểu đồ',
    'table': 'Bảng',
    'figure': 'Hình vẽ',
    'mixed': 'Chữ và hình',
  };
}
