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

      test('partial: lời diễn giải bị cắt ngắn, KHÔNG phải ảnh hỏng, vẫn hỏi tiếp được', () {
        final r = (parse(transform(example('partial_truncated'))) as ApiOk<DescribeResult>).value;
        expect(r.description, startsWith('Bảng có năm hàng'));
        expect(r.unreadable, isFalse);
        expect(r.truncated, isTrue);
        expect(r.status, 'partial');
        expect(r.canAsk, isTrue);
      });

      test('B0 để question_answering_ready=false (dành cho B1): vẫn hỏi tiếp được', () {
        final body = (jsonDecode(example('ok_bar_chart')) as Map<String, dynamic>)
          ..['question_answering_ready'] = false;
        final r = (parse(transform(jsonEncode(body))) as ApiOk<DescribeResult>).value;
        expect(r.canAsk, isTrue);
      });

      test('cổng chất lượng ảnh chặn: câu hướng dẫn chụp lại, không cho hỏi tiếp', () {
        final r = (parse(transform(example('unreadable_capture_gate'))) as ApiOk<DescribeResult>).value;
        expect(r.description, startsWith('Ảnh quá tối'));
        expect(r.wholeUnreadable, isTrue);
        expect(r.uncertainties, ['capture_gate:dark']);
        expect(r.canAsk, isFalse);
      });

      test('trả lời câu hỏi (AnswerResult): đọc answer_vi', () {
        final r = ApiClient.parseEnvelope(
          utf8.encode(transform(example('answer_ok'))),
          (d) => AskResult.fromJson(d as Map<String, dynamic>),
        );
        final a = (r as ApiOk<AskResult>).value;
        expect(a.answer, 'Cột Thứ Hai cao nhất, với bốn mươi quyển.');
        expect(a.imageId, 'img-001');
        expect(a.latencyMs, 3400);
      });

      test('trả lời lỗi: thành lỗi, đọc câu báo', () {
        final r = ApiClient.parseEnvelope(
          utf8.encode(transform(example('answer_error_timeout'))),
          (d) => AskResult.fromJson(d as Map<String, dynamic>),
        );
        expect((r as ApiFail<AskResult>).message, 'Hết thời gian chờ mô hình.');
      });

      test('error: thành lỗi, đọc câu báo của module AI', () {
        final f = parse(transform(example('error_timeout'))) as ApiFail<DescribeResult>;
        expect(f.code, 'timeout');
        expect(f.message, 'Hết thời gian chờ mô hình.');
      });
    });
  }

  test('ApiClient gọi máy chủ trả hợp đồng v0.1 dạng gốc vẫn chạy', () async {
    final api = ApiClient(
      'http://x',
      client: MockClient((_) async => http.Response.bytes(utf8.encode(example('ok_bar_chart')), 200)),
    );
    final r = await api.describe(Uint8List.fromList([1, 2, 3]));
    expect((r as ApiOk<DescribeResult>).value.pageType, 'bar_chart');
  });

  group('lời nói theo trạng thái', () {
    Future<String> spokenFor(String name) async {
      final api = FakeApi(next: parse(example(name)));
      final speaker = FakeSpeaker();
      final c = ReaderController(api: () => api, speaker: speaker, earcons: FakeEarcons());
      await c.describe(Uint8List.fromList([1]));
      // Câu đầu là "Đang đọc trang"; mô tả được đọc từng câu nên ghép lại để so.
      return speaker.spoken.skip(1).join(' ');
    }

    test('ảnh hỏng hẳn: giải thích rồi hướng dẫn chụp lại, không lặp "có chỗ không đọc được"', () async {
      final s = await spokenFor('unreadable_blurred');
      expect(s, endsWith(S.retakeHint));
      expect(s, isNot(contains(S.unreadableHint)));
    });

    test('lời diễn giải bị cắt ngắn: đọc phần có được rồi gợi ý hỏi thêm', () async {
      final s = await spokenFor('partial_truncated');
      expect(s, startsWith('Bảng có năm hàng'));
      expect(s, endsWith(S.truncatedHint));
      expect(s, isNot(contains(S.unreadableHint)));
    });

    test('cổng chất lượng ảnh đã hướng dẫn chụp lại: không nhắc lại lần hai', () async {
      final s = await spokenFor('unreadable_capture_gate');
      expect(s, contains('chụp lại nhé'));
      expect(s, isNot(contains(S.retakeHint)));
    });

    test('lỗi: đọc nguyên câu báo lỗi', () async {
      final s = await spokenFor('error_timeout');
      expect(s, 'Hết thời gian chờ mô hình.');
    });
  });
}
