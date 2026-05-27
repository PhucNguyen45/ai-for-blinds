import 'dart:convert';
import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;

/// Service for communicating with the FastAPI backend.
/// Handles OCR, image description, TTS, STT, and RAG query via API calls.
class ApiService {
  /// Base URL of the backend server.
  /// Defaults to localhost:8000 for development.
  String baseUrl;

  ApiService({this.baseUrl = 'http://localhost:8000'});

  /// Set a custom backend URL (e.g., from settings).
  void setBaseUrl(String url) {
    baseUrl = url.endsWith('/') ? url.substring(0, url.length - 1) : url;
  }

  /// Send an image to the backend for AI-powered description in Vietnamese.
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

  /// Send an audio file to the backend for Vietnamese speech-to-text.
  /// Returns the transcribed text, or null on failure.
  Future<String?> sttAudio(File audioFile, {String language = 'vi'}) async {
    try {
      final uri = Uri.parse('$baseUrl/stt');
      final request = http.MultipartRequest('POST', uri);
      request.files.add(
        await http.MultipartFile.fromPath('file', audioFile.path),
      );
      request.fields['language'] = language;

      final streamedResponse = await request.send().timeout(
        const Duration(seconds: 60),
      );
      final response = await http.Response.fromStream(streamedResponse);

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        if (data is Map && data.containsKey('data') && data['data'] is Map) {
          return data['data']['text'] as String?;
        }
        return data['text'] as String?;
      } else {
        debugPrint('API stt error: ${response.statusCode} ${response.body}');
        return null;
      }
    } catch (e) {
      debugPrint('API stt exception: $e');
      return null;
    }
  }

  /// Send a question to the RAG backend for textbook-grounded Q&A.
  /// Returns a map with 'answer' (String) and 'source' (Map?), or null on failure.
  Future<Map<String, dynamic>?> ragQuery({
    required String question,
    int nResults = 5,
    int? grade,
    String? subject,
  }) async {
    try {
      final uri = Uri.parse('$baseUrl/rag/query');
      final body = <String, dynamic>{
        'question': question,
        'n_results': nResults,
      };
      if (grade != null) body['grade'] = grade;
      if (subject != null) body['subject'] = subject;

      final response = await http
          .post(uri, headers: {'Content-Type': 'application/json'}, body: jsonEncode(body))
          .timeout(const Duration(seconds: 60));

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        if (data is Map && data.containsKey('data')) {
          return data['data'] as Map<String, dynamic>;
        }
        return data as Map<String, dynamic>?;
      } else {
        debugPrint('API rag query error: ${response.statusCode} ${response.body}');
        return null;
      }
    } catch (e) {
      debugPrint('API rag query exception: $e');
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
