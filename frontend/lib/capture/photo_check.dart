import 'dart:typed_data';
import 'dart:ui' as ui;

import 'frame_quality.dart';

/// Kiểm ảnh vừa chụp ngay trên máy, trước khi gửi đi.
///
/// Trả về lỗi quan trọng nhất, hoặc `null` nếu ảnh đạt **hoặc không kiểm được** (không chắc thì cho qua).
Future<CaptureIssue?> checkPhoto(Uint8List bytes, {int maxSide = 640}) async {
  ui.ImmutableBuffer? buffer;
  ui.ImageDescriptor? descriptor;
  ui.Codec? codec;
  ui.Image? image;
  try {
    buffer = await ui.ImmutableBuffer.fromUint8List(bytes);
    descriptor = await ui.ImageDescriptor.encoded(buffer);
    // Giải mã thẳng ở cỡ nhỏ cho nhanh; chỉ đặt một cạnh để giữ tỉ lệ.
    final wide = descriptor.width >= descriptor.height;
    final longSide = wide ? descriptor.width : descriptor.height;
    final target = longSide > maxSide ? maxSide : null;
    codec = await descriptor.instantiateCodec(
      targetWidth: wide ? target : null,
      targetHeight: wide ? null : target,
    );
    image = (await codec.getNextFrame()).image;
    final data = await image.toByteData(format: ui.ImageByteFormat.rawRgba);
    if (data == null) return null;
    return assess(measureGray(_toGray(data.buffer.asUint8List(), image.width, image.height)));
  } catch (_) {
    return null;
  } finally {
    image?.dispose();
    codec?.dispose();
    descriptor?.dispose();
    buffer?.dispose();
  }
}

/// RGBA sang xám theo trọng số ITU-R 601 (như chế độ "L" của thư viện ảnh trên máy chủ).
GrayImage _toGray(Uint8List rgba, int width, int height) {
  final out = Uint8List(width * height);
  for (var i = 0, j = 0; i < out.length; i++, j += 4) {
    out[i] = (rgba[j] * 299 + rgba[j + 1] * 587 + rgba[j + 2] * 114) ~/ 1000;
  }
  return GrayImage(out, width, height);
}
