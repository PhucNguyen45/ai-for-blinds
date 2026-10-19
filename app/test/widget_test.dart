// Kiểm tra giao diện theo checklist trợ năng: nhãn TalkBack, vùng chạm,
// độ tương phản (dùng bộ kiểm tra có sẵn của Flutter).
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:sgbe/main.dart';
import 'package:sgbe/reader/reader_controller.dart';
import 'package:sgbe/services/capture_source.dart';
import 'package:sgbe/services/settings_store.dart';
import 'package:sgbe/strings.dart';

import 'fakes.dart';

void main() {
  late FakeApi api;
  late FakeSpeaker speaker;
  late FakeCapture capture;
  late FakeBridge bridge;

  Future<void> pumpApp(WidgetTester tester, {bool voiceReady = true}) async {
    SharedPreferences.setMockInitialValues({});
    final settings = await SettingsStore.load();
    api = FakeApi();
    speaker = FakeSpeaker();
    capture = FakeCapture();
    bridge = FakeBridge();
    final controller = ReaderController(api: () => api, speaker: speaker, earcons: FakeEarcons());
    tester.view.physicalSize = const Size(1080, 2340);
    tester.view.devicePixelRatio = 3;
    addTearDown(tester.view.reset);
    await tester.pumpWidget(SgbeApp(
      controller: controller,
      settings: settings,
      speaker: speaker,
      voiceReady: voiceReady,
      capture: capture,
      bridge: bridge,
    ));
    await tester.pump();
  }

  testWidgets('màn hình chính có nhãn TalkBack cho vùng chụp và 3 nút', (tester) async {
    await pumpApp(tester);
    expect(find.bySemanticsLabel(S.captureLabel), findsOneWidget);
    expect(find.bySemanticsLabel(S.repeat), findsOneWidget);
    expect(find.bySemanticsLabel(S.pickImage), findsOneWidget);
    expect(find.bySemanticsLabel(S.settings), findsOneWidget);
  });

  testWidgets('màn hình chính đạt chuẩn vùng chạm, nhãn và tương phản', (tester) async {
    final handle = tester.ensureSemantics();
    await pumpApp(tester);
    await expectLater(tester, meetsGuideline(androidTapTargetGuideline));
    await expectLater(tester, meetsGuideline(labeledTapTargetGuideline));
    await expectLater(tester, meetsGuideline(textContrastGuideline));
    handle.dispose();
  });

  testWidgets('nút lớn cao ít nhất 80 điểm ảnh logic', (tester) async {
    await pumpApp(tester);
    for (final label in [S.repeat, S.pickImage, S.settings]) {
      expect(tester.getSize(find.bySemanticsLabel(label)).height, greaterThanOrEqualTo(80), reason: label);
    }
  });

  testWidgets('chạm vùng camera: chụp, gửi, đọc mô tả và hiện chữ', (tester) async {
    await pumpApp(tester);
    await tester.tap(find.bySemanticsLabel(S.captureLabel));
    await tester.pumpAndSettle();
    expect(capture.pictures, 1);
    expect(api.describeCalls, 1);
    expect(speaker.spoken.last, 'Trang có một lược đồ.');
    expect(find.text('Trang có một lược đồ.'), findsOneWidget);
  });

  testWidgets('bấm nút âm lượng cũng chụp', (tester) async {
    await pumpApp(tester);
    bridge.keys.add('down');
    await tester.pumpAndSettle();
    expect(capture.pictures, 1);
    expect(api.describeCalls, 1);
  });

  testWidgets('camera bị từ chối quyền: báo bằng giọng nói, không gửi gì', (tester) async {
    await pumpApp(tester);
    capture.cameraState = CameraState.denied;
    await tester.pump();
    await tester.tap(find.bySemanticsLabel(S.captureLabel));
    await tester.pumpAndSettle();
    expect(api.describeCalls, 0);
    expect(speaker.spoken.last, S.cameraDenied);
  });

  testWidgets('thiếu giọng tiếng Việt: hiện cảnh báo và nút mở cài đặt giọng đọc', (tester) async {
    await pumpApp(tester, voiceReady: false);
    expect(find.text(S.voiceMissingShown), findsOneWidget);
    await tester.tap(find.bySemanticsLabel(S.openTtsSettings));
    await tester.pump();
    expect(bridge.ttsSettingsOpened, 1);
  });

  testWidgets('màn hình Cài đặt mở được và đạt chuẩn tương phản', (tester) async {
    final handle = tester.ensureSemantics();
    await pumpApp(tester);
    await tester.tap(find.bySemanticsLabel(S.settings));
    await tester.pumpAndSettle();
    expect(find.text(S.serverUrl), findsOneWidget);
    await expectLater(tester, meetsGuideline(textContrastGuideline));
    await expectLater(tester, meetsGuideline(androidTapTargetGuideline));
    handle.dispose();
  });
}
