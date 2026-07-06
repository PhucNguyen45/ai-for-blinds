import 'dart:async';
import 'dart:io';

import 'package:audioplayers/audioplayers.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_tts/flutter_tts.dart';
import 'package:path_provider/path_provider.dart';
import 'package:record/record.dart';

import 'storage_service.dart';

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

  // --- STT ---
  bool _isListening = false;
  final StreamController<String> _sttResultController =
      StreamController<String>.broadcast();

  /// Stream of ASR (speech-to-text) results from the backend.
  Stream<String> get sttResults => _sttResultController.stream;

  static const _settingsKey = 'tts_settings';

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

  // ========== Settings Persistence ==========

  /// Initialize with persisted settings. Call after construction.
  Future<void> init() async {
    await _loadSettings();
    // Re-apply loaded settings to TTS engine
    await _tts.setSpeechRate(_speechRate);
    await _tts.setPitch(_pitch);
    await _tts.setVolume(_volume);
    await cleanupOldRecordings();
  }

  Future<void> _loadSettings() async {
    try {
      final storage = StorageService();
      final settings = await storage.readJson(_settingsKey);
      if (settings != null) {
        _speechRate = (settings['speechRate'] as num?)?.toDouble() ?? 0.5;
        _pitch = (settings['pitch'] as num?)?.toDouble() ?? 1.0;
        _volume = (settings['volume'] as num?)?.toDouble() ?? 1.0;
      }
    } catch (e) {
      debugPrint('Error loading TTS settings: $e');
    }
  }

  Future<void> _saveSettings() async {
    try {
      final storage = StorageService();
      await storage.writeJson(_settingsKey, {
        'speechRate': _speechRate,
        'pitch': _pitch,
        'volume': _volume,
      });
    } catch (e) {
      debugPrint('Error saving TTS settings: $e');
    }
  }

  // ========== TTS Methods ==========

  /// Speak the given text aloud. Stops any current speech first.
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
    _isSpeaking = false;
    _isPaused = false;
    notifyListeners();
  }

  /// Set speech rate (0.0 - 1.0, default 0.5).
  Future<void> setSpeechRate(double rate) async {
    _speechRate = rate;
    await _tts.setSpeechRate(rate);
    notifyListeners();
    _saveSettings(); // fire and forget
  }

  /// Set pitch (0.5 - 2.0, default 1.0).
  Future<void> setPitch(double p) async {
    _pitch = p;
    await _tts.setPitch(p);
    notifyListeners();
    _saveSettings(); // fire and forget
  }

  /// Set volume (0.0 - 1.0, default 1.0).
  Future<void> setVolume(double vol) async {
    _volume = vol;
    await _tts.setVolume(vol);
    notifyListeners();
    _saveSettings(); // fire and forget
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

  /// Delete recordings older than 7 days to prevent storage buildup.
  Future<void> cleanupOldRecordings() async {
    try {
      final appDir = await getApplicationDocumentsDirectory();
      final dir = Directory('${appDir.path}/voice_notes');
      if (!await dir.exists()) return;

      final cutoff = DateTime.now().subtract(const Duration(days: 7));
      final files = dir.listSync();
      int deleted = 0;

      for (final file in files) {
        if (file is File) {
          final stat = file.statSync();
          if (stat.modified.isBefore(cutoff)) {
            await file.delete();
            deleted++;
          }
        }
      }

      if (deleted > 0) {
        debugPrint('Cleaned up $deleted old recording(s)');
      }
    } catch (e) {
      debugPrint('Error cleaning up recordings: $e');
    }
  }

  @override
  void dispose() {
    _tts.stop();
    _recorder.dispose();
    _player.dispose();
    _sttResultController.close();
    super.dispose();
  }
}
