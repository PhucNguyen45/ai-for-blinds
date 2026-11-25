/// Mọi câu app nói ra và chữ hiển thị đều nằm ở đây.
///
/// Người dùng không nhìn màn hình, nên câu nói quan trọng hơn chữ hiển thị.
/// Quy tắc viết: câu ngắn, luôn nói việc người dùng làm được tiếp theo.
/// Vị trí nút ("góc trên bên trái") chỉ dùng trong lời hướng dẫn, vì vị trí các nút không bao giờ đổi.
class S {
  S._();

  static const appName = 'SgBe';

  // Khởi động và hướng dẫn
  static const greeting = 'SgBe sẵn sàng. Bấm nút âm lượng, hoặc chạm hai lần vào giữa màn hình để chụp trang sách.';
  static const tutorial =
      'Chào bạn, đây là SgBe, trợ lý đọc sách giáo khoa. '
      'Chạm một lần vào bất kỳ đâu để nghe tên nút. Chạm hai lần để dùng nút đó. '
      'Giữa màn hình là vùng chụp. Bấm nút âm lượng để chụp nhanh. '
      'Mép dưới có ba nút: Đọc lại, Hỏi, và Thư viện. '
      'Góc trên bên trái là Cài đặt, góc trên bên phải là Trợ giúp.';
  static const help =
      'Hướng dẫn. Giữa màn hình là vùng chụp: đưa máy lên trên trang sách, cách khoảng ba mươi phân, '
      'rồi bấm nút âm lượng hoặc chạm hai lần vào giữa màn hình. '
      'Mép dưới có ba nút. Bên trái là Đọc lại, ở giữa là Hỏi, bên phải là Thư viện. '
      'Góc trên bên trái là Cài đặt, góc trên bên phải là Trợ giúp. '
      'Chạm một lần để nghe tên nút, chạm hai lần để dùng. Rê ngón tay để dò các nút. '
      'Đang đọc mà muốn dừng, bạn chạm vào màn hình hoặc bấm nút âm lượng.';
  static const voiceMissingEnglish =
      'Vietnamese voice is not installed. Please install Vietnamese voice data '
      'in your phone text to speech settings.';
  static const voiceMissingShown =
      'Điện thoại chưa có giọng đọc tiếng Việt. Vào Cài đặt, Trợ năng, '
      'Chuyển văn bản thành giọng nói, tải dữ liệu giọng tiếng Việt.';

  // Chụp và đọc
  static const working = 'Đang đọc trang, xin chờ.';
  static const stillWorking = 'Vẫn đang đọc trang này, xin chờ thêm.';
  static const unreadableHint = 'Có chỗ mình không đọc được. Bạn có thể chụp lại, giữ máy thẳng và đủ sáng.';
  static const retakeHint = 'Bạn thử chụp lại, giữ máy thẳng, cách trang sách khoảng ba mươi phân và đủ sáng.';
  static const truncatedHint = 'Phần mô tả bị ngắt giữa chừng. Bạn có thể bấm Hỏi để hỏi thêm về phần còn lại.';
  static const nothingToRepeat = 'Chưa có trang nào. Hãy chụp một trang sách trước.';
  static const cameraNotReady = 'Camera chưa sẵn sàng. Bạn thử lại sau giây lát.';
  static const cameraOpening = 'Đang mở camera…';
  static const cameraDenied =
      'SgBe chưa được phép dùng camera. Bạn mở cài đặt điện thoại và cấp quyền camera cho SgBe.';
  static const noCamera = 'Không tìm thấy camera. Bạn có thể chọn ảnh có sẵn trong Cài đặt.';
  static const pickCancelled = 'Đã huỷ chọn ảnh.';
  static const cameraReady = 'Camera sẵn sàng. Chạm hai lần hoặc bấm nút âm lượng để chụp.';

  // Lỗi mạng (khi máy chủ không trả về được câu thông báo của nó)
  static const errTimeout = 'Máy chủ trả lời quá lâu. Bạn thử chụp lại nhé.';
  static const errOffline = 'Không kết nối được máy chủ. Bạn kiểm tra Wi-Fi và địa chỉ máy chủ trong Cài đặt.';
  static const errBadData = 'Máy chủ trả về dữ liệu lạ. Bạn thử lại sau nhé.';

  // Màn hình chính: nhãn (TalkBack đọc, app cũng đọc khi chạm một lần)
  static const captureLabel = 'Vùng chụp';
  static const captureSay = 'Vùng chụp. Chạm hai lần để chụp trang sách. Có thể bấm nút âm lượng.';
  static const resultLabel = 'Kết quả';
  static const resultSay = 'Kết quả trang vừa chụp. Chạm hai lần để chụp trang mới.';
  static const errorSay = 'Có lỗi. Chạm hai lần để quay lại camera.';
  static const busySay = 'Đang đọc trang, xin chờ.';
  static const captureHint = 'Chạm hai lần để chụp';
  static const newPageHint = 'Chạm hai lần: chụp trang mới';
  static const retryHint = 'Chạm hai lần: quay lại camera';
  static const resultTitle = 'Trang vừa chụp';
  static const repeat = 'Đọc lại';
  static const repeatSay = 'Đọc lại. Chạm hai lần để nghe lại mô tả trang.';
  static const ask = 'Hỏi';
  static const askSay = 'Hỏi. Chạm hai lần để hỏi thêm về trang vừa chụp.';
  static const library = 'Thư viện';
  static const librarySay = 'Thư viện. Chạm hai lần để nghe sách đã số hóa.';
  static const settings = 'Cài đặt';
  static const settingsSay = 'Cài đặt. Chạm hai lần để mở.';
  static const helpLabel = 'Trợ giúp';
  static const helpSay = 'Trợ giúp. Chạm hai lần để nghe hướng dẫn.';
  static const back = 'Quay lại';
  static const backSay = 'Quay lại. Chạm hai lần để về màn hình trước.';
  static const homeSay = 'Màn hình chụp.';
  static const captionIdle = 'Chạm một lần để nghe, chạm hai lần để dùng';
  static const stateSending = 'Đang đọc trang…';
  static const stateAsking = 'Đang hỏi…';
  static const stateError = 'Có lỗi';

  // Hỏi
  static const askTitle = 'Hỏi về trang này';
  static const askOpen =
      'Hỏi về trang vừa chụp. Bấm nút âm lượng, hoặc chạm hai lần nút Nói câu hỏi ngay trên nút '
      'Quay lại, rồi nói câu hỏi của bạn.';
  static const askOpenNoStt =
      'Hỏi về trang vừa chụp. Điện thoại chưa nhận được giọng nói, nên có ba câu hỏi gợi ý '
      'ở giữa màn hình. Nút Quay lại ở mép dưới.';
  static const asking = 'Đang hỏi, xin chờ.';
  static const askNeedPage = 'Hãy chụp một trang trước khi hỏi.';
  static const askCannot = 'Trang này chưa đọc được nên chưa hỏi được. Bạn chụp lại trang nhé.';
  static const askEmpty = 'Chưa có câu trả lời. Bấm nút âm lượng rồi nói câu hỏi.';
  static const askEmptyNoStt = 'Chưa có câu trả lời. Chạm hai lần vào một câu hỏi gợi ý.';
  static const askEmptyShown =
      'Bấm nút âm lượng hoặc chạm hai lần nút Nói câu hỏi, rồi nói. '
      'Ví dụ: "Hình vẽ có mấy phần?"';
  static const askEmptyShownNoStt = 'Chọn một câu hỏi bên dưới. Câu trả lời sẽ được đọc to.';

  // Nói câu hỏi (nhận giọng nói có sẵn của Android)
  static const mic = 'Nói câu hỏi';
  static const micSay = 'Nói câu hỏi. Chạm hai lần rồi nói. Có thể bấm nút âm lượng.';
  static const micStop = 'Đang nghe';
  static const micStopSay = 'Đang nghe. Chạm hai lần để dừng.';
  static const sttPrompt = 'Mời bạn nói.';
  static const listeningShown = 'Đang nghe…';
  static const sttNoMatch = 'Mình chưa nghe rõ. Bạn bấm nút âm lượng rồi nói lại nhé.';
  static const sttNetwork =
      'Nhận giọng nói đang cần mạng mà mạng yếu. Bạn thử lại, hoặc tải gói nhận giọng nói '
      'tiếng Việt ngoại tuyến cho điện thoại.';
  static const sttPermission = 'SgBe chưa được phép dùng micro. Bạn cấp quyền micro cho SgBe trong cài đặt điện thoại.';
  static const sttLanguage =
      'Điện thoại chưa có nhận giọng nói tiếng Việt. Bạn vào cài đặt Google, mục Giọng nói, '
      'tải tiếng Việt.';
  static const sttUnavailable = 'Điện thoại này không có dịch vụ nhận giọng nói. Bạn dùng các câu hỏi gợi ý.';
  static const sttBusy = 'Micro đang bận, bạn thử lại sau giây lát.';
  static const sttOther = 'Không nhận được giọng nói. Bạn thử lại nhé.';
  static const answerLabel = 'Câu trả lời';
  static const answerSay = 'Câu trả lời. Chạm hai lần để nghe lại.';
  static const youAsked = 'Bạn hỏi';
  static const askSuggestions = [
    'Trang này nói về điều gì?',
    'Hình vẽ gồm những phần nào?',
    'Giải thích lại cho dễ hiểu hơn',
  ];

  // Thư viện
  static const sampleBadge = 'Bản mẫu';
  static String libraryCount(int n) => 'Thư viện. Có $n cuốn sách.';
  static const originServer = 'Sách lấy từ máy chủ của nhóm.';
  static const originCache = 'Chưa kết nối được máy chủ, đang dùng bản đã lưu trên máy.';
  static const originSample = 'Đây là sách mẫu để thử.';
  static const backAtBottom = 'Nút Quay lại ở mép dưới.';
  static const badgeServer = 'Máy chủ';
  static const badgeCache = 'Đã lưu';
  static const noteServer = 'Sách do nhóm số hóa. Sách ghi "chưa duyệt" là lời mô tả chưa có người kiểm tra lại.';
  static const noteCache = 'Đang dùng bản đã lưu từ lần trước, nghe được cả khi không có mạng.';
  static const libraryEmpty = 'Thư viện chưa có sách.';
  static const libraryNote = 'Sách mẫu để thử cách nghe sách. Kho sách thật sẽ tải từ máy chủ của nhóm.';
  static const prevPage = 'Trang trước';
  static const nextPage = 'Trang sau';
  static const readPage = 'Đọc trang';
  static const firstPage = 'Đây là trang đầu.';
  static const lastPage = 'Đây là trang cuối.';

  // Cài đặt (dùng bằng chạm nghe, chạm hai lần)
  static const settingsOpen = 'Cài đặt. Có năm mục. Nút Quay lại ở mép dưới.';
  static const speechRate = 'Tốc độ đọc';
  static const sound = 'Âm báo';
  static const vibrate = 'Rung';
  static const on = 'Bật';
  static const off = 'Tắt';
  static const pickImage = 'Đọc ảnh có sẵn';
  static const pickImageSub = 'Chọn ảnh trong máy';
  static const advanced = 'Cho người hỗ trợ';
  static const advancedSub = 'Máy chủ, chế độ demo';
  static const changeHint = 'Chạm hai lần để đổi.';
  static const openHint = 'Chạm hai lần để mở.';
  static const tryVoiceSentence = 'Đây là tốc độ đọc hiện tại.';

  // Cài đặt cho người hỗ trợ (màn hình biểu mẫu thường, dùng với TalkBack hoặc người nhìn)
  static const advancedTitle = 'Cài đặt cho người hỗ trợ';
  static const advancedOpen = 'Cài đặt cho người hỗ trợ. Nút Quay lại ở mép dưới.';
  static const serverUrl = 'Địa chỉ máy chủ';
  static const serverUrlHint =
      'Máy ảo dùng http://10.0.2.2:8000. Điện thoại thật dùng địa chỉ IP của laptop, '
      'ví dụ http://192.168.1.15:8000';
  static const checkServer = 'Kiểm tra kết nối';
  static const serverOkPrefix = 'Đã kết nối máy chủ.';
  static const serverModeMock = 'Máy chủ đang ở chế độ thử, câu trả lời chưa phải từ mô hình thật.';
  static const serverAiModule = 'Máy chủ đang dùng mô hình thật của nhóm.';
  static const serverUnreachableStart = 'Chưa kết nối được máy chủ, nên chưa chụp và đọc trang được. '
      'Thư viện đã lưu vẫn nghe được. Người hỗ trợ có thể kiểm tra trong Cài đặt.';
  static const serverMockStart = 'Lưu ý: máy chủ đang chạy dữ liệu thử, câu trả lời chưa phải từ mô hình thật.';
  static const speechRateFine = 'Tốc độ đọc chỉnh tinh';
  static const tryVoice = 'Nghe thử';
  static const pageType = 'Loại trang';
  static const demoMode = 'Chế độ demo';
  static const demoModeHint = 'Không cần máy chủ, trả lời mẫu để thử giao diện';
  static const demoDescription =
      'Đây là chế độ demo, ảnh không được gửi đi đâu. Trang có một đoạn văn về cây xanh '
      'và một hình vẽ cái cây có rễ, thân và lá. Rễ nằm dưới đất, thân ở giữa, lá ở trên cùng.';
  static const openTtsSettings = 'Mở cài đặt giọng đọc';
  static const replayTutorial = 'Nghe lại hướng dẫn';
  static const saved = 'Đã lưu.';

  /// Tên loại hình để hiện cạnh kết quả: `image_type` của hợp đồng v0.1 hoặc `page_type` của API v1.
  /// Loại không rõ (`other`, `unknown`, `auto`) thì không hiện.
  static String? kindName(String code) => const {
    'bar_chart': 'Biểu đồ cột',
    'line_chart': 'Biểu đồ đường',
    'pie_chart': 'Biểu đồ tròn',
    'flow_diagram': 'Sơ đồ',
    'cycle_diagram': 'Sơ đồ vòng',
    'geometry': 'Hình học',
    'text': 'Đoạn văn',
    'map': 'Bản đồ',
    'chart': 'Biểu đồ',
    'table': 'Bảng',
    'figure': 'Hình vẽ',
    'mixed': 'Chữ và hình',
  }[code];

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
