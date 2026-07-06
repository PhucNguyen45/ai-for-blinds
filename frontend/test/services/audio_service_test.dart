import 'package:flutter_test/flutter_test.dart';
import 'package:ai_for_blinds/services/audio_service.dart';

void main() {
  group('AudioService', () {
    test('initial state is idle', () {
      final service = AudioService();
      expect(service.isSpeaking, false);
      expect(service.isPaused, false);
      expect(service.isRecording, false);
      expect(service.isListening, false);
      expect(service.speechRate, 0.5);
      expect(service.pitch, 1.0);
      expect(service.volume, 1.0);
    });
  });
}
