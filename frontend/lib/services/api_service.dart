import 'dart:convert';
import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;

/// Service for communicating with the FastAPI backend.
/// Handles image description, OCR, and TTS via API calls.
class ApiService {
  /// Base URL of the backend server.
  /// Defaults to localhost:8000 for development.
  /// Can be overridden via constructor or setter.
  String baseUrl;

  ApiService({this.baseUrl = 'http://localhost:8000'});

  /// Set a custom backend URL (e.g., from settings).
  void setBaseUrl(String url) {
    baseUrl = url.endsWith('/') ? url.substring(0, url.length - 1) : url;
  }

  /// Send an image to the backend for AI-powered description in Vietnamese.
  /// Uses Gemini 2.5 Flash to describe the image contextually for blind students.
  /// Returns the description text, or null on failure.
  Future<String?> describeImage(File imageFile) async {
    try {
      final uri = Uri.parse('$baseUrl/describe');
      final request = http.MultipartRequest('POST', uri);
      request.files.add(
        await http.MultipartFile.fromPath('file', imageFile.path),
      );

      final streamedResponse = await request.send().timeout(
        const Duration(seconds: 60),
      );
      final response = await http.Response.fromStream(streamedResponse);

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return data['description'] as String?;
      } else {
        debugPrint('API describe error: ${response.statusCode} ${response.body}');
        return null;
      }
    } catch (e) {
      debugPrint('API describe exception: $e');
      return null;
    }
  }

  /// Send an image to the backend for OCR text extraction.
  /// Returns the extracted text, or null on failure.
  Future<String?> ocrImage(File imageFile) async {
    try {
      final uri = Uri.parse('$baseUrl/ocr');
      final request = http.MultipartRequest('POST', uri);
      request.files.add(
        await http.MultipartFile.fromPath('file', imageFile.path),
      );

      final streamedResponse = await request.send().timeout(
        const Duration(seconds: 30),
      );
      final response = await http.Response.fromStream(streamedResponse);

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return data['text'] as String?;
      } else {
        debugPrint('API ocr error: ${response.statusCode} ${response.body}');
        return null;
      }
    } catch (e) {
      debugPrint('API ocr exception: $e');
      return null;
    }
  }

  /// Check if the backend is reachable.
  Future<bool> isBackendAvailable() async {
    try {
      final uri = Uri.parse('$baseUrl/');
      final response = await http.get(uri).timeout(const Duration(seconds: 5));
      return response.statusCode == 200;
    } catch (e) {
      return false;
    }
  }
}
