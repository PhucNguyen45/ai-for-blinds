import 'package:flutter_test/flutter_test.dart';
import 'package:ai_for_blinds/services/voice_command_service.dart';

void main() {
  group('VoiceCommandService.parseCommand', () {
    final service = VoiceCommandService();

    test('maps navigation phrases to commands', () {
      expect(service.parseCommand('về trang chủ'), 'home');
      expect(service.parseCommand('trang chủ'), 'home');
      expect(service.parseCommand('home'), 'home');
      expect(service.parseCommand('quét tài liệu'), 'scanner');
      expect(service.parseCommand('quét'), 'scanner');
      expect(service.parseCommand('chụp ảnh'), 'scanner');
      expect(service.parseCommand('hỏi đáp'), 'voice-qa');
      expect(service.parseCommand('đặt câu hỏi'), 'voice-qa');
      expect(service.parseCommand('tìm kiếm'), 'search');
      expect(service.parseCommand('ôn tập'), 'review');
      expect(service.parseCommand('cài đặt'), 'settings');
    });

    test('maps control phrases to commands', () {
      expect(service.parseCommand('dừng lại'), 'stop');
      expect(service.parseCommand('im lặng'), 'stop');
      expect(service.parseCommand('đọc lại'), 'repeat');
      expect(service.parseCommand('đọc'), 'repeat');
      expect(service.parseCommand('trợ giúp'), 'help');
      expect(service.parseCommand('giúp đỡ'), 'help');
    });

    test('is case-insensitive and trims whitespace', () {
      expect(service.parseCommand('  Quét Tài Liệu  '), 'scanner');
      expect(service.parseCommand('CÀI ĐẶT'), 'settings');
    });

    test('returns null for unrecognized text', () {
      expect(service.parseCommand('xin chào'), isNull);
      expect(service.parseCommand('hôm nay thế nào'), isNull);
      expect(service.parseCommand(''), isNull);
    });
  });
}
