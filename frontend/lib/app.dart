import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'screens/home_screen.dart';
import 'screens/review_screen.dart';
import 'screens/scanner_screen.dart';
import 'screens/settings_screen.dart';
import 'screens/voice_qa_screen.dart';
import 'services/audio_service.dart';
import 'services/storage_service.dart';
import 'theme/app_theme.dart';

/// Root widget for the SgBe Vision application.
/// Cung cấp AudioService + StorageService qua Provider.
/// Routes: / (Home), /scanner, /voice-qa, /review, /settings.
class BlindScholarApp extends StatelessWidget {
  const BlindScholarApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => AudioService()),
        Provider(create: (_) => StorageService()),
      ],
      child: MaterialApp(
        title: 'SgBe Vision',
        debugShowCheckedModeBanner: false,

        // High-contrast themes
        theme: AppTheme.lightHighContrast,
        darkTheme: AppTheme.darkHighContrast,
        themeMode: ThemeMode.system,

        // Route configuration — voice-first navigation
        initialRoute: '/',
        routes: {
          '/': (context) => const HomeScreen(),
          '/scanner': (context) => const ScannerScreen(),
          '/voice-qa': (context) => const VoiceQAScreen(),
          '/review': (context) => const ReviewScreen(),
          '/settings': (context) => const SettingsScreen(),
        },

        // Accessibility: large text, high contrast, bold text
        builder: (context, child) {
          return MediaQuery(
            data: MediaQuery.of(context).copyWith(
              accessibleNavigation: true,
              boldText: true,
              highContrast: true,
              textScaler: MediaQuery.of(context).textScaler.clamp(
                minScaleFactor: 1.2,
                maxScaleFactor: 2.0,
              ),
            ),
            child: child!,
          );
        },
      ),
    );
  }
}
