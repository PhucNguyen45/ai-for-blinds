// App đọc được kết quả theo hợp đồng AI v0.1 của Phúc (ai/contract/examples trên nhánh phuc),
// cả dạng gốc lẫn khi backend bọc trong {data, error}.
import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';

import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:sgbe/api/api_client.dart';
import 'package:sgbe/api/models.dart';
import 'package:sgbe/reader/reader_controller.dart';
import 'package:sgbe/strings.dart';

import 'fakes.dart';

String example(String name) => File('test/fixtures/contract_v01/$name.json').readAsStringSync();

ApiResult<DescribeResult> parse(String body) =>
    ApiClient.parseEnvelope(utf8.encode(body), (d) => DescribeResult.fromJson(d as Map<String, dynamic>));

String wrap(String body) => '{"data": $body, "error": null}';

void main() {
  for (final (label, transform) in [('dạng gốc', (String b) => b), ('bọc {data, error}', wrap)]) {
    group(label, () {
      test('ok: đọc lời diễn giải, loại hình, cho hỏi tiếp', () {
        final r = (parse(transform(example('ok_bar_chart'))) as ApiOk<DescribeResult>).value;
        expect(r.description, startsWith('Biểu đồ có năm cột'));
        expect(r.summary, startsWith('Biểu đồ cột về số sách'));
        expect(r.pageType, 'bar_chart');
        expect(r.status, 'ok');
        expect(r.unreadable, isFalse);
        expect(r.canAsk, isTrue);
        expect(r.imageId, 'img-001');
        expect(r.latencyMs, 3400);
        expect(r.model, 'example/model');
      });

      test('unreadable: nói câu giải thích, đánh dấu không đọc được, không cho hỏi tiếp', () {
        final r = (parse(transform(example('unreadable_blurred'))) as ApiOk<DescribeResult>).value;
        expect(r.description, startsWith('Ảnh quá mờ'));
        expect(r.unreadable, isTrue);
        expect(r.status, 'unreadable');
        expect(r.canAsk, isFalse);
      });

      test('partial: đọc phần diễn giải có được và đánh dấu thiếu', () {
        final r = (parse(transform(example('partial_truncated'))) as ApiOk<DescribeResult>).value;
        expect(r.description, startsWith('Bảng có năm hàng'));
        expect(r.unreadable, isTrue);
        expect(r.status, 'partial');
      });

      test('error: thành lỗi, đọc câu báo của module AI', () {
        final f = parse(transform(example('error_timeout'))) as ApiFail<DescribeResult>;
        expect(f.code, 'timeout');
        expect(f.message, 'Hết thời gian chờ mô hình.');
      });
    });
  }

  test('ApiClient gọi máy chủ trả hợp đồng v0.1 dạng gốc vẫn chạy', () async {
    final api = ApiClient('http://x',
        client: MockClient((_) async => http.Response.bytes(utf8.encode(example('ok_bar_chart')), 200)));
    final r = await api.describe(Uint8List.fromList([1, 2, 3]));
    expect((r as ApiOk<DescribeResult>).value.pageType, 'bar_chart');
  });

  group('lời nói theo trạng thái', () {
    Future<String> spokenFor(String name) async {
      final api = FakeApi(next: parse(example(name)));
      final speaker = FakeSpeaker();
      final c = ReaderController(api: () => api, speaker: speaker, earcons: FakeEarcons());
      await c.describe(Uint8List.fromList([1]));
      return speaker.spoken.last;
    }

    test('ảnh hỏng hẳn: giải thích rồi hướng dẫn chụp lại, không lặp "có chỗ không đọc được"', () async {
      final s = await spokenFor('unreadable_blurred');
      expect(s, endsWith(S.retakeHint));
      expect(s, isNot(contains(S.unreadableHint)));
    });

    test('ảnh bị cắt một phần: đọc phần có được rồi báo có chỗ không đọc được', () async {
      final s = await spokenFor('partial_truncated');
      expect(s, startsWith('Bảng có năm hàng'));
      expect(s, endsWith(S.unreadableHint));
    });

    test('lỗi: đọc nguyên câu báo lỗi', () async {
      final s = await spokenFor('error_timeout');
      expect(s, 'Hết thời gian chờ mô hình.');
    });
  });
}
