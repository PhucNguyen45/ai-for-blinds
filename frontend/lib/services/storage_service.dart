import 'dart:convert';
import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:path_provider/path_provider.dart';

import '../models/learning_moment.dart';

/// Service that abstracts local file storage operations.
/// Provides a unified API for reading/writing JSON, managing directories,
/// and persisting app data to the device's documents directory.
class StorageService {
  /// Get the app's documents directory.
  Future<Directory> getDocumentsDirectory() async {
    return await getApplicationDocumentsDirectory();
  }

  /// Get or create a subdirectory within the documents directory.
  Future<Directory> getDirectory(String name) async {
    final appDir = await getDocumentsDirectory();
    final dir = Directory('${appDir.path}/$name');
    if (!await dir.exists()) {
      await dir.create(recursive: true);
    }
    return dir;
  }

  /// Read a JSON file and decode it.
  /// Returns null if the file doesn't exist or can't be decoded.
  Future<dynamic> readJson(String fileName, {String? subdirectory}) async {
    try {
      final file = await _getFile(fileName, subdirectory: subdirectory);
      if (!await file.exists()) return null;
      final content = await file.readAsString();
      return jsonDecode(content);
    } catch (e) {
      debugPrint('StorageService.readJson error ($fileName): $e');
      return null;
    }
  }

  /// Write a JSON-serializable object to a file.
  Future<bool> writeJson(String fileName, dynamic data, {String? subdirectory}) async {
    try {
      final file = await _getFile(fileName, subdirectory: subdirectory);
      final encoded = jsonEncode(data);
      await file.writeAsString(encoded);
      return true;
    } catch (e) {
      debugPrint('StorageService.writeJson error ($fileName): $e');
      return false;
    }
  }

  /// Delete a file.
  Future<bool> deleteFile(String fileName, {String? subdirectory}) async {
    try {
      final file = await _getFile(fileName, subdirectory: subdirectory);
      if (await file.exists()) {
        await file.delete();
      }
      return true;
    } catch (e) {
      debugPrint('StorageService.deleteFile error ($fileName): $e');
      return false;
    }
  }

  /// Check if a file exists.
  Future<bool> fileExists(String fileName, {String? subdirectory}) async {
    try {
      final file = await _getFile(fileName, subdirectory: subdirectory);
      return await file.exists();
    } catch (_) {
      return false;
    }
  }

  /// List all files in a subdirectory.
  Future<List<FileSystemEntity>> listFiles(String subdirectory) async {
    try {
      final dir = await getDirectory(subdirectory);
      return dir.listSync();
    } catch (e) {
      debugPrint('StorageService.listFiles error ($subdirectory): $e');
      return [];
    }
  }

  /// Load all saved LearningMoments from JSON storage.
  Future<List<LearningMoment>> loadLearningMoments() async {
    try {
      final data = await readJson('learning_moments.json');
      if (data == null) return [];
      final List<dynamic> items = data as List<dynamic>;
      return items
          .map((e) => LearningMoment.fromJson(e as Map<String, dynamic>))
          .toList();
    } catch (e) {
      debugPrint('StorageService.loadLearningMoments error: $e');
      return [];
    }
  }

  /// Save a LearningMoment to JSON storage.
  Future<bool> saveLearningMoment(LearningMoment moment) async {
    try {
      final moments = await loadLearningMoments();
      moments.add(moment);
      final encoded = moments.map((m) => m.toJson()).toList();
      return await writeJson('learning_moments.json', encoded);
    } catch (e) {
      debugPrint('StorageService.saveLearningMoment error: $e');
      return false;
    }
  }

  /// Backend address chosen in Cài đặt. Null means use the build default.
  Future<String?> loadBackendUrl() async {
    final data = await readJson('settings.json');
    if (data is Map && data['backend_url'] is String) {
      return data['backend_url'] as String;
    }
    return null;
  }

  Future<bool> saveBackendUrl(String url) async {
    final data = await readJson('settings.json');
    final map = data is Map ? Map<String, dynamic>.from(data) : <String, dynamic>{};
    map['backend_url'] = url;
    return await writeJson('settings.json', map);
  }

  /// Get a File reference within the app's documents directory.
  Future<File> _getFile(String fileName, {String? subdirectory}) async {
    final appDir = await getDocumentsDirectory();
    if (subdirectory != null) {
      final dir = await getDirectory(subdirectory);
      return File('${dir.path}/$fileName');
    }
    return File('${appDir.path}/$fileName');
  }
}
