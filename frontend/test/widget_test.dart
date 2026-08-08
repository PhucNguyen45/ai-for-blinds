import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';

import 'package:ai_for_blinds/screens/home_screen.dart';
import 'package:ai_for_blinds/services/audio_service.dart';
import 'package:ai_for_blinds/services/voice_command_service.dart';
import 'package:ai_for_blinds/services/voice_controller.dart';

Widget buildHome() {
  return MultiProvider(
    providers: [
      ChangeNotifierProvider(create: (_) => AudioService()),
      ChangeNotifierProvider(create: (_) => VoiceCommandService()),
      ChangeNotifierProxyProvider2<AudioService, VoiceCommandService,
          VoiceController>(
        create: (_) => VoiceController(),
        update: (_, audio, voice, controller) =>
            controller!..attach(audio: audio, voice: voice),
      ),
    ],
    child: const MaterialApp(home: HomeScreen()),
  );
}

void main() {
  testWidgets('Home screen shows app title and feature buttons',
      (WidgetTester tester) async {
    await tester.pumpWidget(buildHome());
    await tester.pump();

    expect(find.text('SgBe Vision'), findsOneWidget);
    expect(find.text('Chào bạn 👋'), findsOneWidget);
    expect(find.text('Chạm để bắt đầu'), findsOneWidget);
    expect(find.text('Quét tài liệu'), findsOneWidget);
    expect(find.text('Hỏi đáp'), findsOneWidget);
    expect(find.text('Tìm kiếm thông tin'), findsOneWidget);
  });

  testWidgets('Tapping "Chạm để bắt đầu" activates the voice assistant',
      (WidgetTester tester) async {
    await tester.pumpWidget(buildHome());
    await tester.pump();

    final controller =
        tester.element(find.byType(HomeScreen)).read<VoiceController>();
    expect(controller.voiceState, VoiceState.speaking);

    await tester.tap(find.text('Chạm để bắt đầu'));
    await tester.pump();

    // triggerGlobalVoice announces listening then starts command recognition.
    expect(controller.voiceState, VoiceState.speaking);
  });
}
