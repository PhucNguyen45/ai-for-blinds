import 'dart:async';

import 'package:flutter/foundation.dart';

import 'audio_service.dart';
import 'voice_command_service.dart';

/// The overall voice interaction state shown across the app.
enum VoiceState {
  /// No activity — waiting for the user.
  idle,

  /// The microphone is listening for a command or question.
  listening,

  /// A request is being processed (e.g. AI inference).
  processing,

  /// Text-to-speech is speaking.
  speaking,

  /// An error occurred.
  error,
}

/// Coordinates all global voice interaction: TTS prompts, on-device command
/// listening (via [VoiceCommandService]) and the [VoiceState] exposed to the
/// UI. Screens that only care about content recording (Q&A / search) keep
/// using [AudioService] directly.
class VoiceController extends ChangeNotifier {
  AudioService? _audio;
  VoiceCommandService? _voice;
  StreamSubscription<void>? _ttsSubscription;

  /// Route navigation callback set by the app shell (e.g. '/scanner').
  ValueChanged<String>? onNavigate;

  bool _autoListen = false;
  bool _listenAfterPrompt = false;
  bool _isCommandListening = false;
  VoiceState _voiceState = VoiceState.idle;

  VoiceController();

  AudioService get audio => _audio!;
  VoiceCommandService get voice => _voice!;

  /// Whether the app should automatically start listening for commands after
  /// speaking a prompt. Persisted by the settings screen.
  bool get autoListen => _autoListen;
  set autoListen(bool value) {
    if (_autoListen == value) return;
    _autoListen = value;
    notifyListeners();
  }

  VoiceState get voiceState => _voiceState;

  /// Bind this controller to the app-wide services. Idempotent.
  void attach({
    required AudioService audio,
    required VoiceCommandService voice,
  }) {
    _audio = audio;
    _voice = voice;
    _ttsSubscription ??= audio.onTtsComplete.listen((_) => _onTtsComplete());
    voice.onCommand = _onCommand;
    voice.onUnrecognized = _onUnrecognized;
  }

  void _setState(VoiceState state) {
    if (_voiceState == state) return;
    _voiceState = state;
    notifyListeners();
  }

  /// Speak [text]. When [awaitReply] is true and auto-listen is enabled,
  /// the app starts listening for a command once TTS finishes.
  Future<void> speak(String text, {bool awaitReply = false}) async {
    _listenAfterPrompt = awaitReply && _autoListen;
    _setState(VoiceState.speaking);
    await audio.stop();
    await audio.speak(text);
  }

  /// Speak [text] and always start command listening afterwards, regardless
  /// of the auto-listen setting (used for prompts that expect a reply).
  Future<void> _speakAndListen(String text) async {
    _listenAfterPrompt = true;
    _setState(VoiceState.speaking);
    await audio.stop();
    await audio.speak(text);
  }

  /// Global voice trigger — called from long-press, shake or the voice FAB.
  /// Announces listening and then starts on-device command recognition.
  Future<void> triggerGlobalVoice() async {
    await _speakAndListen('Tôi đang nghe. Hãy nói lệnh của bạn.');
  }

  /// Start on-device command listening.
  Future<void> startCommandListening() async {
    if (_isCommandListening) return;
    _isCommandListening = true;
    _setState(VoiceState.listening);
    await voice.startListening();
    if (!voice.isListening) {
      _isCommandListening = false;
      _setState(VoiceState.idle);
    }
  }

  /// Stop on-device command listening.
  Future<void> stopCommandListening() async {
    if (!_isCommandListening) return;
    _isCommandListening = false;
    await voice.stopListening();
    if (_voiceState == VoiceState.listening) _setState(VoiceState.idle);
  }

  void _onTtsComplete() {
    if (_listenAfterPrompt) {
      _listenAfterPrompt = false;
      startCommandListening();
    } else if (_voiceState == VoiceState.speaking) {
      _setState(VoiceState.idle);
    }
  }

  void _onCommand(String cmd) {
    _isCommandListening = false;
    _setState(VoiceState.processing);
    switch (cmd) {
      case 'home':
        _navigateAndConfirm('/', 'Đã về trang chủ.');
      case 'scanner':
        _navigateAndConfirm('/scanner', 'Đã mở chế độ quét tài liệu.');
      case 'voice-qa':
        _navigateAndConfirm('/voice-qa', 'Đã mở màn hình hỏi đáp kiến thức.');
      case 'search':
        _navigateAndConfirm('/search', 'Đã mở màn hình tìm kiếm thông tin.');
      case 'review':
        _navigateAndConfirm('/review', 'Đã mở màn hình ôn tập.');
      case 'settings':
        _navigateAndConfirm('/settings', 'Đã mở màn hình cài đặt.');
      case 'stop':
        _setState(VoiceState.idle);
        audio.speak('Đã dừng nghe lệnh.');
      case 'repeat':
        final last = audio.lastSpokenText;
        if (last.isNotEmpty) speak(last);
      case 'help':
        _speakAndListen(_helpText);
    }
  }

  void _navigateAndConfirm(String route, String confirmation) {
    onNavigate?.call(route);
    speak(confirmation);
  }

  void _onUnrecognized(String text) {
    _isCommandListening = false;
    final trimmed = text.trim();
    final prompt = trimmed.isEmpty
        ? 'Tôi không nghe rõ. Hãy nói lại lệnh của bạn.'
        : 'Tôi không hiểu lệnh "$trimmed". Nói "trợ giúp" để nghe danh sách lệnh.';
    _speakAndListen(prompt);
  }

  static const _helpText =
      'Bạn có thể nói: trang chủ, quét tài liệu, hỏi đáp, tìm kiếm, '
      'ôn tập, cài đặt, dừng lại, đọc lại, hoặc trợ giúp. '
      'Nhấn giữ màn hình hoặc lắc nhẹ máy để gọi giọng nói bất cứ lúc nào. '
      'Vuốt trái phải để chuyển trang.';

  @override
  void dispose() {
    _ttsSubscription?.cancel();
    super.dispose();
  }
}
