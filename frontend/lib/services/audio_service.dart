import 'dart:async';
import 'dart:io';

import 'package:audioplayers/audioplayers.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_tts/flutter_tts.dart';
import 'package:path_provider/path_provider.dart';
import 'package:record/record.dart';

import 'api_service.dart';

/// Service that manages ALL audio operations in the app.
/// Combines TTS (flutter_tts), STT (speech_to_text), and recording (record package).
/// Exposed as a ChangeNotifier via Provider for reactive UI.
class AudioService extends ChangeNotifier {
  // --- TTS ---
  final FlutterTts _tts = FlutterTts();
  double _speechRate = 0.5;
  double _pitch = 1.0;
  double _volume = 1.0;
  bool _isSpeaking = false;
  bool _isPaused = false;
  String _selectedLanguage = 'vi-VN';
  String _lastSpokenText = '';

  // --- Recording ---
  final AudioRecorder _recorder = AudioRecorder();
  String? _currentRecordingPath;
  bool _isRecording = false;

  // --- Playback ---
  final AudioPlayer _player = AudioPlayer();
  final ApiService _api = ApiService();

  /// Prefer the server voice (Edge TTS, giọng Hoài My) over the on-device
  /// engine.
  ///
  /// A single timeout is not proof the server is gone — it may just have been
  /// busy answering a description. Give up only after two failures in a row,
  /// and try again after a minute rather than staying on the weaker device
  /// voice for the rest of the session.
  static const _failuresBeforeGivingUp = 2;
  static const _retryAfter = Duration(minutes: 1);

  bool _useServerVoice = true;
  int _serverVoiceFailures = 0;
  DateTime? _serverVoiceDisabledAt;

  bool get useServerVoice => _useServerVoice;
  set useServerVoice(bool value) {
    _useServerVoice = value;
    _serverVoiceFailures = 0;
    _serverVoiceDisabledAt = null;
    notifyListeners();
  }

  bool get _shouldTryServerVoice {
    if (_useServerVoice) return true;
    final since = _serverVoiceDisabledAt;
    if (since != null && DateTime.now().difference(since) > _retryAfter) {
      _useServerVoice = true;
      _serverVoiceFailures = 0;
      return true;
    }
    return false;
  }

  // --- STT ---
  bool _isListening = false;
  final StreamController<String> _sttResultController =
      StreamController<String>.broadcast();

  /// Stream of ASR (speech-to-text) results from the backend.
  Stream<String> get sttResults => _sttResultController.stream;

  // ========== Getters ==========

  // TTS
  double get speechRate => _speechRate;
  double get pitch => _pitch;
  double get volume => _volume;
  bool get isSpeaking => _isSpeaking;
  bool get isPaused => _isPaused;
  String get selectedLanguage => _selectedLanguage;

  // Recording
  bool get isRecording => _isRecording;
  String? get currentRecordingPath => _currentRecordingPath;

  // Playback
  bool get isPlaying => _player.state == PlayerState.playing;
  Stream<void> get onPlaybackComplete => _player.onPlayerComplete;

  // STT
  bool get isListening => _isListening;

  // ========== Initialization ==========

  AudioService() {
    _initTts();
  }

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

  // ========== TTS Methods ==========

  /// Speak the given text aloud. Stops any current speech first.
  ///
  /// Tries the server voice, falls back to the on-device engine so the app
  /// still talks with no network.
  Future<void> speak(String text) async {
    if (text.trim().isEmpty) return;
    _lastSpokenText = text;
    await _tts.stop();
    await _player.stop();

    if (_shouldTryServerVoice) {
      final bytes = await _api.ttsAudio(text);
      if (bytes != null && bytes.isNotEmpty) {
        _serverVoiceFailures = 0;
        try {
          final dir = await getTemporaryDirectory();
          final file = File(
            '${dir.path}/sgbe_speak_'
            '${DateTime.now().millisecondsSinceEpoch}.mp3',
          );
          await file.writeAsBytes(bytes);
          _isSpeaking = true;
          notifyListeners();
          await _player.play(DeviceFileSource(file.path));
          return;
        } catch (e) {
          debugPrint('Server voice playback failed: $e');
        }
      } else {
        _serverVoiceFailures++;
        if (_serverVoiceFailures >= _failuresBeforeGivingUp) {
          // Stop paying the timeout on every sentence, but only for a while.
          _useServerVoice = false;
          _serverVoiceDisabledAt = DateTime.now();
          debugPrint('Server voice off for ${_retryAfter.inMinutes} min');
        }
      }
    }

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

  /// Resume paused speech (re-speaks from last known text).
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
    await _player.stop();
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

  /// Set language (e.g., 'en-US', 'vi-VN').
  Future<void> setLanguage(String lang) async {
    _selectedLanguage = lang;
    await _tts.setLanguage(lang);
    notifyListeners();
  }

  Future<Set<String>> getLanguages() async {
    return await _tts.getLanguages;
  }

  bool get isVietnamese => _selectedLanguage.startsWith('vi');

  // ========== Recording Methods ==========

  /// Request microphone permission.
  Future<bool> requestMicPermission() async {
    return await _recorder.hasPermission();
  }

  /// Start recording audio. Returns the file path, or null on failure.
  Future<String?> startRecording({String? directory}) async {
    try {
      final dir = directory ?? await _getDefaultDirectory();
      final timestamp = DateTime.now().millisecondsSinceEpoch;
      final path = '$dir/note_$timestamp.m4a';

      await _recorder.start(
        const RecordConfig(
          encoder: AudioEncoder.aacLc,
          bitRate: 128000,
          sampleRate: 44100,
        ),
        path: path,
      );

      _isRecording = true;
      _currentRecordingPath = path;
      notifyListeners();
      return path;
    } catch (e) {
      debugPrint('AudioService.startRecording error: $e');
      return null;
    }
  }

  /// Stop recording and return the file path. Returns null if not recording.
  Future<String?> stopRecording() async {
    if (!_isRecording) return null;
    try {
      final path = await _recorder.stop();
      _isRecording = false;
      notifyListeners();
      return path;
    } catch (e) {
      debugPrint('AudioService.stopRecording error: $e');
      _isRecording = false;
      notifyListeners();
      return null;
    }
  }

  Future<String> _getDefaultDirectory() async {
    final appDir = await getApplicationDocumentsDirectory();
    final notesDir = Directory('${appDir.path}/voice_notes');
    if (!await notesDir.exists()) {
      await notesDir.create(recursive: true);
    }
    return notesDir.path;
  }

  // ========== Playback Methods ==========

  /// Play an audio file.
  Future<bool> playFile(String filePath) async {
    try {
      final file = File(filePath);
      if (!await file.exists()) return false;
      if (isPlaying) await _player.stop();
      await _player.play(DeviceFileSource(filePath));
      return true;
    } catch (e) {
      debugPrint('AudioService.playFile error: $e');
      return false;
    }
  }

  /// Stop audio playback.
  Future<void> stopPlayback() async {
    await _player.stop();
  }

  // ========== STT Methods ==========

  /// Simulate setting the listening state.
  /// Actual STT is handled by sending audio to backend /stt endpoint.
  void setListening(bool value) {
    _isListening = value;
    notifyListeners();
  }

  /// Emit a speech-to-text result (called by the UI when backend responds).
  void emitSttResult(String text) {
    _sttResultController.add(text);
  }

  // ========== Cleanup ==========

  @override
  void dispose() {
    _tts.stop();
    _recorder.dispose();
    _player.dispose();
    _sttResultController.close();
    super.dispose();
  }
}
