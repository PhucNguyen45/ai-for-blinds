import 'package:flutter/foundation.dart';
import 'package:flutter_tts/flutter_tts.dart';

/// Giọng đọc của app. Tách giao diện ra để test không cần điện thoại.
abstract class Speaker {
  /// Trả về `true` nếu máy có giọng tiếng Việt.
  Future<bool> init({required double rate});
  Future<void> speak(String text);
  Future<void> speakEnglish(String text);
  Future<void> stop();
  Future<void> setRate(double rate);
}

/// Dùng engine chuyển văn bản thành giọng nói của Android (thường là Google TTS).
///
/// App tự đọc bằng TTS thay vì nhờ TalkBack, để người không bật TalkBack cũng
/// nghe được. Vì vậy chữ trạng thái trên màn hình KHÔNG đặt liveRegion, tránh
/// hai giọng đọc chồng nhau khi TalkBack đang bật.
class TtsSpeaker implements Speaker {
  final FlutterTts _tts = FlutterTts();
  static const vi = 'vi-VN';

  @override
  Future<bool> init({required double rate}) async {
    await _tts.awaitSpeakCompletion(true);
    final available = await _tts.isLanguageAvailable(vi);
    final ok = available == true || available == 1;
    if (ok) await _tts.setLanguage(vi);
    await _tts.setSpeechRate(rate);
    return ok;
  }

  @override
  Future<void> speak(String text) async {
    await _tts.stop();
    await _tts.setLanguage(vi);
    await _tts.speak(text);
  }

  @override
  Future<void> speakEnglish(String text) async {
    await _tts.stop();
    await _tts.setLanguage('en-US');
    await _tts.speak(text);
  }

  @override
  Future<void> stop() => _tts.stop();

  @override
  Future<void> setRate(double rate) => _tts.setSpeechRate(rate);
}

/// Câu app đang nói, để hiện thành phụ đề trên màn hình.
@immutable
class Caption {
  const Caption(this.text, {required this.speaking});
  static const empty = Caption('', speaking: false);

  final String text;

  /// `false` khi câu đã nói xong hoặc bị dừng: phụ đề vẫn hiện nhưng mờ đi.
  final bool speaking;
}

/// Bọc một [Speaker] để mọi câu nói đều hiện lên phụ đề (người nhìn kém,
/// giáo viên đứng cạnh, hội đồng xem demo đều đọc được app đang nói gì).
class CaptionedSpeaker implements Speaker {
  CaptionedSpeaker(this.inner);

  final Speaker inner;
  final ValueNotifier<Caption> caption = ValueNotifier(Caption.empty);
  int _token = 0;

  @override
  Future<bool> init({required double rate}) => inner.init(rate: rate);

  @override
  Future<void> speak(String text) => _run(text, () => inner.speak(text));

  @override
  Future<void> speakEnglish(String text) => _run(text, () => inner.speakEnglish(text));

  Future<void> _run(String text, Future<void> Function() say) async {
    final token = ++_token;
    caption.value = Caption(text, speaking: true);
    try {
      await say();
    } finally {
      if (token == _token) caption.value = Caption(text, speaking: false);
    }
  }

  @override
  Future<void> stop() async {
    _token++;
    final c = caption.value;
    if (c.speaking) caption.value = Caption(c.text, speaking: false);
    await inner.stop();
  }

  @override
  Future<void> setRate(double rate) => inner.setRate(rate);
}
