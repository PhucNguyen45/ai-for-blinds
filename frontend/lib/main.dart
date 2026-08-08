import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'app.dart';
import 'services/api_service.dart';
import 'services/settings_service.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Load persisted settings and apply them before the app starts.
  var settings = await SettingsService().load();
  if (settings.deviceId.isEmpty) {
    // First launch: generate and persist a stable device identifier so
    // saved learning moments can be scoped to this device.
    settings = settings.copyWith(deviceId: SettingsService.generateDeviceId());
    await SettingsService().save(settings);
  }
  ApiService.configure(
    baseUrl: settings.serverUrl,
    apiKey: settings.apiKey,
  );

  // Set preferred orientations to portrait for easier handling
  SystemChrome.setPreferredOrientations([
    DeviceOrientation.portraitUp,
    DeviceOrientation.portraitDown,
  ]);

  runApp(BlindScholarApp(initialAutoListen: settings.autoListen));
}
