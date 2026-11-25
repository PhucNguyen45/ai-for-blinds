// Kiểm tra app đọc đúng phản hồi THẬT của backend (lưu trong test/fixtures,
// lấy từ backend nhánh dev chạy chế độ mock ngày 19/10/2026).
import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';

import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:sgbe/api/api_client.dart';
import 'package:sgbe/api/models.dart';
import 'package:sgbe/strings.dart';

String fixture(String name) => File('test/fixtures/$name').readAsStringSync();

http.Response jsonResponse(String body, int status) =>
    http.Response.bytes(utf8.encode(body), status, headers: {'content-type': 'application/json; charset=utf-8'});

void main() {
  final image = Uint8List.fromList([0xFF, 0xD8, 0xFF]);

  group('normalizeBaseUrl', () {
    test('thêm http:// và bỏ dấu / thừa', () {
      expect(ApiClient.normalizeBaseUrl(' 192.168.1.15:8000/ '), 'http://192.168.1.15:8000');
      expect(ApiClient.normalizeBaseUrl('https://a.b/'), 'https://a.b');
      expect(ApiClient.normalizeBaseUrl(''), '');
    });
  });

  group('describe', () {
    test('gửi multipart đúng tên trường và đọc kết quả thành công', () async {
      late http.Request sent;
      final api = ApiClient(
        'http://x',
        client: MockClient((req) async {
          sent = req;
          return jsonResponse(fixture('describe_ok.json'), 200);
        }),
      );

      final result = await api.describe(image, pageType: 'map');

      expect(sent.url.toString(), 'http://x/v1/describe');
      final body = latin1.decode(sent.bodyBytes);
      expect(body, contains('name="image"'));
      expect(body, contains('name="page_type"'));
      expect(body, contains('map'));
      final ok = result as ApiOk<DescribeResult>;
      expect(ok.value.imageId, 'b9b1d4985e464bbb');
      expect(ok.value.pageType, 'map');
      expect(ok.value.unreadable, isFalse);
      expect(ok.value.description, startsWith('Đây là dữ liệu thử'));
    });

    test('ảnh hỏng: đọc mã và câu báo lỗi của máy chủ', () async {
      final api = ApiClient(
        'http://x',
        client: MockClient((_) async => jsonResponse(fixture('describe_invalid_image.json'), 400)),
      );
      final fail = await api.describe(image) as ApiFail<DescribeResult>;
      expect(fail.code, 'INVALID_IMAGE');
      expect(fail.message, 'Ảnh gửi lên không đọc được. Bạn chụp lại nhé.');
    });

    test('máy chủ trả HTML thay vì JSON: báo dữ liệu lạ', () async {
      final api = ApiClient('http://x', client: MockClient((_) async => http.Response('<h1>502</h1>', 502)));
      final fail = await api.describe(image) as ApiFail<DescribeResult>;
      expect(fail.code, 'BAD_RESPONSE');
      expect(fail.message, S.errBadData);
    });

    test('mất mạng: báo không kết nối được', () async {
      final api = ApiClient('http://x', client: MockClient((_) async => throw http.ClientException('refused')));
      final fail = await api.describe(image) as ApiFail<DescribeResult>;
      expect(fail.code, 'NETWORK');
      expect(fail.message, S.errOffline);
    });

    test('quá giờ: báo máy chủ trả lời quá lâu', () async {
      final api = ApiClient(
        'http://x',
        slowTimeout: const Duration(milliseconds: 50),
        client: MockClient((_) => Completer<http.Response>().future),
      );
      final fail = await api.describe(image) as ApiFail<DescribeResult>;
      expect(fail.code, 'TIMEOUT');
      expect(fail.message, S.errTimeout);
    });

    test('chưa có địa chỉ máy chủ: không gọi mạng', () async {
      var called = false;
      final api = ApiClient(
        '',
        client: MockClient((_) async {
          called = true;
          return http.Response('', 200);
        }),
      );
      expect(await api.describe(image), isA<ApiFail<DescribeResult>>());
      expect(called, isFalse);
    });
  });

  group('ask', () {
    test('gửi image_id, câu hỏi và lịch sử; đọc câu trả lời', () async {
      late Map<String, dynamic> body;
      final api = ApiClient(
        'http://x',
        client: MockClient((req) async {
          body = jsonDecode(utf8.decode(req.bodyBytes)) as Map<String, dynamic>;
          return jsonResponse(fixture('ask_ok.json'), 200);
        }),
      );

      final ok =
          await api.ask('b9b1d4985e464bbb', 'Có mấy tỉnh?', history: const [AskTurn('Đây là gì?', 'Một lược đồ.')])
              as ApiOk<AskResult>;

      expect(body['image_id'], 'b9b1d4985e464bbb');
      expect(body['question'], 'Có mấy tỉnh?');
      expect(body['history'], [
        {'question': 'Đây là gì?', 'answer': 'Một lược đồ.'},
      ]);
      expect(ok.value.answer, contains('Có mấy tỉnh?'));
    });

    test('ảnh không còn trên máy chủ: IMAGE_NOT_FOUND', () async {
      final api = ApiClient(
        'http://x',
        client: MockClient((_) async => jsonResponse(fixture('ask_image_not_found.json'), 404)),
      );
      final fail = await api.ask('0000000000000000', 'a') as ApiFail<AskResult>;
      expect(fail.code, 'IMAGE_NOT_FOUND');
    });
  });

  test('health: nhận ra máy chủ đang ở chế độ thử', () async {
    final api = ApiClient('http://x', client: MockClient((_) async => jsonResponse(fixture('health.json'), 200)));
    final ok = await api.health() as ApiOk<HealthInfo>;
    expect(ok.value.isMock, isTrue);
    expect(ok.value.sttMode, 'mock');
  });
}
