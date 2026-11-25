import 'dart:async';
import 'package:flutter/foundation.dart';

import '../api/api_client.dart';
import '../api/models.dart';
import '../services/earcons.dart';
import '../services/speech.dart';
import '../strings.dart';

enum ReaderStatus { idle, sending, speaking, error }

/// Tách đoạn văn thành câu để đọc từng câu và tô vàng câu đang đọc.
List<String> splitSentences(String text) => [
  for (final s in text.trim().split(RegExp(r'(?<=[.!?…])\s+|\n+')))
    if (s.trim().isNotEmpty) s.trim(),
];

/// Luồng chính của app: chụp → gửi → nghe, rồi hỏi tiếp trên cùng trang.
///
/// Không phụ thuộc Flutter UI hay camera, nên test được bằng đồ giả.
class ReaderController extends ChangeNotifier {
  ReaderController({
    required this.api,
    required this.speaker,
    required this.earcons,
    String Function()? pageType,
    this.waitingInterval = const Duration(seconds: 3),
    this.stillWorkingAfter = const Duration(seconds: 20),
  }) : _pageType = pageType ?? (() => 'auto');

  /// Mã nội dung đang đọc, để màn hình biết tô vàng câu ở đâu.
  static const pageId = 'page';
  static const answerId = 'answer';

  /// Lấy API theo cài đặt hiện tại (máy chủ thật hoặc demo) ở mỗi lần gọi.
  final SgbeApi Function() api;
  final String Function() _pageType;
  final Speaker speaker;
  final EarconPlayer earcons;
  final Duration waitingInterval;
  final Duration stillWorkingAfter;

  ReaderStatus _status = ReaderStatus.idle;
  ReaderStatus get status => _status;
  bool get busy => _status == ReaderStatus.sending;

  DescribeResult? _last;

  /// Kết quả mô tả gần nhất (giữ `image_id` để hỏi tiếp).
  DescribeResult? get last => _last;

  Uint8List? _lastImage;

  /// Ảnh vừa chụp, để hiện ảnh tĩnh lúc chờ và ảnh nhỏ cạnh kết quả.
  Uint8List? get lastImage => _lastImage;

  String _pageText = '';
  List<String> _pageSentences = const [];

  /// Câu mô tả trang gần nhất (đã kèm gợi ý chụp lại nếu có).
  List<String> get pageSentences => _pageSentences;

  String _errorText = '';
  String _errorScope = pageId;

  /// Câu báo lỗi gần nhất và nơi lỗi xảy ra ([pageId] hoặc [answerId]).
  String get errorText => _errorText;
  String get errorScope => _errorScope;

  /// Chữ hiện trên màn hình: lỗi nếu đang lỗi, nếu không thì mô tả gần nhất.
  String get shownText => _status == ReaderStatus.error ? _errorText : _pageText;

  String? _readingId;
  int _sentenceIndex = -1;

  /// Nội dung đang đọc và câu đang đọc (-1 khi không đọc).
  String? get readingId => _readingId;
  int get sentenceIndex => _sentenceIndex;

  final List<AskTurn> _turns = [];
  List<AskTurn> get turns => List.unmodifiable(_turns);

  String? _pendingQuestion;

  /// Câu hỏi đang chờ máy chủ trả lời.
  String? get pendingQuestion => _pendingQuestion;

  int _speechToken = 0;

  /// Hành động chính khi chạm hai lần vào vùng chụp hoặc bấm nút âm lượng:
  /// đang nói thì dừng, đang gửi thì báo chờ, còn lại thì chụp.
  /// Trả về `true` nếu nên chụp ảnh mới.
  Future<bool> primaryAction() async {
    switch (_status) {
      case ReaderStatus.speaking:
        await stopSpeaking();
        return false;
      case ReaderStatus.sending:
        await speaker.speak(S.working);
        return false;
      case ReaderStatus.idle:
      case ReaderStatus.error:
        return true;
    }
  }

  /// Gửi ảnh đã chụp và đọc kết quả.
  Future<void> describe(Uint8List image) async {
    if (busy) return;
    _lastImage = image;
    _turns.clear();
    _stopReadingState();
    await earcons.play(Earcon.shutter);
    _setStatus(ReaderStatus.sending, force: true);
    unawaited(_sayPlain(S.working));

    final result = await _waiting(() => api().describe(image, pageType: _pageType()));
    switch (result) {
      case ApiOk(:final value):
        _last = value;
        _pageText = _spokenFor(value);
        _pageSentences = splitSentences(_pageText);
        await earcons.play(Earcon.done);
        await readText(_pageText, id: pageId);
      case ApiFail(:final message):
        await fail(message);
    }
  }

  /// Câu đọc cho một kết quả mô tả:
  /// - bị cắt ngắn (`partial`): đọc phần có được, gợi ý hỏi thêm;
  /// - ảnh hỏng hẳn: mô tả là câu giải thích; thêm hướng dẫn chụp lại, trừ khi câu đó đã hướng dẫn
  ///   (cổng chất lượng ảnh của module AI đã viết sẵn "… rồi chụp lại nhé");
  /// - có chỗ không đọc được (API v1 `unreadable=true`): báo có chỗ chưa đọc được.
  static String _spokenFor(DescribeResult value) {
    final text = value.description;
    if (value.truncated) return '$text ${S.truncatedHint}';
    if (!value.unreadable) return text;
    if (value.wholeUnreadable) return text.contains('chụp lại') ? text : '$text ${S.retakeHint}';
    return '$text ${S.unreadableHint}';
  }

  /// Hỏi tiếp về trang vừa chụp, gửi kèm các lượt hỏi trước (hợp đồng API v1 `/v1/ask`).
  Future<void> ask(String question) async {
    final last = _last;
    if (last == null) return warn(S.askNeedPage);
    if (!last.canAsk) return warn(S.askCannot);
    if (busy) return announce(S.working);

    _pendingQuestion = question;
    _stopReadingState();
    _setStatus(ReaderStatus.sending, force: true);
    unawaited(_sayPlain(S.asking));

    final result = await _waiting(() => api().ask(last.imageId, question, history: List.of(_turns)));
    _pendingQuestion = null;
    switch (result) {
      case ApiOk(:final value):
        _turns.add(AskTurn(question, value.answer));
        await earcons.play(Earcon.done);
        await readText(value.answer, id: answerId);
      case ApiFail(:final message):
        await fail(message, scope: answerId);
    }
  }

  /// Đọc một đoạn theo từng câu; màn hình tô vàng câu [sentenceIndex].
  /// Chạm bất kỳ (hoặc câu nói khác chen vào) thì dừng ngay.
  /// [intro] (vd "Trang 42.") được đọc trước, không tô vàng.
  Future<void> readText(String text, {required String id, String? intro}) async {
    final token = ++_speechToken;
    final sentences = splitSentences(text);
    _readingId = id;
    _sentenceIndex = intro == null ? 0 : -1;
    _setStatus(ReaderStatus.speaking, force: true);
    if (intro != null) {
      await speaker.speak(intro);
      if (token != _speechToken) return;
    }
    for (var i = 0; i < sentences.length; i++) {
      if (token != _speechToken) return;
      _sentenceIndex = i;
      notifyListeners();
      await speaker.speak(sentences[i]);
    }
    if (token != _speechToken) return;
    _sentenceIndex = -1;
    _setStatus(ReaderStatus.idle, force: true);
  }

  /// Đọc lại mô tả gần nhất.
  Future<void> repeat() async {
    if (_last == null) return warn(S.nothingToRepeat);
    await readText(_pageText, id: pageId);
  }

  /// Đọc lại câu trả lời gần nhất.
  Future<void> repeatAnswer() async {
    if (_turns.isEmpty) return announce(S.askEmpty);
    await readText(_turns.last.answer, id: answerId);
  }

  /// Báo lỗi bằng âm báo và giọng nói (không dùng SnackBar: người dùng không nhìn thấy).
  Future<void> fail(String message, {String scope = pageId}) async {
    _errorText = message;
    _errorScope = scope;
    _stopReadingState();
    await earcons.play(Earcon.error);
    _setStatus(ReaderStatus.error, force: true);
    await _sayPlain(message);
  }

  /// Nhắc người dùng làm bước trước (âm lỗi + giọng nói), không đổi màn hình.
  Future<void> warn(String message) async {
    _interrupt();
    await earcons.play(Earcon.error);
    await speaker.speak(message);
  }

  /// Nói một câu ngắn (tên nút, xác nhận). Đang đọc thì dừng đọc trước.
  Future<void> announce(String text) async {
    _interrupt();
    await speaker.speak(text);
  }

  Future<void> stopSpeaking() async {
    _interrupt();
    await speaker.stop();
  }

  /// Quay về trạng thái sẵn sàng sau khi người dùng đã nghe lỗi.
  void clearError() {
    if (_status == ReaderStatus.error) _setStatus(ReaderStatus.idle);
  }

  Future<ApiResult<T>> _waiting<T>(Future<ApiResult<T>> Function() call) async {
    final ticker = Timer.periodic(waitingInterval, (_) => earcons.play(Earcon.waiting));
    final reminder = Timer(stillWorkingAfter, () {
      if (busy) unawaited(_sayPlain(S.stillWorking));
    });
    try {
      return await call();
    } finally {
      ticker.cancel();
      reminder.cancel();
    }
  }

  void _interrupt() {
    _speechToken++;
    final wasReading = _sentenceIndex >= 0;
    _sentenceIndex = -1;
    if (_status == ReaderStatus.speaking) {
      _setStatus(ReaderStatus.idle);
    } else if (wasReading) {
      notifyListeners();
    }
  }

  void _stopReadingState() {
    _speechToken++;
    _sentenceIndex = -1;
  }

  Future<void> _sayPlain(String text) => speaker.speak(text);

  void _setStatus(ReaderStatus s, {bool force = false}) {
    if (_status == s && !force) return;
    _status = s;
    notifyListeners();
  }
}
