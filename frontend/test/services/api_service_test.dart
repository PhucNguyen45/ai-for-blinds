import 'package:flutter_test/flutter_test.dart';
import 'package:ai_for_blinds/services/api_service.dart';

void main() {
  group('ApiService', () {
    setUp(() {
      // ApiService stores its config statically; reset before each test.
      ApiService.configure(
        baseUrl: 'http://192.168.1.100:8000',
        apiKey: 'sgbe_dev_key_2024',
      );
    });

    test('default baseUrl', () {
      final api = ApiService();
      expect(api.baseUrl, 'http://192.168.1.100:8000');
    });

    test('custom baseUrl', () {
      final api = ApiService(baseUrl: 'http://localhost:8000');
      expect(api.baseUrl, 'http://localhost:8000');
    });

    test('setBaseUrl trims trailing slash', () {
      final api = ApiService();
      api.setBaseUrl('http://test.com/');
      expect(api.baseUrl, 'http://test.com');
    });

    test('setApiKey', () {
      final api = ApiService();
      api.setApiKey('test-key');
      expect(api.apiKey, 'test-key');
    });

    test('configure applies shared static config across instances', () {
      ApiService.configure(baseUrl: 'http://shared:9000', apiKey: 'k');
      final a = ApiService();
      final b = ApiService();
      expect(a.baseUrl, 'http://shared:9000');
      expect(b.baseUrl, 'http://shared:9000');
      expect(b.apiKey, 'k');
    });

    test('configure ignores empty values', () {
      final api = ApiService();
      api.setBaseUrl('http://keep:8000');
      ApiService.configure(baseUrl: '', apiKey: '');
      expect(api.baseUrl, 'http://keep:8000');
    });
  });
}
