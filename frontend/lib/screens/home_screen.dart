import 'package:flutter/material.dart';
import '../theme/app_theme.dart';
import '../widgets/big_button.dart';

/// Home screen with 4 massive buttons for blind users.
/// No decorations, no welcome text, just the features.
class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;

    return Scaffold(
      appBar: AppBar(
        title: const Text('BlindScholar'),
        backgroundColor: isDark ? AppTheme.pureBlack : AppTheme.primaryBlue,
        automaticallyImplyLeading: false,
      ),
      body: Semantics(
        label: 'Home screen. Select a feature.',
        child: SafeArea(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              children: [
                const SizedBox(height: 8),
                BigButton(
                  icon: Icons.menu_book_rounded,
                  label: 'Book Scanner',
                  semanticLabel: 'Book Scanner. Point camera at a book page to have it read aloud.',
                  color: AppTheme.primaryBlue,
                  iconColor: Colors.white,
                  onTap: () => Navigator.pushNamed(context, '/book-scanner'),
                ),
                const SizedBox(height: 12),
                BigButton(
                  icon: Icons.record_voice_over_rounded,
                  label: 'Text Reader',
                  semanticLabel: 'Text Reader. Type or paste text and have it read aloud.',
                  color: AppTheme.accentGreen,
                  iconColor: Colors.white,
                  onTap: () => Navigator.pushNamed(context, '/text-reader'),
                ),
                const SizedBox(height: 12),
                BigButton(
                  icon: Icons.mic_rounded,
                  label: 'Voice Notes',
                  semanticLabel: 'Voice Notes. Record and manage voice memos for your studies.',
                  color: AppTheme.accentOrange,
                  iconColor: Colors.white,
                  onTap: () => Navigator.pushNamed(context, '/voice-notes'),
                ),
                const SizedBox(height: 12),
                BigButton(
                  icon: Icons.settings_rounded,
                  label: 'Settings',
                  semanticLabel: 'Settings. Adjust speech speed, pitch, and volume.',
                  color: AppTheme.primaryDark,
                  iconColor: Colors.white,
                  onTap: () => Navigator.pushNamed(context, '/settings'),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
