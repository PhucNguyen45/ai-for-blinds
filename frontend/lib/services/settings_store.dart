import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../api/api_client.dart';
import '../api/demo_api.dart';

/// Cài đặt lưu trên máy. Đổi địa chỉ máy chủ không phải build lại app.
class SettingsStore extends ChangeNotifier {
  SettingsStore(this._prefs);

  static Future<SettingsStore> load() async => SettingsStore(await SharedPreferences.getInstance());

  final SharedPreferences _prefs;

  /// Máy ảo Android nhìn thấy laptop ở 10.0.2.2. Điện thoại thật phải đổi sang IP LAN.
  static const defaultServer = 'http://10.0.2.2:8000';
  static const defaultRate = 0.5;

  String get serverUrl => _prefs.getString('server_url') ?? defaultServer;
  double get speechRate => _prefs.getDouble('speech_rate') ?? defaultRate;
  bool get demoMode => _prefs.getBool('demo_mode') ?? false;
  String get pageType => _prefs.getString('page_type') ?? 'auto';

  Future<void> setServerUrl(String v) => _set(() => _prefs.setString('server_url', ApiClient.normalizeBaseUrl(v)));
  Future<void> setSpeechRate(double v) => _set(() => _prefs.setDouble('speech_rate', v));
  Future<void> setDemoMode(bool v) => _set(() => _prefs.setBool('demo_mode', v));
  Future<void> setPageType(String v) => _set(() => _prefs.setString('page_type', v));

  Future<void> _set(Future<bool> Function() write) async {
    await write();
    _api = null;
    notifyListeners();
  }

  SgbeApi? _api;

  /// API đang dùng, theo cài đặt hiện tại (máy chủ thật hoặc demo).
  SgbeApi get api => _api ??= demoMode ? DemoApi() : ApiClient(serverUrl);
}
