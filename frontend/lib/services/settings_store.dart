import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../api/api_client.dart';
import '../api/demo_api.dart';
import '../library/library_data.dart';

/// Một mức tốc độ đọc chọn nhanh trong Cài đặt (thang của flutter_tts: 0,5 là bình thường).
@immutable
class RatePreset {
  const RatePreset(this.value, this.name);
  final double value;
  final String name;
}

/// Cài đặt lưu trên máy. Đổi địa chỉ máy chủ không phải build lại app.
class SettingsStore extends ChangeNotifier implements LibraryCache {
  SettingsStore(this._prefs);

  static Future<SettingsStore> load() async => SettingsStore(await SharedPreferences.getInstance());

  final SharedPreferences _prefs;

  /// Máy ảo Android nhìn thấy laptop ở 10.0.2.2. Điện thoại thật phải đổi sang IP LAN.
  static const defaultServer = 'http://10.0.2.2:8000';
  static const defaultRate = 0.5;

  /// Bốn mức chọn nhanh; chỉnh tinh từ 0,3 tới 1,0 ở phần cài đặt cho người hỗ trợ.
  static const ratePresets = [
    RatePreset(0.35, 'Chậm'),
    RatePreset(0.5, 'Bình thường'),
    RatePreset(0.65, 'Nhanh'),
    RatePreset(0.8, 'Rất nhanh'),
  ];

  String get serverUrl => _prefs.getString('server_url') ?? defaultServer;
  double get speechRate => _prefs.getDouble('speech_rate') ?? defaultRate;
  bool get demoMode => _prefs.getBool('demo_mode') ?? false;
  String get pageType => _prefs.getString('page_type') ?? 'auto';
  bool get soundOn => _prefs.getBool('sound_on') ?? true;
  bool get vibrateOn => _prefs.getBool('vibrate_on') ?? true;

  /// Đã nghe lời hướng dẫn lần đầu chưa.
  bool get tutorialDone => _prefs.getBool('tutorial_done') ?? false;

  /// Mức gần nhất với tốc độ đang đặt (tốc độ có thể đã chỉnh tinh).
  RatePreset get ratePreset {
    var best = ratePresets.first;
    for (final p in ratePresets) {
      if ((p.value - speechRate).abs() < (best.value - speechRate).abs()) best = p;
    }
    return best;
  }

  /// Mức tốc độ tiếp theo (vòng lại từ đầu), dùng khi chạm hai lần vào "Tốc độ đọc".
  RatePreset get nextRatePreset {
    final i = ratePresets.indexOf(ratePreset);
    return ratePresets[(i + 1) % ratePresets.length];
  }

  Future<void> setServerUrl(String v) => _set(() => _prefs.setString('server_url', ApiClient.normalizeBaseUrl(v)));
  Future<void> setSpeechRate(double v) => _set(() => _prefs.setDouble('speech_rate', v));
  Future<void> setDemoMode(bool v) => _set(() => _prefs.setBool('demo_mode', v));
  Future<void> setPageType(String v) => _set(() => _prefs.setString('page_type', v));
  Future<void> setSoundOn(bool v) => _set(() => _prefs.setBool('sound_on', v));
  Future<void> setVibrateOn(bool v) => _set(() => _prefs.setBool('vibrate_on', v));
  Future<void> setTutorialDone(bool v) => _set(() => _prefs.setBool('tutorial_done', v));

  /// Bản thư viện tải lần trước (JSON), để nghe khi mất mạng. Không báo đổi cài đặt.
  @override
  String? get libraryCache => _prefs.getString('library_cache');

  @override
  Future<void> setLibraryCache(String json) => _prefs.setString('library_cache', json);

  Future<void> _set(Future<bool> Function() write) async {
    await write();
    _api = null;
    notifyListeners();
  }

  SgbeApi? _api;

  /// API đang dùng, theo cài đặt hiện tại (máy chủ thật hoặc demo).
  SgbeApi get api => _api ??= demoMode ? DemoApi() : ApiClient(serverUrl);
}
