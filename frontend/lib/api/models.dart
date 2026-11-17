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
    // v0.1: unreadable/unsupported chỉ có summary_vi giải thích lý do; partial = ảnh bị cắt một phần.
    final unreadable = (j['unreadable'] as bool?) ??
        (status == 'unreadable' || status == 'unsupported' || status == 'partial');
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
      // API v1 không có trường này: mọi ảnh đã mô tả đều hỏi tiếp được.
      canAsk: (j['question_answering_ready'] as bool?) ?? (status == null || status == 'ok' || status == 'partial'),
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
}

class AskTurn {
  const AskTurn(this.question, this.answer);
  final String question;
  final String answer;

  Map<String, String> toJson() => {'question': question, 'answer': answer};
}

class AskResult {
  const AskResult({required this.imageId, required this.answer, required this.latencyMs});

  factory AskResult.fromJson(Map<String, dynamic> j) => AskResult(
        imageId: j['image_id'] as String,
        answer: j['answer'] as String,
        latencyMs: (j['latency_ms'] as num?)?.toInt() ?? 0,
      );

  final String imageId;
  final String answer;
  final int latencyMs;
}

class HealthInfo {
  const HealthInfo({required this.status, required this.vlmMode, required this.model, required this.sttMode});

  factory HealthInfo.fromJson(Map<String, dynamic> j) => HealthInfo(
        status: (j['status'] as String?) ?? '',
        vlmMode: (j['vlm_mode'] as String?) ?? '',
        model: (j['model'] as String?) ?? '',
        sttMode: (j['stt_mode'] as String?) ?? '',
      );

  final String status;
  final String vlmMode;
  final String model;
  final String sttMode;

  bool get isMock => vlmMode == 'mock';
}
