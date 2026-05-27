import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import '../services/tts_service.dart';
import '../theme/app_theme.dart';

/// Settings screen. Simplified: just sliders and a test button, no decorative elements.
class SettingsScreen extends StatelessWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;
    final bgColor = isDark ? AppTheme.pureBlack : AppTheme.pureWhite;
    final cardColor = isDark ? AppTheme.darkCard : AppTheme.pureWhite;
    final borderColor = isDark ? Colors.grey.shade700 : Colors.grey.shade300;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Settings'),
        backgroundColor: isDark ? AppTheme.pureBlack : AppTheme.primaryBlue,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_rounded, size: 32),
          onPressed: () => Navigator.pop(context),
        ),
      ),
      body: Container(
        color: bgColor,
        child: Consumer<TtsService>(
          builder: (context, tts, _) {
            return ListView(
              padding: const EdgeInsets.all(16),
              children: [
                const SizedBox(height: 8),

                // Speech Speed
                _SettingSlider(
                  label: 'Speech Speed',
                  value: tts.speechRate,
                  min: 0.2,
                  max: 1.0,
                  divisions: 8,
                  displayValue: tts.speechRate.toStringAsFixed(1),
                  onChanged: (val) => tts.setSpeechRate(val),
                  cardColor: cardColor,
                  borderColor: borderColor,
                  theme: theme,
                ),
                const SizedBox(height: 12),

                // Pitch
                _SettingSlider(
                  label: 'Pitch',
                  value: tts.pitch,
                  min: 0.5,
                  max: 2.0,
                  divisions: 6,
                  displayValue: tts.pitch.toStringAsFixed(1),
                  onChanged: (val) => tts.setPitch(val),
                  cardColor: cardColor,
                  borderColor: borderColor,
                  theme: theme,
                ),
                const SizedBox(height: 12),

                // Volume
                _SettingSlider(
                  label: 'Volume',
                  value: tts.volume,
                  min: 0.0,
                  max: 1.0,
                  divisions: 5,
                  displayValue: tts.volume.toStringAsFixed(1),
                  onChanged: (val) => tts.setVolume(val),
                  cardColor: cardColor,
                  borderColor: borderColor,
                  theme: theme,
                ),

                const SizedBox(height: 24),

                // Test button
                Semantics(
                  button: true,
                  label: 'Test speech settings.',
                  child: GestureDetector(
                    onTap: () {
                      HapticFeedback.mediumImpact();
                      tts.speak(
                        'Hello! This is a test of your current speech settings. '
                        'If you can hear this clearly, your settings are good to go.',
                      );
                    },
                    child: Container(
                      width: double.infinity,
                      constraints: const BoxConstraints(minHeight: 72),
                      padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
                      decoration: BoxDecoration(
                        color: AppTheme.accentGreen,
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: const Center(
                        child: Text(
                          'Test Settings',
                          style: TextStyle(
                            fontSize: 24,
                            fontWeight: FontWeight.w600,
                            color: Colors.white,
                          ),
                        ),
                      ),
                    ),
                  ),
                ),

                const SizedBox(height: 32),

                // About
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: cardColor,
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: borderColor),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'BlindScholar v1.0.0',
                        style: theme.textTheme.titleLarge,
                      ),
                      const SizedBox(height: 4),
                      Text(
                        'Accessible study companion for blind students.',
                        style: theme.textTheme.bodyMedium?.copyWith(
                          color: isDark ? Colors.grey.shade400 : Colors.grey.shade600,
                        ),
                      ),
                    ],
                  ),
                ),

                const SizedBox(height: 32),
              ],
            );
          },
        ),
      ),
    );
  }
}

/// A plain slider card with label and value, no decorative icons.
class _SettingSlider extends StatelessWidget {
  final String label;
  final double value;
  final double min;
  final double max;
  final int divisions;
  final String displayValue;
  final ValueChanged<double> onChanged;
  final Color cardColor;
  final Color borderColor;
  final ThemeData theme;

  const _SettingSlider({
    required this.label,
    required this.value,
    required this.min,
    required this.max,
    required this.divisions,
    required this.displayValue,
    required this.onChanged,
    required this.cardColor,
    required this.borderColor,
    required this.theme,
  });

  @override
  Widget build(BuildContext context) {
    return Semantics(
      label: '$label. $displayValue',
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: cardColor,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: borderColor),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Text(
                  label,
                  style: theme.textTheme.titleLarge,
                ),
                const Spacer(),
                Text(
                  displayValue,
                  style: theme.textTheme.titleLarge?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
            Slider(
              value: value,
              min: min,
              max: max,
              divisions: divisions,
              label: '$label: $displayValue',
              onChanged: onChanged,
            ),
          ],
        ),
      ),
    );
  }
}
