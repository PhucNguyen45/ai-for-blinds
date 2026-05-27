import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:google_mlkit_text_recognition/google_mlkit_text_recognition.dart';

/// Service that handles OCR text extraction from images using Google ML Kit.
/// Works 100% on-device with no network required.
class OcrService {
  final TextRecognizer _recognizer = TextRecognizer();

  /// Extract text from an image file.
  /// Returns the recognized text or null on failure.
  Future<String?> extractTextFromImage(File imageFile) async {
    try {
      final inputImage = InputImage.fromFile(imageFile);
      final recognizedText = await _recognizer.processImage(inputImage);

      if (recognizedText.text.trim().isEmpty) {
        return null;
      }

      return recognizedText.text;
    } catch (e) {
      debugPrint('OCR Error: $e');
      return null;
    }
  }

  /// Dispose the recognizer to free resources.
  void dispose() {
    _recognizer.close();
  }
}
