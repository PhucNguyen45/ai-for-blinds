// Gọi THẲNG máy chủ đang chạy để chắc máy chủ chấp nhận đúng dạng app gửi lên
// (MockClient không kiểm được phần này).
//
// Bỏ qua mặc định. Chạy khi có máy chủ:
//   SGBE_LIVE=http://127.0.0.1:8000 flutter test test/live_backend_test.dart
// (PowerShell: $env:SGBE_LIVE="http://127.0.0.1:8000"; flutter test test/live_backend_test.dart)
import 'dart:io';
import 'dart:typed_data';

import 'package:flutter_test/flutter_test.dart';
import 'package:sgbe/api/api_client.dart';
import 'package:sgbe/api/models.dart';

void main() {
  final base = Platform.environment['SGBE_LIVE'];
  final skip = base == null ? 'Đặt SGBE_LIVE=<địa chỉ máy chủ> để chạy' : null;

  // Ảnh PNG 1×1 hợp lệ — đủ để máy chủ mở được ảnh.
  final png = Uint8List.fromList(const [
    0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A, 0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52, //
    0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01, 0x08, 0x02, 0x00, 0x00, 0x00, 0x90, 0x77, 0x53,
    0xDE, 0x00, 0x00, 0x00, 0x0C, 0x49, 0x44, 0x41, 0x54, 0x08, 0xD7, 0x63, 0xF8, 0xCF, 0xC0, 0x00,
    0x00, 0x03, 0x01, 0x01, 0x00, 0x18, 0xDD, 0x8D, 0xB0, 0x00, 0x00, 0x00, 0x00, 0x49, 0x45, 0x4E,
    0x44, 0xAE, 0x42, 0x60, 0x82,
  ]);

  test('health', () async {
    final r = await ApiClient(base!).health();
    expect(r, isA<ApiOk<HealthInfo>>());
  }, skip: skip);

  test('describe rồi ask trên cùng image_id', () async {
    final api = ApiClient(base!);
    final d = await api.describe(png, pageType: 'figure');
    expect(d, isA<ApiOk<DescribeResult>>(), reason: d is ApiFail ? (d as ApiFail).message : '');
    final imageId = (d as ApiOk<DescribeResult>).value.imageId;
    expect(imageId, matches(RegExp(r'^[0-9a-f]{16}$')));

    final a = await api.ask(imageId, 'Có gì trong ảnh?', history: const [AskTurn('Đây là gì?', 'Một ảnh nhỏ.')]);
    expect(a, isA<ApiOk<AskResult>>(), reason: a is ApiFail ? (a as ApiFail).message : '');
  }, skip: skip);

  test('ảnh hỏng thì máy chủ trả INVALID_IMAGE và app đọc được câu báo', () async {
    final d = await ApiClient(base!).describe(Uint8List.fromList([1, 2, 3]));
    final fail = d as ApiFail<DescribeResult>;
    expect(fail.code, 'INVALID_IMAGE');
    expect(fail.message, isNotEmpty);
  }, skip: skip);
}
