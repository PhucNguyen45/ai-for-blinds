import 'dart:typed_data';
import 'dart:ui' as ui;

import 'package:flutter_test/flutter_test.dart';
import 'package:sgbe/capture/frame_quality.dart';
import 'package:sgbe/capture/photo_check.dart';

/// Ảnh xám [w]×[h], mỗi điểm lấy từ [at].
GrayImage gray(int w, int h, int Function(int x, int y) at) {
  final px = Uint8List(w * h);
  for (var y = 0; y < h; y++) {
    for (var x = 0; x < w; x++) {
      px[y * w + x] = at(x, y);
    }
  }
  return GrayImage(px, w, h);
}

/// Giả trang chữ: nền [paper], các ô "chữ" màu [ink] có cạnh sắc.
GrayImage page({int paper = 220, int ink = 30, int w = 160, int h = 120}) =>
    gray(w, h, (x, y) => (x ~/ 4).isEven && (y ~/ 6).isEven ? ink : paper);

CaptureIssue? judge(GrayImage g) => assess(measureGray(g));

Future<Uint8List> png(void Function(ui.Canvas canvas) draw, {int w = 320, int h = 240}) async {
  final recorder = ui.PictureRecorder();
  draw(ui.Canvas(recorder));
  final image = await recorder.endRecording().toImage(w, h);
  final data = await image.toByteData(format: ui.ImageByteFormat.png);
  return data!.buffer.asUint8List();
}

void main() {
  group('đánh giá khung hình', () {
    test('trang sáng, chữ sắc: đạt', () => expect(judge(page()), isNull));

    test('gần như đen: tối', () => expect(judge(gray(160, 120, (_, _) => 8)), CaptureIssue.dark));

    test('cả trang thiếu sáng, không có vùng nào sáng: tối', () {
      expect(judge(page(paper: 34, ink: 10)), CaptureIssue.dark);
    });

    test('nền đen nhưng chữ sáng, tương phản cao (hình vũ trụ, bảng đen): đạt', () {
      // trung bình dưới 30 nhưng nét sáng rõ: không được coi là ảnh tối
      final g = gray(160, 120, (x, y) => (x % 12 < 2 && y % 10 < 6) ? 230 : 4);
      expect(measureGray(g).mean, lessThan(30));
      expect(judge(g), isNull);
    });

    test('trắng xóa, không tương phản: chói', () => expect(judge(gray(160, 120, (_, _) => 250)), CaptureIssue.glare));

    test('chuyển sáng tối rất mượt, không cạnh nào: mờ', () {
      expect(judge(gray(160, 120, (x, _) => 60 + x)), CaptureIssue.blur);
    });
  });

  group('thu nhỏ mặt phẳng sáng', () {
    test('bỏ phần đệm cuối hàng và thu cạnh dài về giới hạn', () {
      // 8×4 điểm, mỗi hàng đệm thêm 2 byte rác (255)
      final plane = Uint8List(10 * 4)..fillRange(0, 40, 255);
      for (var y = 0; y < 4; y++) {
        plane.fillRange(y * 10, y * 10 + 8, 100);
      }
      final g = downscaleLuma(plane, width: 8, height: 4, rowStride: 10, maxSide: 4);
      expect((g.width, g.height), (4, 2));
      expect(g.pixels, everyElement(100));
    });

    test('ảnh nhỏ hơn giới hạn thì giữ nguyên cỡ', () {
      final g = downscaleLuma(Uint8List(12)..fillRange(0, 12, 7), width: 4, height: 3, rowStride: 4, maxSide: 640);
      expect((g.width, g.height), (4, 3));
    });
  });

  group('độ rung giữa hai khung', () {
    test('hai khung giống nhau: không rung', () => expect(frameDifference(page(), page()), 0));

    test('khung bị dịch đi: khác nhiều hơn ngưỡng rung', () {
      final moved = gray(160, 120, (x, y) => ((x + 4) ~/ 4).isEven && (y ~/ 6).isEven ? 30 : 220);
      expect(frameDifference(page(), moved), greaterThan(const FrameThresholds().shakeDifference));
    });

    test('khác cỡ thì không so', () => expect(frameDifference(page(), page(w: 80)), 0));
  });

  group('kiểm ảnh vừa chụp', () {
    testWidgets('ảnh đen: tối', (tester) async {
      final issue = await tester.runAsync(() async {
        final bytes = await png((c) => c.drawColor(const ui.Color(0xFF050505), ui.BlendMode.src));
        return checkPhoto(bytes);
      });
      expect(issue, CaptureIssue.dark);
    });

    testWidgets('ảnh trang có nét sắc: đạt', (tester) async {
      final issue = await tester.runAsync(() async {
        final bytes = await png((c) {
          c.drawColor(const ui.Color(0xFFDDDDDD), ui.BlendMode.src);
          final ink = ui.Paint()..color = const ui.Color(0xFF202020);
          for (var x = 10.0; x < 300; x += 14) {
            for (var y = 10.0; y < 220; y += 18) {
              c.drawRect(ui.Rect.fromLTWH(x, y, 7, 9), ink);
            }
          }
        });
        return checkPhoto(bytes);
      });
      expect(issue, isNull);
    });

    testWidgets('dữ liệu không phải ảnh: không chắc thì cho qua', (tester) async {
      final issue = await tester.runAsync(() => checkPhoto(Uint8List.fromList([1, 2, 3])));
      expect(issue, isNull);
    });
  });
}
