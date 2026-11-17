import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import 'reader/reader_controller.dart';
import 'services/capture_source.dart';
import 'services/earcons.dart';
import 'services/platform_bridge.dart';
import 'services/settings_store.dart';
import 'services/speech.dart';
import 'strings.dart';
import 'ui/home_screen.dart';
import 'ui/theme.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await SystemChrome.setPreferredOrientations([DeviceOrientation.portraitUp]);

  final settings = await SettingsStore.load();
  final speaker = TtsSpeaker();
  var voiceReady = false;
  try {
    voiceReady = await speaker.init(rate: settings.speechRate);
  } catch (_) {
    voiceReady = false;
  }

  final controller = ReaderController(
    api: () => settings.api,
    speaker: speaker,
    earcons: AudioEarconPlayer(),
    pageType: () => settings.pageType,
  );

  runApp(SgbeApp(
    controller: controller,
    settings: settings,
    speaker: speaker,
    voiceReady: voiceReady,
  ));

  // Câu đầu tiên người dùng nghe khi mở app.
  if (voiceReady) {
    await controller.announce(S.greeting);
  } else {
    await speaker.speakEnglish(S.voiceMissingEnglish);
  }
}

class SgbeApp extends StatelessWidget {
  const SgbeApp({
    super.key,
    required this.controller,
    required this.settings,
    required this.speaker,
    required this.voiceReady,
    this.capture,
    this.bridge,
  });

  final ReaderController controller;
  final SettingsStore settings;
  final Speaker speaker;
  final bool voiceReady;
  final CaptureSource? capture;
  final PlatformBridge? bridge;

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: S.appName,
      debugShowCheckedModeBanner: false,
      theme: AppTheme.build(),
      home: HomeScreen(
        controller: controller,
        settings: settings,
        capture: capture ?? DeviceCaptureSource(),
        bridge: bridge ?? PlatformBridge(),
        speaker: speaker,
        voiceReady: voiceReady,
      ),
    );
  }
}
