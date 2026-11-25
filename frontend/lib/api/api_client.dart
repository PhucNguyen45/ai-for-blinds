import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';

import 'package:http/http.dart' as http;

import '../strings.dart';
import 'models.dart';

/// Những gì app cần từ máy chủ. Có hai bản: [ApiClient] gọi máy chủ thật,
/// `DemoApi` trả lời mẫu khi bật chế độ demo.
abstract class SgbeApi {
  Future<ApiResult<DescribeResult>> describe(Uint8List image, {String pageType = 'auto'});
  Future<ApiResult<AskResult>> ask(String imageId, String question, {List<AskTurn> history = const []});
  Future<ApiResult<HealthInfo>> health();

  /// Danh sách sách đã số hóa trên máy chủ.
  Future<ApiResult<List<LibraryBookInfo>>> library();

  /// Các trang của một cuốn.
  Future<ApiResult<LibraryBookPages>> bookPages(String book);
}

/// Gọi máy chủ theo hợp đồng API v1.
///
/// Mọi phản hồi có dạng `{"data": ..., "error": null | {"code", "message"}}`.
/// Lỗi của máy chủ đã có câu tiếng Việt sẵn trong `error.message`; app đọc thẳng.
/// Lỗi trước khi tới máy chủ (mất mạng, quá giờ) dùng câu trong [S].
class ApiClient implements SgbeApi {
  ApiClient(
    String baseUrl, {
    http.Client? client,
    this.slowTimeout = const Duration(seconds: 130),
    this.fastTimeout = const Duration(seconds: 8),
    this.libraryTimeout = const Duration(seconds: 20),
  }) : baseUrl = normalizeBaseUrl(baseUrl),
       _client = client ?? http.Client();

  final String baseUrl;
  final http.Client _client;

  /// Cho `/v1/describe` và `/v1/ask`: máy chủ chờ mô hình tối đa 120 giây,
  /// app chờ thêm 10 giây (theo hợp đồng API v1).
  final Duration slowTimeout;

  /// Cho `/health`.
  final Duration fastTimeout;

  /// Cho `/v1/library` (đọc file trên máy chủ, không gọi mô hình).
  final Duration libraryTimeout;

  static String normalizeBaseUrl(String raw) {
    var url = raw.trim();
    if (url.isEmpty) return url;
    if (!url.startsWith('http://') && !url.startsWith('https://')) url = 'http://$url';
    while (url.endsWith('/')) {
      url = url.substring(0, url.length - 1);
    }
    return url;
  }

  @override
  Future<ApiResult<DescribeResult>> describe(Uint8List image, {String pageType = 'auto'}) {
    final req = http.MultipartRequest('POST', Uri.parse('$baseUrl/v1/describe'))
      ..fields['page_type'] = pageType
      ..files.add(http.MultipartFile.fromBytes('image', image, filename: 'trang.jpg'));
    return _run(
      () => _client.send(req).then(http.Response.fromStream),
      slowTimeout,
      (data) => DescribeResult.fromJson(data as Map<String, dynamic>),
    );
  }

  @override
  Future<ApiResult<AskResult>> ask(String imageId, String question, {List<AskTurn> history = const []}) {
    final body = jsonEncode({
      'image_id': imageId,
      'question': question,
      'history': [for (final t in history) t.toJson()],
    });
    return _run(
      () => _client.post(
        Uri.parse('$baseUrl/v1/ask'),
        headers: {'Content-Type': 'application/json; charset=utf-8'},
        body: body,
      ),
      slowTimeout,
      (data) => AskResult.fromJson(data as Map<String, dynamic>),
    );
  }

  @override
  Future<ApiResult<HealthInfo>> health() => _run(
    () => _client.get(Uri.parse('$baseUrl/health')),
    fastTimeout,
    (data) => HealthInfo.fromJson(data as Map<String, dynamic>),
  );

  @override
  Future<ApiResult<List<LibraryBookInfo>>> library() => _run(
    () => _client.get(Uri.parse('$baseUrl/v1/library')),
    libraryTimeout,
    (data) => [for (final b in data as List) LibraryBookInfo.fromJson(b as Map<String, dynamic>)],
  );

  @override
  Future<ApiResult<LibraryBookPages>> bookPages(String book) => _run(
    () => _client.get(Uri.parse('$baseUrl/v1/library/${Uri.encodeComponent(book)}/pages')),
    libraryTimeout,
    (data) => LibraryBookPages.fromJson(data as Map<String, dynamic>),
  );

  Future<ApiResult<T>> _run<T>(
    Future<http.Response> Function() call,
    Duration timeout,
    T Function(Object? data) parse,
  ) async {
    if (baseUrl.isEmpty) return const ApiFail('NETWORK', S.errOffline);
    final http.Response res;
    try {
      res = await call().timeout(timeout);
    } on TimeoutException {
      return const ApiFail('TIMEOUT', S.errTimeout);
    } on SocketException {
      return const ApiFail('NETWORK', S.errOffline);
    } on http.ClientException {
      return const ApiFail('NETWORK', S.errOffline);
    } on FormatException {
      return const ApiFail('NETWORK', S.errOffline);
    }
    return parseEnvelope(res.bodyBytes, parse);
  }

  /// Tách phản hồi. Nhận hai dạng:
  /// - có vỏ `{data, error}` (API v1);
  /// - kết quả gốc theo hợp đồng AI v0.1 của Phúc (không có vỏ, lỗi nằm ở `status="error"` + `error`).
  /// Tách riêng để test bằng phản hồi thật đã lưu.
  static ApiResult<T> parseEnvelope<T>(List<int> bodyBytes, T Function(Object? data) parse) {
    try {
      final json = jsonDecode(utf8.decode(bodyBytes));
      if (json is! Map<String, dynamic>) return const ApiFail('BAD_RESPONSE', S.errBadData);
      final failure = _failureOf(json);
      if (failure != null) return ApiFail(failure.$1, failure.$2);

      final raw = !json.containsKey('data') && (json.containsKey('schema_version') || json.containsKey('status'));
      final data = raw ? json : json['data'];
      if (data is Map<String, dynamic>) {
        final inner = _failureOf(data);
        if (inner != null) return ApiFail(inner.$1, inner.$2);
      }
      return ApiOk(parse(data));
    } on FormatException {
      return const ApiFail('BAD_RESPONSE', S.errBadData);
    } on TypeError {
      return const ApiFail('BAD_RESPONSE', S.errBadData);
    }
  }

  /// (mã lỗi, câu báo) nếu đối tượng mang lỗi, ngược lại null.
  static (String, String)? _failureOf(Map<String, dynamic> obj) {
    final error = obj['error'];
    if (error is! Map<String, dynamic>) return null;
    final message = error['message'];
    return (
      (error['code'] as String?) ?? 'UNKNOWN',
      message is String && message.trim().isNotEmpty ? message : S.errBadData,
    );
  }
}
