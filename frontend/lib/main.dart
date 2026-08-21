import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'app.dart';
import 'services/api_service.dart';
import 'services/storage_service.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Apply the backend address saved in Cài đặt before any screen calls the API.
  ApiService.configure(await StorageService().loadBackendUrl());

  // Set preferred orientations to portrait for easier handling
  SystemChrome.setPreferredOrientations([
    DeviceOrientation.portraitUp,
    DeviceOrientation.portraitDown,
  ]);

  runApp(const BlindScholarApp());
}
