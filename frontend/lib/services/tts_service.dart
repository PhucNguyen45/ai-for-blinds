import 'package:flutter/foundation.dart';
import 'package:flutter_tts/flutter_tts.dart';

/// Service that wraps FlutterTts with a simple API for the app.
/// Provides text-to-speech with configurable speed, pitch, and volume.
class TtsService extends ChangeNotifier {
  final FlutterTts _tts = FlutterTts();

  double _speechRate = 0.5;
  double _pitch = 1.0;
  double _volume = 1.0;
  bool _isSpeaking = false;
  bool _isPaused = false;
  String _selectedLanguage = 'en-US';
  String _lastSpokenText = '';

  TtsService() {
    _initTts();
  }

  // Getters
  double get speechRate => _speechRate;
  double get pitch => _pitch;
  double get volume => _volume;
  bool get isSpeaking => _isSpeaking;
  bool get isPaused => _isPaused;
  String get selectedLanguage => _selectedLanguage;

  Future<void> _initTts() async {
    await _tts.setLanguage(_selectedLanguage);
    await _tts.setSpeechRate(_speechRate);
    await _tts.setPitch(_pitch);
    await _tts.setVolume(_volume);

    _tts.setStartHandler(() {
      _isSpeaking = true;
      _isPaused = false;
      notifyListeners();
    });

    _tts.setCompletionHandler(() {
      _isSpeaking = false;
      _isPaused = false;
      notifyListeners();
    });

    _tts.setCancelHandler(() {
      _isSpeaking = false;
      _isPaused = false;
      notifyListeners();
    });

    _tts.setErrorHandler((msg) {
      _isSpeaking = false;
      _isPaused = false;
      debugPrint('TTS Error: $msg');
      notifyListeners();
    });
  }

  /// Speak the given text aloud.
  Future<void> speak(String text) async {
    if (text.trim().isEmpty) return;
    _lastSpokenText = text;
    await _tts.stop();
    await _tts.speak(text);
  }

  /// Pause current speech.
  Future<void> pause() async {
    final paused = await _tts.pause();
    if (paused == 1) {
      _isPaused = true;
      notifyListeners();
    }
  }

  /// Resume paused speech (restarts from beginning).
  Future<void> resume() async {
    if (_lastSpokenText.isNotEmpty) {
      await speak(_lastSpokenText);
    }
    _isPaused = false;
    notifyListeners();
  }

  /// Stop speech entirely.
  Future<void> stop() async {
    await _tts.stop();
    _isSpeaking = false;
    _isPaused = false;
    notifyListeners();
  }

  /// Set speech rate (0.0 - 1.0, default 0.5).
  Future<void> setSpeechRate(double rate) async {
    _speechRate = rate;
    await _tts.setSpeechRate(rate);
    notifyListeners();
  }

  /// Set pitch (0.5 - 2.0, default 1.0).
  Future<void> setPitch(double p) async {
    _pitch = p;
    await _tts.setPitch(p);
    notifyListeners();
  }

  /// Set volume (0.0 - 1.0, default 1.0).
  Future<void> setVolume(double vol) async {
    _volume = vol;
    await _tts.setVolume(vol);
    notifyListeners();
  }

  /// Set language (e.g., 'en-US', 'vi-VN', 'hi-IN').
  Future<void> setLanguage(String lang) async {
    _selectedLanguage = lang;
    await _tts.setLanguage(lang);
    notifyListeners();
  }

  /// Get available languages.
  Future<Set<String>> getLanguages() async {
    return await _tts.getLanguages;
  }

  /// Whether the current language is Vietnamese.
  bool get isVietnamese => _selectedLanguage.startsWith('vi');

  /// Preload Vietnamese voice samples.
  Future<void> setVietnamese() async {
    await setLanguage('vi-VN');
  }

  @override
  void dispose() {
    _tts.stop();
    super.dispose();
  }
}
