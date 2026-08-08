import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'screens/home_screen.dart';
import 'screens/review_screen.dart';
import 'screens/scanner_screen.dart';
import 'screens/search_screen.dart';
import 'screens/settings_screen.dart';
import 'screens/voice_qa_screen.dart';
import 'services/audio_service.dart';
import 'services/voice_command_service.dart';
import 'services/voice_controller.dart';
import 'theme/app_theme.dart';
import 'widgets/bottom_nav_bar.dart';
import 'widgets/gesture_navigator.dart';

/// Root widget for SgBe Vision — Neon Pulse edition.
/// 
/// Architecture:
/// - MultiProvider: AudioService + VoiceCommandService + VoiceController
/// - GestureNavigator: swipe navigation + shake-to-voice
/// - NeonBottomNavBar: 4 tabs + center voice FAB
/// - Dark-first: darkHighContrast là theme mặc định
/// - Voice-first: voice commands hoạt động toàn cục
class BlindScholarApp extends StatefulWidget {
  /// Initial value for the "auto-listen" setting, loaded at startup.
  final bool initialAutoListen;

  const BlindScholarApp({super.key, this.initialAutoListen = false});

  @override
  State<BlindScholarApp> createState() => _BlindScholarAppState();
}

class _BlindScholarAppState extends State<BlindScholarApp> {
  int _currentTab = 0;
  final _navigatorKey = GlobalKey<NavigatorState>();

  /// Các route paths tương ứng với tab index
  static const _tabRoutes = ['/', '/scanner', '/voice-qa', '/review'];

  void _onTabChanged(int index) {
    if (index < 0 || index >= _tabRoutes.length) return;
    setState(() => _currentTab = index);
    _navigatorKey.currentState?.pushReplacementNamed(_tabRoutes[index]);
  }

  void _onNavigateRoute(String route) {
    final tabIndex = _tabRoutes.indexOf(route);
    if (tabIndex >= 0) {
      _onTabChanged(tabIndex);
    } else {
      _navigatorKey.currentState?.pushNamed(route);
    }
  }

  void _onVoiceCommand() {
    context.read<VoiceController>().triggerGlobalVoice();
  }

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) {
          final service = AudioService();
          service.init();
          return service;
        }),
        ChangeNotifierProvider(create: (_) {
          final service = VoiceCommandService();
          service.init();
          return service;
        }),
        ChangeNotifierProxyProvider2<
            AudioService,
            VoiceCommandService,
            VoiceController>(
          create: (_) => VoiceController()
            ..onNavigate = _onNavigateRoute
            ..autoListen = widget.initialAutoListen,
          update: (_, audio, voice, controller) =>
              controller!..attach(audio: audio, voice: voice),
        ),
      ],
      child: MaterialApp(
        title: 'SgBe Vision',
        debugShowCheckedModeBanner: false,

        // Dark-first: theme mặc định là darkHighContrast
        theme: AppTheme.lightHighContrast,
        darkTheme: AppTheme.darkHighContrast,
        themeMode: ThemeMode.dark,

        // Navigator key để điều khiển từ bottom nav
        navigatorKey: _navigatorKey,
        initialRoute: '/',
        routes: {
          '/': (context) => const HomeScreen(),
          '/scanner': (context) => const ScannerScreen(),
          '/voice-qa': (context) => const VoiceQAScreen(),
          '/review': (context) => const ReviewScreen(),
          '/search': (context) => const SearchScreen(),
          '/settings': (context) => const SettingsScreen(),
        },
        onGenerateRoute: (settings) {
          // Fallback về home nếu route không tồn tại
          if (settings.name == null || !settings.name!.startsWith('/')) {
            return MaterialPageRoute(
              builder: (_) => const HomeScreen(),
              settings: const RouteSettings(name: '/'),
            );
          }
          return null;
        },

        // Accessibility: large text, high contrast, bold text
        builder: (context, child) {
          return GestureNavigator(
            currentIndex: _currentTab,
            onNavigate: _onTabChanged,
            onVoiceCommand: _onVoiceCommand,
            child: MediaQuery(
              data: MediaQuery.of(context).copyWith(
                accessibleNavigation: true,
                boldText: true,
                highContrast: true,
                textScaler: MediaQuery.of(context).textScaler.clamp(
                  minScaleFactor: 1.2,
                  maxScaleFactor: 2.0,
                ),
              ),
              child: Scaffold(
                body: child!,
                bottomNavigationBar: NeonBottomNavBar(
                  currentIndex: _currentTab,
                  onTabChanged: _onTabChanged,
                  onVoiceTap: _onVoiceCommand,
                  isVoiceActive:
                      context.watch<VoiceCommandService>().isListening,
                ),
              ),
            ),
          );
        },
      ),
    );
  }
}
