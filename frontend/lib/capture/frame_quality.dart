/// Đo chất lượng khung hình ngay trên máy, không cần mạng hay mô hình.
///
/// Cách đo theo cổng của máy chủ (`ai/capture/quality.py`): ảnh xám thu về cạnh dài 640, độ sáng trung bình,
/// phân vị 95, độ lệch chuẩn và phương sai bộ lọc Laplace. Cách thu nhỏ ở đây khác thư viện của máy chủ nên
/// số đo không trùng khít; **ngưỡng chưa được hiệu chỉnh trên điện thoại thật**.
///
/// Nguyên tắc: chỉ báo khi hỏng rõ, không chắc thì cho ảnh đi tiếp (cổng của máy chủ và mô hình vẫn còn phía sau).
library;

import 'dart:math' as math;
import 'dart:typed_data';

enum CaptureIssue { dark, glare, blur, shake }

/// Ảnh xám 8 bit, xếp theo hàng, không có phần đệm.
class GrayImage {
  const GrayImage(this.pixels, this.width, this.height);
  final Uint8List pixels;
  final int width;
  final int height;
}

class FrameStats {
  const FrameStats({required this.mean, required this.p95, required this.std, required this.sharpness});
  final double mean;
  final int p95;
  final double std;

  /// Phương sai đáp ứng Laplace: càng nhỏ càng ít nét.
  final double sharpness;
}

class FrameThresholds {
  const FrameThresholds({
    this.darkMean = 30,
    this.darkP95 = 40,
    this.darkStd = 20,
    this.blurSharpness = 10,
    this.overexposedMean = 235,
    this.overexposedStd = 15,
    this.shakeDifference = 12,
  });

  /// Tối khi cả vùng sáng nhất vẫn dưới [darkP95]...
  final int darkP95;

  /// ...hoặc trung bình dưới [darkMean] VÀ gần như không tương phản (dưới [darkStd]).
  /// Máy chủ chỉ xét trung bình, nên dễ chặn nhầm hình nền đen có nét sáng.
  final double darkMean;
  final double darkStd;

  final double blurSharpness;
  final double overexposedMean;
  final double overexposedStd;

  /// Chênh lệch trung bình giữa hai khung liên tiếp (0–255) từ mức này trở lên là máy đang rung.
  final double shakeDifference;
}

/// Thu mặt phẳng sáng (kênh Y của khung camera, mỗi hàng có thể có byte đệm) về cạnh dài tối đa [maxSide],
/// lấy trung bình từng ô.
GrayImage downscaleLuma(
  Uint8List plane, {
  required int width,
  required int height,
  required int rowStride,
  int maxSide = 640,
}) {
  final longSide = math.max(width, height);
  final scale = longSide <= maxSide ? 1.0 : maxSide / longSide;
  final w = math.max(1, (width * scale).round());
  final h = math.max(1, (height * scale).round());
  final out = Uint8List(w * h);
  for (var y = 0; y < h; y++) {
    final y0 = y * height ~/ h;
    final y1 = math.max(y0 + 1, (y + 1) * height ~/ h);
    for (var x = 0; x < w; x++) {
      final x0 = x * width ~/ w;
      final x1 = math.max(x0 + 1, (x + 1) * width ~/ w);
      var sum = 0;
      for (var sy = y0; sy < y1; sy++) {
        final row = sy * rowStride;
        for (var sx = x0; sx < x1; sx++) {
          sum += plane[row + sx];
        }
      }
      out[y * w + x] = (sum / ((y1 - y0) * (x1 - x0))).round();
    }
  }
  return GrayImage(out, w, h);
}

FrameStats measureGray(GrayImage image) {
  final px = image.pixels;
  final histogram = List<int>.filled(256, 0);
  for (final v in px) {
    histogram[v]++;
  }
  var sum = 0.0, squares = 0.0;
  for (var v = 0; v < 256; v++) {
    sum += v * histogram[v];
    squares += v * v * histogram[v];
  }
  final mean = sum / px.length;
  final std = math.sqrt(math.max(0, squares / px.length - mean * mean));

  var p95 = 255;
  var seen = 0;
  for (var v = 0; v < 256; v++) {
    seen += histogram[v];
    if (seen >= 0.95 * px.length) {
      p95 = v;
      break;
    }
  }

  // Laplace 4 láng giềng, cộng 128 rồi cắt về 0–255 như bộ lọc của máy chủ; bỏ viền 1 điểm.
  final w = image.width, h = image.height;
  var n = 0;
  var lapSum = 0.0, lapSquares = 0.0;
  for (var y = 1; y < h - 1; y++) {
    for (var x = 1; x < w - 1; x++) {
      final i = y * w + x;
      final v = (px[i - w] + px[i - 1] + px[i + 1] + px[i + w] - 4 * px[i] + 128).clamp(0, 255);
      lapSum += v;
      lapSquares += v * v;
      n++;
    }
  }
  final lapMean = n == 0 ? 0.0 : lapSum / n;
  final sharpness = n == 0 ? 0.0 : math.max(0.0, lapSquares / n - lapMean * lapMean);

  return FrameStats(mean: mean, p95: p95, std: std, sharpness: sharpness);
}

/// Lỗi quan trọng nhất của một khung, hoặc `null` nếu đạt. Không xét rung (cần hai khung).
CaptureIssue? assess(FrameStats s, [FrameThresholds t = const FrameThresholds()]) {
  if (s.p95 < t.darkP95 || (s.mean < t.darkMean && s.std < t.darkStd)) return CaptureIssue.dark;
  if (s.mean > t.overexposedMean && s.std < t.overexposedStd) return CaptureIssue.glare;
  if (s.sharpness < t.blurSharpness) return CaptureIssue.blur;
  return null;
}

/// Chênh lệch sáng trung bình giữa hai khung cùng cỡ; khác cỡ thì trả 0 (không so được).
double frameDifference(GrayImage a, GrayImage b) {
  if (a.width != b.width || a.height != b.height || a.pixels.isEmpty) return 0;
  var sum = 0;
  for (var i = 0; i < a.pixels.length; i++) {
    sum += (a.pixels[i] - b.pixels[i]).abs();
  }
  return sum / a.pixels.length;
}
