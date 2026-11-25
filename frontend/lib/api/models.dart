/// Kiểu dữ liệu app dùng: theo hợp đồng AI v0.1 của Phúc (ai/contract), đọc được cả API v1 của Nam.
library;

/// Kết quả một lần gọi API: thành công hoặc thất bại, không ném ngoại lệ.
sealed class ApiResult<T> {
  const ApiResult();
}

class ApiOk<T> extends ApiResult<T> {
  const ApiOk(this.value);
  final T value;
}

class ApiFail<T> extends ApiResult<T> {
  const ApiFail(this.code, this.message);

  /// Mã lỗi của máy chủ (`VLM_TIMEOUT`, `IMAGE_NOT_FOUND`, ...) hoặc mã phía app
  /// (`NETWORK`, `TIMEOUT`, `BAD_RESPONSE`).
  final String code;

  /// Câu tiếng Việt đọc thẳng cho người dùng.
  final String message;
}

/// Kết quả mô tả một ảnh.
///
/// Đọc được hai dạng:
/// - hợp đồng AI v0.1 của Phúc (`ai/contract/` trên nhánh `phuc`): `status`, `summary_vi`,
///   `interpretation_vi`, `image_type`, `uncertainties`, `question_answering_ready`, `meta`;
/// - API v1 của Nam (`docs/API_v1.md` trên nhánh `dev`): `description`, `unreadable`, `page_type`.
/// Nhóm đã chọn theo hợp đồng của Phúc; dạng API v1 giữ lại để app vẫn chạy với backend hiện có.
class DescribeResult {
  const DescribeResult({
    required this.imageId,
    required this.description,
    required this.pageType,
    required this.unreadable,
    required this.model,
    required this.promptVersion,
    required this.latencyMs,
    required this.cached,
    this.status = 'ok',
    this.summary = '',
    this.uncertainties = const [],
    this.canAsk = true,
  });

  factory DescribeResult.fromJson(Map<String, dynamic> j) {
    String str(String key) => ((j[key] as String?) ?? '').trim();
    final meta = j['meta'] is Map<String, dynamic> ? j['meta'] as Map<String, dynamic> : const <String, dynamic>{};

    final status = j['status'] as String?; // chỉ có ở hợp đồng v0.1
    final summary = str('summary_vi');
    final interpretation = str('interpretation_vi');
    final description = str('description');
    // v0.1: unreadable/unsupported chỉ có summary_vi giải thích lý do.
    // partial = lời diễn giải bị CẮT NGẮN do giới hạn độ dài (không phải ảnh hỏng), xem `truncated`.
    final unreadable = (j['unreadable'] as bool?) ?? (status == 'unreadable' || status == 'unsupported');
    final text = interpretation.isNotEmpty ? interpretation : (description.isNotEmpty ? description : summary);
    final latencySeconds = meta['latency_seconds'] as num?;

    return DescribeResult(
      imageId: (j['image_id'] as String?) ?? '',
      description: text,
      pageType: (j['page_type'] as String?) ?? (j['image_type'] as String?) ?? 'auto',
      unreadable: unreadable,
      model: (j['model'] as String?) ?? (meta['model'] as String?) ?? '',
      promptVersion: (j['prompt_version'] as String?) ?? (meta['prompt_id'] as String?) ?? '',
      latencyMs: (j['latency_ms'] as num?)?.toInt() ?? ((latencySeconds ?? 0) * 1000).round(),
      cached: (j['cached'] as bool?) ?? false,
      status: status ?? (unreadable ? 'unreadable' : 'ok'),
      summary: summary,
      uncertainties: [for (final u in (j['uncertainties'] as List?) ?? const []) u.toString()],
      // Hỏi tiếp được khi đã có lời mô tả (ok/partial): /v1/ask gửi lại chính ảnh cho mô hình.
      // KHÔNG dựa vào `question_answering_ready`: hợp đồng v0.1 dành cờ đó cho B1 (facts có cấu trúc),
      // phương pháp B0 hiện tại luôn để false (ai/contract/README.md, "Hạn chế hiện tại").
      canAsk: !unreadable && status != 'error',
    );
  }

  final String imageId;
  final String description;
  final String pageType;
  final bool unreadable;
  final String model;
  final String promptVersion;
  final int latencyMs;
  final bool cached;

  /// `ok`, `partial`, `unreadable`, `unsupported` (hợp đồng v0.1).
  final String status;

  /// Tóm tắt ngắn (v0.1); rỗng với API v1.
  final String summary;

  /// Những điều mô hình chưa chắc chắn (v0.1).
  final List<String> uncertainties;

  /// Có đủ căn cứ để hỏi tiếp trên ảnh này không.
  final bool canAsk;

  /// Lời diễn giải bị cắt ngắn do giới hạn độ dài (hợp đồng v0.1 `status="partial"`).
  bool get truncated => status == 'partial';

  /// Ảnh hỏng hẳn (không đọc được / không hỗ trợ): mô tả là câu giải thích lý do.
  bool get wholeUnreadable => status == 'unreadable' || status == 'unsupported';
}

class AskTurn {
  const AskTurn(this.question, this.answer);
  final String question;
  final String answer;

  Map<String, String> toJson() => {'question': question, 'answer': answer};
}

class AskResult {
  const AskResult({required this.imageId, required this.answer, required this.latencyMs});

  /// API v1: `answer`; hợp đồng v0.1 (AnswerResult của Phúc): `answer_vi`.
  factory AskResult.fromJson(Map<String, dynamic> j) {
    final meta = j['meta'] is Map<String, dynamic> ? j['meta'] as Map<String, dynamic> : const <String, dynamic>{};
    return AskResult(
      imageId: (j['image_id'] as String?) ?? '',
      answer: ((j['answer'] ?? j['answer_vi']) as String?)?.trim() ?? '',
      latencyMs:
          (j['latency_ms'] as num?)?.toInt() ?? (((meta['latency_seconds'] as num?) ?? 0) * 1000).round(),
    );
  }

  final String imageId;
  final String answer;
  final int latencyMs;
}

class HealthInfo {
  const HealthInfo({
    required this.status,
    required this.vlmMode,
    required this.model,
    required this.sttMode,
    this.aiModule = false,
  });

  factory HealthInfo.fromJson(Map<String, dynamic> j) => HealthInfo(
    status: (j['status'] as String?) ?? '',
    vlmMode: (j['vlm_mode'] as String?) ?? '',
    model: (j['model'] as String?) ?? '',
    sttMode: (j['stt_mode'] as String?) ?? '',
    aiModule: (j['ai_module'] as bool?) ?? false,
  );

  final String status;
  final String vlmMode;
  final String model;
  final String sttMode;

  /// Máy chủ đang gọi module AI của nhóm (ai/pipeline.py), không phải dữ liệu thử.
  final bool aiModule;

  bool get isMock => vlmMode == 'mock';
}

/// Một cuốn trong kho mô tả SGK của máy chủ (`GET /v1/library`).
class LibraryBookInfo {
  const LibraryBookInfo({required this.book, required this.title, required this.pageCount});

  factory LibraryBookInfo.fromJson(Map<String, dynamic> j) => LibraryBookInfo(
    book: j['book'] as String,
    title: (j['title'] as String?) ?? j['book'] as String,
    pageCount: (j['page_count'] as num?)?.toInt() ?? 0,
  );

  final String book;
  final String title;
  final int pageCount;
}

/// Một trang đã số hóa (`GET /v1/library/{book}/pages`, `PageRecord` của API v1).
class LibraryPage {
  const LibraryPage({
    required this.page,
    required this.pageType,
    required this.description,
    required this.reviewed,
    this.title,
  });

  factory LibraryPage.fromJson(Map<String, dynamic> j) => LibraryPage(
    page: (j['page'] as num).toInt(),
    pageType: (j['page_type'] as String?) ?? 'mixed',
    description: ((j['description'] as String?) ?? '').trim(),
    reviewed: (j['reviewed'] as bool?) ?? false,
    title: (j['title'] as String?)?.trim(),
  );

  final int page;
  final String pageType;
  final String description;

  /// Đã có người kiểm tra lời mô tả chưa.
  final bool reviewed;
  final String? title;
}

class LibraryBookPages {
  const LibraryBookPages({required this.book, required this.title, required this.pages});

  factory LibraryBookPages.fromJson(Map<String, dynamic> j) => LibraryBookPages(
    book: j['book'] as String,
    title: (j['title'] as String?) ?? j['book'] as String,
    pages: [for (final p in (j['pages'] as List? ?? const [])) LibraryPage.fromJson(p as Map<String, dynamic>)],
  );

  final String book;
  final String title;
  final List<LibraryPage> pages;
}
