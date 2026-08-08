import 'dart:convert';
import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;

/// Service for communicating with the FastAPI backend.
/// Handles OCR, image description, TTS, STT, and RAG query via API calls.
///
/// Server URL and API key are stored as static state so every [ApiService]
/// instance shares the same configuration. Configure them once at startup
/// (via [configure]) or from the settings screen.
class ApiService {
  static const _defaultBaseUrl = 'http://192.168.1.100:8000';
  static const _defaultApiKey = 'sgbe_dev_key_2024';

  static String _baseUrl = _defaultBaseUrl;
  static String _apiKey = _defaultApiKey;

  /// Base URL of the backend server.
  /// Defaults to a sensible LAN address for real-world use.
  String get baseUrl => _baseUrl;

  /// Current API key for backend authentication.
  String get apiKey => _apiKey;

  ApiService({String? baseUrl}) {
    if (baseUrl != null) setBaseUrl(baseUrl);
  }

  /// Apply persisted configuration. Empty values keep the current default.
  static void configure({String? baseUrl, String? apiKey}) {
    if (baseUrl != null && baseUrl.trim().isNotEmpty) {
      final trimmed = baseUrl.trim();
      _baseUrl = trimmed.endsWith('/')
          ? trimmed.substring(0, trimmed.length - 1)
          : trimmed;
    }
    if (apiKey != null && apiKey.trim().isNotEmpty) {
      _apiKey = apiKey.trim();
    }
  }

  /// Set a custom backend URL (e.g., from settings).
  void setBaseUrl(String url) {
    final trimmed = url.trim();
    _baseUrl =
        trimmed.endsWith('/') ? trimmed.substring(0, trimmed.length - 1) : trimmed;
  }

  /// Set a custom API key (e.g., from settings).
  void setApiKey(String key) {
    if (key.trim().isNotEmpty) _apiKey = key.trim();
  }

  /// Send an image to the backend for AI-powered description in Vietnamese.
  Future<String?> describeImage(File imageFile) async {
    try {
      final uri = Uri.parse('$baseUrl/describe');
      final request = http.MultipartRequest('POST', uri);
      request.headers['X-API-Key'] = _apiKey;
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
      request.headers['X-API-Key'] = _apiKey;
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
      request.headers['X-API-Key'] = _apiKey;
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
          .post(
            uri,
            headers: {
              'Content-Type': 'application/json',
              'X-API-Key': _apiKey,
            },
            body: jsonEncode(body),
          )
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

  /// Send an image to the backend for object detection (YOLOv8).
  /// Returns detection result map, or null on failure.
  Future<Map<String, dynamic>?> detectImage(File imageFile) async {
    try {
      final uri = Uri.parse('$baseUrl/detect');
      final request = http.MultipartRequest('POST', uri);
      request.headers['X-API-Key'] = _apiKey;
      request.files.add(
        await http.MultipartFile.fromPath('file', imageFile.path),
      );

      final streamedResponse = await request.send().timeout(
        const Duration(seconds: 30),
      );
      final response = await http.Response.fromStream(streamedResponse);

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        if (data is Map && data.containsKey('data')) {
          return data['data'] as Map<String, dynamic>;
        }
        return data as Map<String, dynamic>?;
      } else {
        debugPrint('API detect error: ${response.statusCode} ${response.body}');
        return null;
      }
    } catch (e) {
      debugPrint('API detect exception: $e');
      return null;
    }
  }

  /// Send an image to the backend for VND banknote denomination recognition.
  /// Returns a result map (denomination, formatted, method, confidence), or
  /// null on failure.
  Future<Map<String, dynamic>?> recognizeMoney(File imageFile) async {
    try {
      final uri = Uri.parse('$baseUrl/money');
      final request = http.MultipartRequest('POST', uri);
      request.headers['X-API-Key'] = _apiKey;
      request.files.add(
        await http.MultipartFile.fromPath('file', imageFile.path),
      );

      final streamedResponse = await request.send().timeout(
        const Duration(seconds: 60),
      );
      final response = await http.Response.fromStream(streamedResponse);

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        if (data is Map && data.containsKey('data')) {
          return data['data'] as Map<String, dynamic>;
        }
        return data as Map<String, dynamic>?;
      } else {
        debugPrint('API money error: ${response.statusCode} ${response.body}');
        return null;
      }
    } catch (e) {
      debugPrint('API money exception: $e');
      return null;
    }
  }

  /// Search the web + Vietnamese news via the IR backend.
  /// Returns a list of result maps (title, snippet, url, source, score).
  Future<List<Map<String, dynamic>>> searchWeb(
    String query, {
    int nResults = 5,
  }) async {
    try {
      final uri = Uri.parse('$baseUrl/search');
      final response = await http
          .post(
            uri,
            headers: {
              'Content-Type': 'application/json',
              'X-API-Key': _apiKey,
            },
            body: jsonEncode({
              'query': query,
              'n_results': nResults,
            }),
          )
          .timeout(const Duration(seconds: 45));

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final payload = data is Map ? data['data'] : null;
        final results = payload is Map ? payload['results'] : null;
        if (results is List) {
          return results.cast<Map<String, dynamic>>();
        }
      } else {
        debugPrint('API search error: ${response.statusCode} ${response.body}');
      }
    } catch (e) {
      debugPrint('API search exception: $e');
    }
    return [];
  }

  /// Send data points to the backend for sonification.  /// Returns sonification data (tones, description, summary), or null on failure.
  Future<Map<String, dynamic>?> sonifyData({
    required List<Map<String, dynamic>> dataPoints,
    String chartType = 'bar',
  }) async {
    try {
      final uri = Uri.parse('$baseUrl/sonify');
      final response = await http
          .post(
            uri,
            headers: {
              'Content-Type': 'application/json',
              'X-API-Key': _apiKey,
            },
            body: jsonEncode({
              'data_points': dataPoints,
              'chart_type': chartType,
            }),
          )
          .timeout(const Duration(seconds: 30));

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        if (data is Map && data.containsKey('data')) {
          return data['data'] as Map<String, dynamic>;
        }
        return data as Map<String, dynamic>?;
      } else {
        debugPrint('API sonify error: ${response.statusCode} ${response.body}');
        return null;
      }
    } catch (e) {
      debugPrint('API sonify exception: $e');
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
