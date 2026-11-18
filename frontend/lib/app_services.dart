import 'package:flutter/foundation.dart';

import 'library/library_data.dart';
import 'reader/reader_controller.dart';
import 'services/capture_source.dart';
import 'services/earcons.dart';
import 'services/platform_bridge.dart';
import 'services/settings_store.dart';
import 'services/speech.dart';
import 'services/speech_input.dart';
import 'ui/explore.dart';

/// Mọi dịch vụ các màn hình cần, gom một chỗ để truyền đi và thay bằng đồ giả khi test.
///
/// Cũng là phản hồi của lớp thao tác: chạm một lần thì tách + rung nhẹ + đọc tên nút,
/// chạm hai lần thì âm xác nhận + rung.
class AppServices implements ExploreFeedback {
  AppServices({
    required this.controller,
    required this.settings,
    required this.speaker,
    required this.capture,
    required this.bridge,
    required this.earcons,
    required this.haptics,
    this.library = const AssetLibrarySource(),
    SpeechInput? speechInput,
  }) : speechInput = speechInput ?? AndroidSpeechInput();

  final ReaderController controller;
  final SettingsStore settings;
  final CaptionedSpeaker speaker;
  final CaptureSource capture;
  final PlatformBridge bridge;
  final EarconPlayer earcons;
  final Haptics haptics;
  final LibrarySource library;

  /// Nhận giọng nói tiếng Việt (màn hình Hỏi).
  final SpeechInput speechInput;

  /// Câu app đang nói, cho phụ đề.
  ValueListenable<Caption> get caption => speaker.caption;

  @override
  void onFocus(String spoken) {
    earcons.play(Earcon.focus);
    haptics.focus();
    controller.announce(spoken);
  }

  @override
  void onActivate() {
    earcons.play(Earcon.activate);
    haptics.activate();
  }
}
