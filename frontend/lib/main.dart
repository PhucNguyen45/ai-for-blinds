import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import 'api/models.dart';
import 'app_services.dart';
import 'library/library_data.dart';
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
  // Tràn viền: hình camera chạy cả dưới thanh trạng thái và thanh điều hướng.
  await SystemChrome.setEnabledSystemUIMode(SystemUiMode.edgeToEdge);
  SystemChrome.setSystemUIOverlayStyle(
    const SystemUiOverlayStyle(
      statusBarColor: Colors.transparent,
      systemNavigationBarColor: Colors.transparent,
      statusBarIconBrightness: Brightness.light,
      systemNavigationBarIconBrightness: Brightness.light,
    ),
  );

  final settings = await SettingsStore.load();
  // Chạy thử trên máy ảo không có máy chủ: flutter run --dart-define=SGBE_DEMO=true
  if (const bool.fromEnvironment('SGBE_DEMO') && !settings.demoMode) await settings.setDemoMode(true);
  final speaker = CaptionedSpeaker(TtsSpeaker());
  var voiceReady = false;
  try {
    voiceReady = await speaker.init(rate: settings.speechRate);
  } catch (_) {
    voiceReady = false;
  }

  final earcons = AudioEarconPlayer(enabled: () => settings.soundOn);
  final controller = ReaderController(
    api: () => settings.api,
    speaker: speaker,
    earcons: earcons,
    pageType: () => settings.pageType,
  );
  final services = AppServices(
    controller: controller,
    settings: settings,
    speaker: speaker,
    capture: DeviceCaptureSource(),
    bridge: PlatformBridge(),
    earcons: earcons,
    haptics: Haptics(enabled: () => settings.vibrateOn),
    library: ApiLibrarySource(api: () => settings.api, cache: settings),
  );

  runApp(SgbeApp(services: services, voiceReady: voiceReady));

  // Câu đầu tiên người dùng nghe khi mở app: lần đầu là lời hướng dẫn đầy đủ.
  if (!voiceReady) {
    await speaker.speakEnglish(S.voiceMissingEnglish);
  } else if (!settings.tutorialDone) {
    await settings.setTutorialDone(true);
    unawaited(controller.readText(S.tutorial, id: 'help'));
  } else {
    await controller.announce(S.greeting);
    if (!settings.demoMode) unawaited(_checkServer(settings, controller));
  }
}

/// Kiểm máy chủ một lần khi mở app: học sinh biết ngay nếu chưa chụp-đọc được (mất mạng, sai địa chỉ),
/// hoặc máy chủ đang trả dữ liệu thử. Kết nối tốt thì im lặng.
Future<void> _checkServer(SettingsStore settings, ReaderController controller) async {
  final health = await settings.api.health();
  if (controller.status != ReaderStatus.idle) return; // người dùng đã bắt đầu dùng app: không chen ngang
  switch (health) {
    case ApiFail():
      await controller.announce(S.serverUnreachableStart);
    case ApiOk(:final value) when value.isMock:
      await controller.announce(S.serverMockStart);
    case ApiOk():
      break;
  }
}

class SgbeApp extends StatelessWidget {
  const SgbeApp({super.key, required this.services, required this.voiceReady});

  final AppServices services;
  final bool voiceReady;

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: S.appName,
      debugShowCheckedModeBanner: false,
      theme: AppTheme.build(),
      home: HomeScreen(services: services, voiceReady: voiceReady),
    );
  }
}
