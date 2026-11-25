// Kiểm tra giao diện theo yêu cầu UI-xx (docs/YEU_CAU_GIAO_DIEN.md) và checklist trợ năng:
// nhãn TalkBack, vùng chạm, tương phản (bộ kiểm tra có sẵn của Flutter), cách thao tác
// "chạm để nghe, chạm hai lần để dùng", và không tràn chữ khi phóng chữ hoặc màn hình nhỏ.
import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:sgbe/app_services.dart';
import 'package:sgbe/library/library_data.dart';
import 'package:sgbe/main.dart';
import 'package:sgbe/reader/reader_controller.dart';
import 'package:sgbe/services/capture_source.dart';
import 'package:sgbe/services/earcons.dart';
import 'package:sgbe/services/settings_store.dart';
import 'package:sgbe/services/speech.dart';
import 'package:sgbe/services/speech_input.dart';
import 'package:sgbe/strings.dart';
import 'package:sgbe/ui/ask_screen.dart';
import 'package:sgbe/ui/widgets.dart';

import 'fakes.dart';

void main() {
  late FakeApi api;
  late FakeSpeaker speaker;
  late FakeCapture capture;
  late FakeBridge bridge;
  late FakeEarcons earcons;
  late SettingsStore settings;
  late ReaderController controller;
  late FakeSpeechInput stt;

  Future<void> pumpApp(
    WidgetTester tester, {
    bool voiceReady = true,
    bool sttOk = true,
    Size size = const Size(1080, 2340),
    double ratio = 3,
    LibrarySource library = const FakeLibrary(),
  }) async {
    SharedPreferences.setMockInitialValues({'tutorial_done': true});
    settings = await SettingsStore.load();
    api = FakeApi();
    speaker = FakeSpeaker();
    capture = FakeCapture();
    bridge = FakeBridge();
    earcons = FakeEarcons();
    stt = FakeSpeechInput(ok: sttOk);
    final captioned = CaptionedSpeaker(speaker);
    controller = ReaderController(api: () => api, speaker: captioned, earcons: earcons);
    final services = AppServices(
      controller: controller,
      settings: settings,
      speaker: captioned,
      capture: capture,
      bridge: bridge,
      earcons: earcons,
      haptics: Haptics(),
      library: library,
      speechInput: stt,
    );
    tester.view.physicalSize = size;
    tester.view.devicePixelRatio = ratio;
    addTearDown(tester.view.reset);
    await tester.pumpWidget(SgbeApp(services: services, voiceReady: voiceReady));
    await tester.pump();
  }

  /// Hai lần chạm liền (TestGesture mặc định cùng mốc thời gian, nên luôn trong khoảng chạm hai lần).
  Future<void> doubleTap(WidgetTester tester, Finder f) async {
    await tester.tap(f);
    await tester.pump(const Duration(milliseconds: 80));
    await tester.tap(f);
    await tester.pump();
  }

  Finder label(String l) => find.bySemanticsLabel(l);
  Finder inReading(Finder f) => find.descendant(of: find.byType(ReadingText), matching: f);

  Future<void> captureOnce(WidgetTester tester) async {
    await doubleTap(tester, label(S.captureLabel));
    await tester.pumpAndSettle();
  }

  Future<void> checkGuidelines(WidgetTester tester) async {
    await expectLater(tester, meetsGuideline(androidTapTargetGuideline));
    await expectLater(tester, meetsGuideline(labeledTapTargetGuideline));
    await expectLater(tester, meetsGuideline(textContrastGuideline));
  }

  group('màn hình chính', () {
    testWidgets('UI-20: vùng chụp, 3 nút mép dưới, 2 nút góc trên đều có nhãn TalkBack', (tester) async {
      await pumpApp(tester);
      for (final l in [S.captureLabel, S.repeat, S.ask, S.library, S.settings, S.helpLabel]) {
        expect(label(l), findsOneWidget, reason: l);
      }
    });

    testWidgets('UI-21, UI-22: đạt chuẩn vùng chạm, nhãn và tương phản', (tester) async {
      final handle = tester.ensureSemantics();
      await pumpApp(tester);
      await checkGuidelines(tester);
      handle.dispose();
    });

    testWidgets('UI-21: mọi nút cao ít nhất 80, vùng chụp chiếm phần lớn màn hình', (tester) async {
      await pumpApp(tester);
      for (final l in [S.repeat, S.ask, S.library, S.settings, S.helpLabel]) {
        expect(tester.getSize(label(l)).height, greaterThanOrEqualTo(80), reason: l);
      }
      final stage = tester.getSize(label(S.captureLabel));
      expect(stage.height, greaterThan(780 * 0.4), reason: 'vùng chụp phải là vùng lớn nhất');
    });

    testWidgets('ba nút mép dưới nằm sát đáy, theo thứ tự Đọc lại, Hỏi, Thư viện', (tester) async {
      await pumpApp(tester);
      final r = tester.getRect(label(S.repeat)), a = tester.getRect(label(S.ask)), l = tester.getRect(label(S.library));
      expect(r.left < a.left && a.left < l.left, isTrue);
      expect(780 - r.bottom, lessThan(40));
      expect(tester.getRect(label(S.settings)).left, lessThan(tester.getRect(label(S.helpLabel)).left));
    });
  });

  group('chạm để nghe, chạm hai lần để dùng', () {
    testWidgets('chạm một lần vùng chụp: chỉ đọc tên, có tiếng tách, không chụp', (tester) async {
      await pumpApp(tester);
      await tester.tap(label(S.captureLabel));
      await tester.pumpAndSettle();
      expect(capture.pictures, 0);
      expect(speaker.spoken.last, S.captureSay);
      expect(earcons.played, contains(Earcon.focus));
    });

    testWidgets('UI-01: chạm hai lần vùng chụp: chụp, gửi, đọc và hiện kết quả trong vùng chụp', (tester) async {
      await pumpApp(tester);
      await captureOnce(tester);
      expect(capture.pictures, 1);
      expect(api.describeCalls, 1);
      expect(speaker.spoken.last, 'Trang có một lược đồ.');
      expect(label(S.resultLabel), findsOneWidget);
      expect(inReading(find.textContaining('lược đồ', findRichText: true)), findsOneWidget, reason: 'UI-24');
      expect(earcons.played, containsAllInOrder([Earcon.activate, Earcon.shutter, Earcon.done]));
    });

    testWidgets('hai lần chạm cách nhau quá nửa giây: không chụp', (tester) async {
      await pumpApp(tester);
      final c = tester.getCenter(label(S.captureLabel));
      final g = await tester.createGesture();
      await g.down(c, timeStamp: Duration.zero);
      await g.up(timeStamp: const Duration(milliseconds: 50));
      await tester.pump();
      await g.down(c, timeStamp: const Duration(milliseconds: 900));
      await g.up(timeStamp: const Duration(milliseconds: 950));
      await tester.pumpAndSettle();
      expect(capture.pictures, 0);
      expect(speaker.spoken.where((s) => s == S.captureSay).length, 2);
    });

    testWidgets('chạm Đọc lại rồi chạm Hỏi (khác nút): chỉ nghe tên hai nút', (tester) async {
      await pumpApp(tester);
      await tester.tap(label(S.repeat));
      await tester.pump(const Duration(milliseconds: 80));
      await tester.tap(label(S.ask));
      await tester.pumpAndSettle();
      expect(speaker.spoken, containsAllInOrder([S.repeatSay, S.askSay]));
      expect(find.text(S.askTitle), findsNothing);
    });

    testWidgets('rê ngón tay qua ba nút mép dưới: nghe lần lượt tên từng nút, không dùng nút nào', (tester) async {
      await pumpApp(tester);
      final g = await tester.startGesture(tester.getCenter(label(S.repeat)));
      await g.moveTo(tester.getCenter(label(S.ask)));
      await g.moveTo(tester.getCenter(label(S.library)));
      await g.up();
      await tester.pumpAndSettle();
      expect(speaker.spoken, containsAllInOrder([S.repeatSay, S.askSay, S.librarySay]));
      expect(capture.pictures, 0);
      expect(find.text(S.library), findsOneWidget, reason: 'vẫn ở màn hình chính');
    });

    testWidgets('UI-03: đang đọc kết quả mà chạm bất kỳ: dừng đọc, nghe tên chỗ vừa chạm', (tester) async {
      await pumpApp(tester);
      speaker.hold = Completer<void>(); // mọi câu nói bị giữ lại: giả lập mô tả dài đang đọc
      await doubleTap(tester, label(S.captureLabel));
      for (var i = 0; i < 5; i++) {
        await tester.pump(const Duration(milliseconds: 50));
      }
      expect(controller.status, ReaderStatus.speaking);
      await tester.tap(label(S.repeat));
      await tester.pump();
      expect(controller.status, ReaderStatus.idle);
      expect(speaker.spoken.last, S.repeatSay);
      speaker.hold?.complete();
      await tester.pumpAndSettle();
    });

    testWidgets('kết quả: chạm hai lần vùng kết quả thì về camera', (tester) async {
      await pumpApp(tester);
      await captureOnce(tester);
      await doubleTap(tester, label(S.resultLabel));
      await tester.pumpAndSettle();
      expect(label(S.captureLabel), findsOneWidget);
      expect(speaker.spoken.last, S.cameraReady);
    });

    testWidgets('UI-16: TalkBack bật thì app nhường: chạm (TalkBack chạm hai lần) là dùng, app không tự đọc tên', (
      tester,
    ) async {
      tester.platformDispatcher.accessibilityFeaturesTestValue = const FakeAccessibilityFeatures(
        accessibleNavigation: true,
      );
      addTearDown(tester.platformDispatcher.clearAccessibilityFeaturesTestValue);
      await pumpApp(tester);
      await tester.tap(label(S.captureLabel));
      await tester.pumpAndSettle();
      expect(capture.pictures, 1);
      expect(speaker.spoken, isNot(contains(S.captureSay)));
      expect(earcons.played, isNot(contains(Earcon.focus)));
    });
  });

  group('chụp và lỗi', () {
    testWidgets('bấm nút âm lượng: chụp ngay, không cần chạm hai lần', (tester) async {
      await pumpApp(tester);
      bridge.keys.add('down');
      await tester.pumpAndSettle();
      expect(capture.pictures, 1);
      expect(api.describeCalls, 1);
    });

    testWidgets('camera bị từ chối quyền: báo bằng giọng nói, hiện thẻ lỗi, không gửi gì', (tester) async {
      await pumpApp(tester);
      capture.cameraState = CameraState.denied;
      await tester.pump();
      await doubleTap(tester, label(S.captureLabel));
      await tester.pumpAndSettle();
      expect(api.describeCalls, 0);
      expect(speaker.spoken.last, S.cameraDenied);
      expect(label(S.stateError), findsOneWidget);
    });

    testWidgets('UI-34: thiếu giọng tiếng Việt: hiện cảnh báo và nút mở cài đặt giọng đọc', (tester) async {
      await pumpApp(tester, voiceReady: false);
      expect(find.text(S.voiceMissingShown), findsOneWidget);
      await doubleTap(tester, label(S.openTtsSettings).first);
      await tester.pump();
      expect(bridge.ttsSettingsOpened, 1);
    });

    testWidgets('Đọc lại khi chưa chụp: âm lỗi và nhắc chụp trước', (tester) async {
      await pumpApp(tester);
      await doubleTap(tester, label(S.repeat));
      await tester.pumpAndSettle();
      expect(speaker.spoken.last, S.nothingToRepeat);
      expect(earcons.played.last, Earcon.error);
    });
  });

  group('Hỏi', () {
    testWidgets('chưa chụp thì chưa mở màn hình Hỏi', (tester) async {
      await pumpApp(tester);
      await doubleTap(tester, label(S.ask));
      await tester.pumpAndSettle();
      expect(speaker.spoken.last, S.askNeedPage);
      expect(find.text(S.askTitle), findsNothing);
    });

    Future<void> moHoi(WidgetTester tester) async {
      await captureOnce(tester);
      await doubleTap(tester, label(S.ask));
      await tester.pumpAndSettle();
    }

    testWidgets('UI-43: nói câu hỏi bằng giọng: gửi chữ nghe được + image_id, đọc câu trả lời; đạt chuẩn trợ năng', (
      tester,
    ) async {
      final handle = tester.ensureSemantics();
      await pumpApp(tester);
      await moHoi(tester);
      expect(find.text(S.askTitle), findsOneWidget);
      expect(speaker.spoken.last, S.askOpen);
      expect(label(S.askSuggestions[0]), findsNothing, reason: 'có nhận giọng nói thì không hiện câu gợi ý');
      await checkGuidelines(tester);

      await doubleTap(tester, label(S.mic));
      await tester.pumpAndSettle();
      expect(stt.listens, 1);
      expect(speaker.spoken, contains(S.sttPrompt), reason: 'mời nói trước khi mở micro');
      expect(api.lastQuestion, FakeSpeechInput.macDinh);
      expect(api.lastAskImageId, 'b9b1d4985e464bbb');
      expect(speaker.spoken.last, 'Trả lời.');
      expect(inReading(find.textContaining('Trả lời.', findRichText: true)), findsOneWidget);
      expect(find.text(FakeSpeechInput.macDinh), findsOneWidget, reason: 'câu hỏi hiện thành bong bóng');

      // Nút âm lượng cũng bật nghe; lượt hỏi sau gửi kèm lịch sử
      stt.results.add(const SttText('Còn gì nữa không?'));
      bridge.keys.add('down');
      await tester.pumpAndSettle();
      expect(stt.listens, 2);
      expect(api.lastQuestion, 'Còn gì nữa không?');
      expect(api.lastHistory.single.question, FakeSpeechInput.macDinh, reason: 'gửi kèm lượt hỏi trước');

      await doubleTap(tester, label(S.back));
      await tester.pumpAndSettle();
      expect(find.text(S.askTitle), findsNothing);
      expect(speaker.spoken.last, S.homeSay);
      handle.dispose();
    });

    testWidgets('không nghe rõ: báo bằng giọng nói, không gửi câu hỏi', (tester) async {
      await pumpApp(tester);
      await moHoi(tester);
      stt.results.add(const SttFail('7', S.sttNoMatch));
      await doubleTap(tester, label(S.mic));
      await tester.pumpAndSettle();
      expect(api.lastQuestion, isNull);
      expect(speaker.spoken.last, S.sttNoMatch);
      expect(earcons.played.last, Earcon.error);
    });

    testWidgets('đang nghe mà chạm bất kỳ: dừng nghe, app không đọc tên nút (để không lọt vào micro)', (tester) async {
      await pumpApp(tester);
      await moHoi(tester);
      stt.gate = Completer<SttResult>();
      await doubleTap(tester, label(S.mic));
      await tester.pump(const Duration(milliseconds: 100));
      expect(find.text(S.listeningShown), findsWidgets);
      final noiTruoc = speaker.spoken.length;
      await tester.tap(label(S.back));
      await tester.pumpAndSettle();
      expect(stt.stops, 1);
      expect(speaker.spoken.sublist(noiTruoc), isNot(contains(S.backSay)));
      expect(api.lastQuestion, FakeSpeechInput.macDinh, reason: 'dừng sớm vẫn lấy phần đã nghe');
    });

    testWidgets('dịch vụ nhận giọng không trả lời (mạng yếu): tự dừng, rồi huỷ và báo lỗi mạng, không treo', (
      tester,
    ) async {
      await pumpApp(tester);
      await moHoi(tester);
      stt.gate = Completer<SttResult>();
      stt.stopsComplete = false; // giả lập: dừng thu nhưng không bao giờ có kết quả
      await doubleTap(tester, label(S.mic));
      await tester.pump(AskScreen.nghiToiDa + const Duration(seconds: 1));
      expect(stt.stops, 1, reason: 'quá thời gian nghe thì tự dừng thu âm');
      await tester.pump(AskScreen.choKetQua);
      await tester.pumpAndSettle();
      expect(stt.cancels, 1);
      expect(speaker.spoken.last, S.sttNetwork);
      expect(find.text(S.listeningShown), findsNothing, reason: 'không còn kẹt ở Đang nghe');
      expect(api.lastQuestion, isNull);
    });

    testWidgets('máy không nhận được giọng nói: hiện ba câu gợi ý, hỏi bằng câu gợi ý', (tester) async {
      await pumpApp(tester, sttOk: false);
      await moHoi(tester);
      expect(speaker.spoken.last, S.askOpenNoStt);
      expect(label(S.mic), findsNothing);
      await doubleTap(tester, label(S.askSuggestions[1]));
      await tester.pumpAndSettle();
      expect(api.lastQuestion, S.askSuggestions[1]);
      expect(speaker.spoken.last, 'Trả lời.');
    });
  });

  group('Thư viện', () {
    testWidgets('mở sách, đọc trang đầu, sang trang sau, quay lại; đạt chuẩn trợ năng', (tester) async {
      final handle = tester.ensureSemantics();
      await pumpApp(tester);
      await doubleTap(tester, label(S.library));
      await tester.pumpAndSettle();
      expect(find.text(S.sampleBadge), findsOneWidget, reason: 'phải ghi rõ là bản mẫu');
      expect(find.text('Sách A'), findsOneWidget);
      await checkGuidelines(tester);

      await doubleTap(tester, label('Sách A'));
      await tester.pumpAndSettle();
      expect(
        speaker.spoken,
        containsAllInOrder(['Sách A. Trang 1. Trang một.', 'Nội dung trang một.', 'Câu thứ hai.']),
      );
      await checkGuidelines(tester);

      await doubleTap(tester, label(S.nextPage));
      await tester.pumpAndSettle();
      expect(speaker.spoken, containsAllInOrder(['Trang 2. Trang hai.', 'Nội dung trang hai.']));
      await doubleTap(tester, label(S.nextPage));
      await tester.pumpAndSettle();
      expect(speaker.spoken.last, S.lastPage);

      await doubleTap(tester, label(S.back));
      await tester.pumpAndSettle();
      expect(find.text('Sách B'), findsOneWidget);
      await doubleTap(tester, label(S.back));
      await tester.pumpAndSettle();
      expect(label(S.captureLabel), findsOneWidget);
      handle.dispose();
    });

    testWidgets('sách tải từ máy chủ: ghi "Máy chủ", lời giới thiệu nói rõ nguồn', (tester) async {
      await pumpApp(tester, library: const FakeLibrary(LibraryOrigin.server));
      await doubleTap(tester, label(S.library));
      await tester.pumpAndSettle();
      expect(find.text(S.badgeServer), findsOneWidget);
      expect(find.text(S.sampleBadge), findsNothing);
      expect(speaker.spoken, contains('${S.libraryCount(2)} ${S.originServer} ${S.backAtBottom}'));
    });

    testWidgets('mất mạng, nghe bản đã lưu: ghi "Đã lưu"', (tester) async {
      await pumpApp(tester, library: const FakeLibrary(LibraryOrigin.cache));
      await doubleTap(tester, label(S.library));
      await tester.pumpAndSettle();
      expect(find.text(S.badgeCache), findsOneWidget);
      expect(speaker.spoken, contains('${S.libraryCount(2)} ${S.originCache} ${S.backAtBottom}'));
    });
  });

  group('Cài đặt', () {
    testWidgets('đổi tốc độ đọc, tắt âm báo; đạt chuẩn trợ năng', (tester) async {
      final handle = tester.ensureSemantics();
      await pumpApp(tester);
      await doubleTap(tester, label(S.settings));
      await tester.pumpAndSettle();
      expect(speaker.spoken.last, S.settingsOpen);
      await checkGuidelines(tester);

      await doubleTap(tester, label('${S.speechRate}: Bình thường'));
      await tester.pumpAndSettle();
      expect(settings.speechRate, 0.65);
      expect(speaker.rate, 0.65);
      expect(speaker.spoken.last, startsWith('${S.speechRate}: Nhanh.'));

      await doubleTap(tester, label('${S.sound}: ${S.on}'));
      await tester.pumpAndSettle();
      expect(settings.soundOn, isFalse);
      expect(label('${S.sound}: ${S.off}'), findsOneWidget);
      handle.dispose();
    });

    testWidgets('UI-06: "Đọc ảnh có sẵn" về màn hình chính và đọc ảnh đã chọn', (tester) async {
      await pumpApp(tester);
      await doubleTap(tester, label(S.settings));
      await tester.pumpAndSettle();
      await doubleTap(tester, find.bySemanticsLabel(RegExp('^${S.pickImage}')));
      await tester.pumpAndSettle();
      expect(api.describeCalls, 1);
      expect(label(S.resultLabel), findsOneWidget);
    });

    testWidgets('UI-30: cài đặt cho người hỗ trợ có địa chỉ máy chủ; đạt chuẩn vùng chạm và tương phản', (
      tester,
    ) async {
      final handle = tester.ensureSemantics();
      await pumpApp(tester);
      await doubleTap(tester, label(S.settings));
      await tester.pumpAndSettle();
      await doubleTap(tester, find.bySemanticsLabel(RegExp('^${S.advanced}')));
      await tester.pumpAndSettle();
      expect(find.text(S.serverUrl), findsOneWidget);
      await expectLater(tester, meetsGuideline(androidTapTargetGuideline));
      await expectLater(tester, meetsGuideline(textContrastGuideline));
      handle.dispose();
    });
  });

  group('UI-23: không tràn chữ', () {
    Future<void> walkAllScreens(WidgetTester tester) async {
      await captureOnce(tester);
      await doubleTap(tester, label(S.ask));
      await tester.pumpAndSettle();
      await doubleTap(tester, label(S.mic));
      await tester.pumpAndSettle();
      await doubleTap(tester, label(S.back));
      await tester.pumpAndSettle();
      await doubleTap(tester, label(S.library));
      await tester.pumpAndSettle();
      await doubleTap(tester, label('Sách A'));
      await tester.pumpAndSettle();
      await doubleTap(tester, label(S.back));
      await tester.pumpAndSettle();
      await doubleTap(tester, label(S.back));
      await tester.pumpAndSettle();
      await doubleTap(tester, label(S.settings));
      await tester.pumpAndSettle();
      await doubleTap(tester, find.bySemanticsLabel(RegExp('^${S.advanced}')));
      await tester.pumpAndSettle();
    }

    testWidgets('phóng chữ hệ thống 200% trên mọi màn hình', (tester) async {
      tester.platformDispatcher.textScaleFactorTestValue = 2.0;
      addTearDown(tester.platformDispatcher.clearTextScaleFactorTestValue);
      await pumpApp(tester);
      await walkAllScreens(tester);
      expect(tester.takeException(), isNull);
    });

    testWidgets('màn hình nhỏ 360×640 trên mọi màn hình', (tester) async {
      await pumpApp(tester, size: const Size(720, 1280), ratio: 2);
      await walkAllScreens(tester);
      expect(tester.takeException(), isNull);
    });
  });
}
