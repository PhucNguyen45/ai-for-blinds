import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:google_mlkit_text_recognition/google_mlkit_text_recognition.dart';

/// On-device OCR fallback using Google ML Kit Text Recognition.
/// Used when backend OCR endpoint is unavailable.
class LocalOcrService {
  bool _available = false;

  bool get available => _available;

  Future<void> init() async {
    try {
      // ML Kit initializes lazily - just mark as available
      _available = true;
    } catch (e) {
      debugPrint('Local OCR not available: $e');
      _available = false;
    }
  }

  Future<String?> extractText(File imageFile) async {
    if (!_available) return null;
    try {
      final inputImage = InputImage.fromFile(imageFile);
      final textRecognizer = TextRecognizer();
      final recognizedText = await textRecognizer.processImage(inputImage);
      textRecognizer.close();

      if (recognizedText.text.trim().isEmpty) return null;
      return recognizedText.text.trim();
    } catch (e) {
      debugPrint('Local OCR error: $e');
      return null;
    }
  }
}
