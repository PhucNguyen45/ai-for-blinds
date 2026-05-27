import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'screens/book_scanner_screen.dart';
import 'screens/home_screen.dart';
import 'screens/text_reader_screen.dart';
import 'screens/voice_notes_screen.dart';
import 'screens/settings_screen.dart';
import 'services/tts_service.dart';
import 'theme/app_theme.dart';

/// Root widget for the BlindScholar application.
/// Configures routing and provides TtsService via Provider.
class BlindScholarApp extends StatelessWidget {
  const BlindScholarApp({super.key});

  @override
  Widget build(BuildContext context) {
    return ChangeNotifierProvider(
      create: (_) => TtsService(),
      child: MaterialApp(
        title: 'BlindScholar',
        debugShowCheckedModeBanner: false,

        // Use high-contrast themes
        theme: AppTheme.lightHighContrast,
        darkTheme: AppTheme.darkHighContrast,
        themeMode: ThemeMode.system,

        // Route configuration
        initialRoute: '/',
        routes: {
          '/': (context) => const HomeScreen(),
          '/book-scanner': (context) => const BookScannerScreen(),
          '/text-reader': (context) => const TextReaderScreen(),
          '/voice-notes': (context) => const VoiceNotesScreen(),
          '/settings': (context) => const SettingsScreen(),
        },

        // Enable accessibility large text
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
