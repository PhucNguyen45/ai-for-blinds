import 'dart:typed_data';

import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:sgbe/capture/frame_quality.dart';
import 'package:sgbe/reader/reader_controller.dart';
import 'package:sgbe/services/earcons.dart';
import 'package:sgbe/services/settings_store.dart';
import 'package:sgbe/strings.dart';

import 'fakes.dart';

void main() {
  late FakeApi api;
  late FakeSpeaker speaker;
  late FakeEarcons earcons;
  late List<String> events;
  late List<CaptureIssue?> verdicts; // kết quả kiểm cho các lần chụp, lấy lần lượt
  var guideOn = true;
  late ReaderController c;
  final image = Uint8List.fromList([1, 2, 3]);

  setUp(() {
    api = FakeApi();
    speaker = FakeSpeaker();
    earcons = FakeEarcons();
    events = [];
    verdicts = [];
    guideOn = true;
    c = ReaderController(
      api: () => api,
      speaker: speaker,
      earcons: earcons,
      photoCheck: (_) async => verdicts.isEmpty ? null : verdicts.removeAt(0),
      guideOn: () => guideOn,
      onCaptureEvent: events.add,
    );
  });

  test('ảnh hỏng rõ: không gửi đi, báo lý do và mời chụp lại', () async {
    verdicts = [CaptureIssue.dark];
    await c.describe(image, fromCamera: true);

    expect(api.describeCalls, 0);
    expect(speaker.spoken.last, S.retake(CaptureIssue.dark));
    expect(earcons.played.last, Earcon.error);
    expect(c.status, ReaderStatus.error);
    expect(await c.primaryAction(), isTrue);
    expect(events, ['shot', 'phone_dark', 'phone_blocked']);
  });

  test('chụp lại vẫn bị đánh hỏng: gửi đi, không khóa người dùng', () async {
    verdicts = [CaptureIssue.dark, CaptureIssue.dark];
    await c.describe(image, fromCamera: true);
    await c.describe(image, fromCamera: true);

    expect(api.describeCalls, 1);
    expect(events, ['shot', 'phone_dark', 'phone_blocked', 'shot', 'phone_dark', 'server_ok']);
  });

  test('sau một lần được gửi, ảnh hỏng kế tiếp lại bị giữ', () async {
    verdicts = [CaptureIssue.blur, null, CaptureIssue.blur];
    for (var i = 0; i < 3; i++) {
      await c.describe(image, fromCamera: true);
    }
    expect(api.describeCalls, 1);
  });

  test('tắt hướng dẫn: vẫn đếm lỗi để làm mốc so sánh nhưng không giữ ảnh', () async {
    guideOn = false;
    verdicts = [CaptureIssue.blur];
    await c.describe(image, fromCamera: true);

    expect(api.describeCalls, 1);
    expect(events, ['shot', 'phone_blur', 'server_ok']);
  });

  test('ảnh chọn từ thư viện máy: không kiểm, không đếm', () async {
    verdicts = [CaptureIssue.dark];
    await c.describe(image);

    expect(api.describeCalls, 1);
    expect(events, isEmpty);
  });

  test('máy chủ báo cả ảnh không đọc được: đếm là hỏng phía máy chủ', () async {
    api.next = FakeApi.ok(description: 'Ảnh mờ quá, bạn chụp lại nhé.', unreadable: true, status: 'unreadable');
    await c.describe(image, fromCamera: true);
    expect(events, ['shot', 'server_unreadable']);
  });

  test('bộ kiểm bị lỗi: vẫn gửi ảnh đi', () async {
    final broken = ReaderController(
      api: () => api,
      speaker: speaker,
      earcons: earcons,
      photoCheck: (_) async => throw StateError('hỏng'),
    );
    await broken.describe(image, fromCamera: true);
    expect(api.describeCalls, 1);
  });

  test('đang kiểm ảnh thì bấm tiếp không gửi trùng', () async {
    final first = c.describe(image, fromCamera: true);
    expect(c.busy, isTrue);
    await c.describe(image, fromCamera: true);
    await first;
    expect(api.describeCalls, 1);
  });

  group('lưu trên máy', () {
    test('hướng dẫn chụp mặc định bật; số liệu chỉ là số đếm, cộng dồn', () async {
      SharedPreferences.setMockInitialValues({});
      final s = await SettingsStore.load();
      expect(s.captureGuideOn, isTrue);
      expect(s.captureStats, isEmpty);

      await s.countCapture('shot');
      await s.countCapture('shot');
      await s.countCapture('phone_dark');
      expect(s.captureStats, {'shot': 2, 'phone_dark': 1});

      await s.setCaptureGuideOn(false);
      expect(s.captureGuideOn, isFalse);
    });

    test('câu tóm tắt số liệu', () {
      expect(S.captureStatsText(const {}), S.captureStatsEmpty);
      final text = S.captureStatsText(const {'shot': 10, 'phone_dark': 2, 'phone_blur': 1, 'server_unreadable': 1});
      expect(text, contains('10 lần chụp'));
      expect(text, contains('tối 2'));
      expect(text, contains('mờ 1'));
      expect(text, contains('máy chủ không đọc được 1'));
    });
  });
}
