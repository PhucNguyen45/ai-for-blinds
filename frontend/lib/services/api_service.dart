import 'dart:convert';
import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'package:http_parser/http_parser.dart';

/// Service for communicating with the FastAPI backend.
/// Handles OCR, image description, TTS, STT, and RAG query via API calls.
class ApiService {
  /// Base URL of the backend server.
  ///
  /// `localhost` on an Android device means the phone itself, not the dev
  /// machine, so the default targets the emulator host alias `10.0.2.2`.
  /// On a physical device pass the LAN IP of the dev machine instead:
  ///   flutter run --dart-define=BACKEND_URL=http://192.168.1.x:8000
  static const defaultBaseUrl = String.fromEnvironment(
    'BACKEND_URL',
    defaultValue: 'http://10.0.2.2:8000',
  );

  /// Address entered in Cài đặt. Applies to every ApiService created after
  /// it is set, so screens that build their own instance pick it up too.
  static String? _savedBaseUrl;

  static String get activeBaseUrl => _savedBaseUrl ?? defaultBaseUrl;

  /// Apply an address for the whole app (call before building screens).
  static void configure(String? url) {
    if (url == null || url.trim().isEmpty) {
      _savedBaseUrl = null;
      return;
    }
    final trimmed = url.trim();
    _savedBaseUrl =
        trimmed.endsWith('/') ? trimmed.substring(0, trimmed.length - 1) : trimmed;
  }

  String baseUrl;

  ApiService({String? baseUrl}) : baseUrl = baseUrl ?? activeBaseUrl;

  /// `MultipartFile.fromPath` defaults to `application/octet-stream`, which
  /// `validate_image()` rejects with 400. Derive the real type from the path.
  MediaType _imageMediaType(String path) {
    final ext = path.split('.').last.toLowerCase();
    switch (ext) {
      case 'png':
        return MediaType('image', 'png');
      case 'webp':
        return MediaType('image', 'webp');
      case 'bmp':
        return MediaType('image', 'bmp');
      default:
        return MediaType('image', 'jpeg');
    }
  }

  /// Unwrap `{success, message, data: {...}}` from `response_builder.py`.
  /// Falls back to the raw body for endpoints that reply flat.
  Map<String, dynamic>? _unwrap(dynamic body) {
    if (body is! Map) return null;
    final inner = body['data'];
    if (inner is Map) return Map<String, dynamic>.from(inner);
    return Map<String, dynamic>.from(body);
  }

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
        await http.MultipartFile.fromPath(
          'file',
          imageFile.path,
          contentType: _imageMediaType(imageFile.path),
        ),
      );

      final streamedResponse = await request.send().timeout(
        const Duration(seconds: 60),
      );
      final response = await http.Response.fromStream(streamedResponse);

      if (response.statusCode == 200) {
        final body = jsonDecode(response.body);
        return _unwrap(body)?['description'] as String?;
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
        await http.MultipartFile.fromPath(
          'file',
          imageFile.path,
          contentType: _imageMediaType(imageFile.path),
        ),
      );

      final streamedResponse = await request.send().timeout(
        const Duration(seconds: 30),
      );
      final response = await http.Response.fromStream(streamedResponse);

      if (response.statusCode == 200) {
        final body = jsonDecode(response.body);
        return _unwrap(body)?['text'] as String?;
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
        final body = jsonDecode(response.body);
        return _unwrap(body)?['text'] as String?;
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
        final body = jsonDecode(response.body);
        return _unwrap(body);
      } else {
        debugPrint('API rag query error: ${response.statusCode} ${response.body}');
        return null;
      }
    } catch (e) {
      debugPrint('API rag query exception: $e');
      return null;
    }
  }

  /// Ask the backend to read `text` with the Edge TTS Vietnamese voice.
  ///
  /// The on-device engine (flutter_tts) depends on whatever the phone has
  /// installed — some devices have no Vietnamese voice at all. The server
  /// voice is consistent, so try it first and fall back on failure.
  Future<List<int>?> ttsAudio(String text, {String? voice}) async {
    try {
      final uri = Uri.parse('$baseUrl/tts');
      final response = await http
          .post(
            uri,
            headers: {'Content-Type': 'application/json; charset=utf-8'},
            body: jsonEncode({
              'text': text,
              'voice': ?voice,
            }),
          )
          .timeout(const Duration(seconds: 15));

      if (response.statusCode == 200 &&
          response.headers['content-type']?.contains('audio') == true) {
        return response.bodyBytes;
      }
      debugPrint('API tts error: ${response.statusCode}');
      return null;
    } catch (e) {
      debugPrint('API tts exception: $e');
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
