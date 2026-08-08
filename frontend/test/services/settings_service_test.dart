import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:ai_for_blinds/services/settings_service.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUp(() {
    SharedPreferences.setMockInitialValues({});
  });

  test('load returns defaults when nothing is persisted', () async {
    final settings = await SettingsService().load();
    expect(settings.serverUrl, '');
    expect(settings.apiKey, '');
    expect(settings.autoListen, false);
    expect(settings.deviceId, '');
  });

  test('save then load round-trips values', () async {
    final service = SettingsService();
    await service.save(
      const AppSettings(
        serverUrl: 'http://10.0.0.5:8000',
        apiKey: 'my-key',
        autoListen: true,
        deviceId: 'dev-abc123',
      ),
    );

    final loaded = await service.load();
    expect(loaded.serverUrl, 'http://10.0.0.5:8000');
    expect(loaded.apiKey, 'my-key');
    expect(loaded.autoListen, true);
    expect(loaded.deviceId, 'dev-abc123');
  });

  test('copyWith preserves unset fields', () {
    const base = AppSettings(
      serverUrl: 'http://a',
      apiKey: 'k',
      autoListen: false,
      deviceId: 'dev-1',
    );
    final updated = base.copyWith(autoListen: true);
    expect(updated.serverUrl, 'http://a');
    expect(updated.apiKey, 'k');
    expect(updated.autoListen, true);
    expect(updated.deviceId, 'dev-1');
  });

  test('generateDeviceId returns a non-empty unique id', () {
    final a = SettingsService.generateDeviceId();
    final b = SettingsService.generateDeviceId();
    expect(a, isNotEmpty);
    expect(a, startsWith('dev-'));
    expect(a, isNot(b));
  });
}
