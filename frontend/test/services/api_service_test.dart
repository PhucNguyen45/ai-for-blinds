import 'package:flutter_test/flutter_test.dart';
import 'package:ai_for_blinds/services/api_service.dart';

void main() {
  group('ApiService', () {
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
      // No getter for apiKey, just verify setter works
    });
  });
}
