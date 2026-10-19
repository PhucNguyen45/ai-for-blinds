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
