import 'dart:async';
import 'package:flutter/foundation.dart';

import '../api/api_client.dart';
import '../api/models.dart';
import '../services/earcons.dart';
import '../services/speech.dart';
import '../strings.dart';

enum ReaderStatus { idle, sending, speaking, error }

/// Luồng chính của app: chụp → gửi → nghe.
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

  /// Lấy API theo cài đặt hiện tại (máy chủ thật hoặc demo) ở mỗi lần gọi.
  final SgbeApi Function() api;
  final String Function() _pageType;
  final Speaker speaker;
  final EarconPlayer earcons;
  final Duration waitingInterval;
  final Duration stillWorkingAfter;

  ReaderStatus _status = ReaderStatus.idle;
  ReaderStatus get status => _status;

  DescribeResult? _last;
  DescribeResult? get last => _last;

  /// Chữ hiện trên màn hình: mô tả gần nhất hoặc câu báo lỗi.
  String _shownText = '';
  String get shownText => _shownText;

  int _speechToken = 0;

  bool get busy => _status == ReaderStatus.sending;

  /// Hành động chính khi chạm màn hình hoặc bấm nút âm lượng:
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
    await earcons.play(Earcon.shutter);
    _setStatus(ReaderStatus.sending);
    unawaited(_say(S.working, finishStatus: null));

    final ticker = Timer.periodic(waitingInterval, (_) => earcons.play(Earcon.waiting));
    final reminder = Timer(stillWorkingAfter, () {
      if (busy) unawaited(_say(S.stillWorking, finishStatus: null));
    });
    final ApiResult<DescribeResult> result;
    try {
      result = await api().describe(image, pageType: _pageType());
    } finally {
      ticker.cancel();
      reminder.cancel();
    }

    switch (result) {
      case ApiOk(:final value):
        _last = value;
        final spoken = value.unreadable ? '${value.description} ${S.unreadableHint}' : value.description;
        _shownText = spoken;
        await earcons.play(Earcon.done);
        _setStatus(ReaderStatus.speaking);
        await _say(spoken, finishStatus: ReaderStatus.idle);
      case ApiFail(:final message):
        await fail(message);
    }
  }

  /// Đọc lại mô tả gần nhất.
  Future<void> repeat() async {
    final last = _last;
    if (last == null) {
      await speaker.speak(S.nothingToRepeat);
      return;
    }
    _setStatus(ReaderStatus.speaking);
    await _say(_shownText.isEmpty ? last.description : _shownText, finishStatus: ReaderStatus.idle);
  }

  /// Báo lỗi bằng âm báo và giọng nói (không dùng SnackBar: người dùng không nhìn thấy).
  Future<void> fail(String message) async {
    _shownText = message;
    await earcons.play(Earcon.error);
    _setStatus(ReaderStatus.error);
    await _say(message, finishStatus: ReaderStatus.error);
  }

  /// Nói một câu ngắn không đổi trạng thái (lời chào, xác nhận).
  Future<void> announce(String text) => speaker.speak(text);

  Future<void> stopSpeaking() async {
    _speechToken++;
    await speaker.stop();
    if (_status == ReaderStatus.speaking) _setStatus(ReaderStatus.idle);
  }

  Future<void> _say(String text, {required ReaderStatus? finishStatus}) async {
    final token = ++_speechToken;
    await speaker.speak(text);
    // Nếu trong lúc nói đã có câu khác chen vào hoặc người dùng dừng, giữ nguyên trạng thái.
    if (finishStatus != null && token == _speechToken && _status != ReaderStatus.sending) {
      _setStatus(finishStatus);
    }
  }

  void _setStatus(ReaderStatus s) {
    if (_status == s) return;
    _status = s;
    notifyListeners();
  }
}
