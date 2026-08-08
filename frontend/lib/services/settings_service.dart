import 'dart:math';

import 'package:shared_preferences/shared_preferences.dart';

/// Application settings that are persisted on the device via
/// [SharedPreferences]. Loaded once at startup and updated from the
/// settings screen.
class AppSettings {
  /// Backend server URL. Empty means the ApiService default is used.
  final String serverUrl;

  /// Backend API key. Empty means the ApiService default is used.
  final String apiKey;

  /// Whether the app auto-listens for voice commands after speaking a prompt.
  final bool autoListen;

  /// Stable device identifier used to scope saved learning moments.
  /// Empty means no moments will be saved/synced.
  final String deviceId;

  const AppSettings({
    required this.serverUrl,
    required this.apiKey,
    required this.autoListen,
    required this.deviceId,
  });

  AppSettings copyWith({
    String? serverUrl,
    String? apiKey,
    bool? autoListen,
    String? deviceId,
  }) {
    return AppSettings(
      serverUrl: serverUrl ?? this.serverUrl,
      apiKey: apiKey ?? this.apiKey,
      autoListen: autoListen ?? this.autoListen,
      deviceId: deviceId ?? this.deviceId,
    );
  }
}

/// Persists and loads [AppSettings] using shared preferences.
class SettingsService {
  static const _kServerUrl = 'server_url';
  static const _kApiKey = 'api_key';
  static const _kAutoListen = 'auto_listen';
  static const _kDeviceId = 'device_id';

  /// Generate a stable, anonymous device identifier (persisted locally).
  /// Used to scope saved learning moments to this device only.
  static String generateDeviceId() {
    final random = Random.secure();
    final now = DateTime.now().millisecondsSinceEpoch.toRadixString(16);
    final rand = List.generate(8, (_) => random.nextInt(16).toRadixString(16)).join();
    return 'dev-$now-$rand';
  }

  Future<AppSettings> load() async {
    final prefs = await SharedPreferences.getInstance();
    return AppSettings(
      serverUrl: prefs.getString(_kServerUrl) ?? '',
      apiKey: prefs.getString(_kApiKey) ?? '',
      autoListen: prefs.getBool(_kAutoListen) ?? false,
      deviceId: prefs.getString(_kDeviceId) ?? '',
    );
  }

  Future<void> save(AppSettings settings) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_kServerUrl, settings.serverUrl);
    await prefs.setString(_kApiKey, settings.apiKey);
    await prefs.setBool(_kAutoListen, settings.autoListen);
    await prefs.setString(_kDeviceId, settings.deviceId);
  }
}
