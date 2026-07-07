import 'dart:async';
import 'package:flutter/foundation.dart';
import 'package:speech_to_text/speech_to_text.dart' as stt;

class VoiceCommandService extends ChangeNotifier {
  final stt.SpeechToText _speech = stt.SpeechToText();
  bool _isListening = false;
  bool _isAvailable = false;
  String lastCommand = '';
  String lastHypothesis = '';

  // ---------------------------------------------------------------------------
  // Getters
  // ---------------------------------------------------------------------------

  bool get isListening => _isListening;
  bool get isAvailable => _isAvailable;

  // ---------------------------------------------------------------------------
  // Initialization
  // ---------------------------------------------------------------------------

  Future<void> init() async {
    try {
      final available = await _speech.initialize(
        onStatus: _onStatus,
        onError: _onError,
      );
      _isAvailable = available;
    } catch (e) {
      debugPrint('VoiceCommandService.init error: $e');
      _isAvailable = false;
    }
    notifyListeners();
  }

  // ---------------------------------------------------------------------------
  // Start / Stop listening
  // ---------------------------------------------------------------------------

  Future<void> startListening() async {
    if (!_isAvailable) {
      debugPrint('VoiceCommandService: speech recognition not available');
      return;
    }

    // If already listening, stop first to avoid overlapping sessions.
    if (_isListening) {
      await stopListening();
    }

    final started = await _speech.listen(
      localeId: 'vi_VN',
      listenFor: const Duration(seconds: 30),
      pauseFor: const Duration(seconds: 3),
      partialResults: true,
      onResult: (result) {
        lastHypothesis = result.recognizedWords;

        if (result.finalResult) {
          final text = result.recognizedWords;
          final cmd = parseCommand(text);
          if (cmd != null) {
            lastCommand = cmd;
          }
        }

        notifyListeners();
      },
    );

    if (started) {
      _isListening = true;
      notifyListeners();
    }
  }

  Future<void> stopListening() async {
    await _speech.stop();
    _isListening = false;
    notifyListeners();
  }

  // ---------------------------------------------------------------------------
  // Command parsing
  // ---------------------------------------------------------------------------

  /// Returns the recognised command keyword, or `null` if no command matched.
  String? parseCommand(String text) {
    final trimmed = text.trim().toLowerCase();

    // Priority-ordered so more specific phrases are checked first.
    if (trimmed == 'về trang chủ' || trimmed == 'trang chủ' || trimmed == 'home') {
      return 'home';
    }
    if (trimmed == 'quét tài liệu' || trimmed == 'quét' || trimmed == 'scan' || trimmed == 'chụp ảnh') {
      return 'scanner';
    }
    if (trimmed == 'hỏi đáp' || trimmed == 'hỏi bài' || trimmed == 'đặt câu hỏi' || trimmed == 'câu hỏi' || trimmed == 'qa') {
      return 'voice-qa';
    }
    if (trimmed == 'ôn tập' || trimmed == 'xem lại' || trimmed == 'review') {
      return 'review';
    }
    if (trimmed == 'cài đặt' || trimmed == 'settings' || trimmed == 'setting') {
      return 'settings';
    }
    if (trimmed == 'dừng lại' || trimmed == 'im lặng' || trimmed == 'stop') {
      return 'stop';
    }
    if (trimmed == 'đọc lại' || trimmed == 'đọc' || trimmed == 'repeat') {
      return 'repeat';
    }
    if (trimmed == 'trợ giúp' || trimmed == 'giúp đỡ' || trimmed == 'help') {
      return 'help';
    }

    return null;
  }

  // ---------------------------------------------------------------------------
  // Lifecycle
  // ---------------------------------------------------------------------------

  @override
  void dispose() {
    stopListening();
    _speech.cancel();
    super.dispose();
  }

  // ---------------------------------------------------------------------------
  // Private handlers
  // ---------------------------------------------------------------------------

  void _onStatus(String status) {
    _isListening = status == 'listening';
    notifyListeners();
  }

  void _onError(dynamic error) {
    debugPrint('VoiceCommandService error: $error');
    _isListening = false;
    notifyListeners();
  }
}
