import 'dart:typed_data';

import 'package:flutter_test/flutter_test.dart';
import 'package:sgbe/capture/frame_quality.dart';
import 'package:sgbe/capture/live_guide.dart';

void main() {
  late LiveGuide guide;
  setUp(() => guide = LiveGuide(persistFrames: 3, repeatAfter: const Duration(seconds: 6)));

  /// Đưa lần lượt các khung (mỗi khung cách nhau 400 ms) và gom các tín hiệu phát ra.
  List<GuideSignal> feed(List<CaptureIssue?> frames, {int startMs = 0}) => [
    for (var i = 0; i < frames.length; i++)
      ?guide.onFrame(frames[i], Duration(milliseconds: startMs + i * 400)),
  ];

  test('lỗi thoáng qua thì không nhắc', () {
    expect(feed([CaptureIssue.dark, CaptureIssue.dark, null, CaptureIssue.dark]), isEmpty);
  });

  test('lỗi kéo dài đủ số khung thì nhắc đúng một lần', () {
    expect(feed(List.filled(8, CaptureIssue.dark)), [const GuideSignal.hint(CaptureIssue.dark)]);
  });

  test('lỗi còn mãi thì chỉ nhắc lại sau khoảng nghỉ', () {
    // 20 khung × 400 ms = 7,6 s: nhắc lúc 0,8 s và 6,8 s
    expect(feed(List.filled(20, CaptureIssue.dark)), hasLength(2));
  });

  test('đổi sang lỗi khác kéo dài thì nhắc lỗi mới', () {
    final signals = feed([...List.filled(3, CaptureIssue.dark), ...List.filled(3, CaptureIssue.shake)]);
    expect(signals, [const GuideSignal.hint(CaptureIssue.dark), const GuideSignal.hint(CaptureIssue.shake)]);
  });

  test('khung đạt ổn định: báo sẵn sàng một lần', () {
    expect(feed(List.filled(10, null)), [const GuideSignal.ready()]);
  });

  test('hỏng rồi đạt lại: báo sẵn sàng thêm lần nữa', () {
    final signals = feed([...List.filled(3, null), ...List.filled(3, CaptureIssue.blur), ...List.filled(3, null)]);
    expect(signals, [
      const GuideSignal.ready(),
      const GuideSignal.hint(CaptureIssue.blur),
      const GuideSignal.ready(),
    ]);
  });

  test('chập chờn một khung không làm báo sẵn sàng liên tục', () {
    final signals = feed([...List.filled(3, null), CaptureIssue.shake, ...List.filled(5, null)]);
    expect(signals, [const GuideSignal.ready()]);
  });

  test('reset thì bắt đầu đếm lại', () {
    feed(List.filled(2, CaptureIssue.dark));
    guide.reset();
    expect(feed(List.filled(2, CaptureIssue.dark), startMs: 800), isEmpty);
  });

  group('phân tích chuỗi khung hình', () {
    GrayImage flat(int v) => GrayImage(Uint8List(64 * 48)..fillRange(0, 64 * 48, v), 64, 48);

    GrayImage stripes(int shift) {
      final px = Uint8List(64 * 48);
      for (var i = 0; i < px.length; i++) {
        px[i] = (((i % 64) + shift) ~/ 4).isEven ? 30 : 220;
      }
      return GrayImage(px, 64, 48);
    }

    test('khung tối báo tối, kể cả khi đang rung: tối quan trọng hơn', () {
      final analyzer = FrameAnalyzer();
      analyzer.analyze(stripes(0));
      expect(analyzer.analyze(flat(5)), CaptureIssue.dark);
    });

    test('máy đang di chuyển: rung', () {
      final analyzer = FrameAnalyzer();
      expect(analyzer.analyze(stripes(0)), isNull);
      expect(analyzer.analyze(stripes(4)), CaptureIssue.shake);
      expect(analyzer.analyze(stripes(4)), isNull);
    });
  });
}
