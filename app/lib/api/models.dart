/// Kiểu dữ liệu theo hợp đồng API v1 (docs/API_v1.md).
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
  });

  factory DescribeResult.fromJson(Map<String, dynamic> j) => DescribeResult(
        imageId: j['image_id'] as String,
        description: j['description'] as String,
        pageType: (j['page_type'] as String?) ?? 'auto',
        unreadable: (j['unreadable'] as bool?) ?? false,
        model: (j['model'] as String?) ?? '',
        promptVersion: (j['prompt_version'] as String?) ?? '',
        latencyMs: (j['latency_ms'] as num?)?.toInt() ?? 0,
        cached: (j['cached'] as bool?) ?? false,
      );

  final String imageId;
  final String description;
  final String pageType;
  final bool unreadable;
  final String model;
  final String promptVersion;
  final int latencyMs;
  final bool cached;
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
