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
  });

  test('save then load round-trips values', () async {
    final service = SettingsService();
    await service.save(
      const AppSettings(
        serverUrl: 'http://10.0.0.5:8000',
        apiKey: 'my-key',
        autoListen: true,
      ),
    );

    final loaded = await service.load();
    expect(loaded.serverUrl, 'http://10.0.0.5:8000');
    expect(loaded.apiKey, 'my-key');
    expect(loaded.autoListen, true);
  });

  test('copyWith preserves unset fields', () {
    const base = AppSettings(
      serverUrl: 'http://a',
      apiKey: 'k',
      autoListen: false,
    );
    final updated = base.copyWith(autoListen: true);
    expect(updated.serverUrl, 'http://a');
    expect(updated.apiKey, 'k');
    expect(updated.autoListen, true);
  });
}
