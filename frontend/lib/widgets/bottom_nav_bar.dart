import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../utils/responsive.dart';

/// A custom bottom navigation bar for the Neon Pulse theme.
///
/// Displays 4 labeled tab icons with a center floating voice FAB that
/// rises above the bar. Provides haptic feedback on interactions.
///
/// Tab indices map to [currentIndex] as follows:
///   0 – home, 1 – scanner, 2 – Q&A, 3 – review
class NeonBottomNavBar extends StatelessWidget {
  /// The index of the currently selected tab (0–3).
  final int currentIndex;

  /// Called when a tab is tapped, with the tab's index.
  final ValueChanged<int> onTabChanged;

  /// Called when the center voice FAB is tapped.
  final VoidCallback onVoiceTap;

  /// Whether the voice assistant is currently active / listening.
  ///
  /// When `true` the FAB switches to lime (0xFF39FF14) and shows a
  /// pulsing glow shadow.
  final bool isVoiceActive;

  const NeonBottomNavBar({
    super.key,
    required this.currentIndex,
    required this.onTabChanged,
    required this.onVoiceTap,
    this.isVoiceActive = false,
  });

  @override
  Widget build(BuildContext context) {
    final barH = Responsive.scale(context, 80, min: 60, max: 90);
    final fabS = Responsive.scale(context, 64, min: 48, max: 72);
    final tabIconS = Responsive.scale(context, 26, min: 20, max: 32);
    final tabFontS = Responsive.textScale(context, 12, min: 10, max: 14);

    return Stack(
      clipBehavior: Clip.none,
      children: [
        // ── Bottom bar ─────────────────────────────────────
        Container(
          height: barH,
          decoration: const BoxDecoration(
            color: Color(0xFF141829),
            border: Border(
              top: BorderSide(color: Color(0xFF1E2A4A), width: 1),
            ),
          ),
          child: SafeArea(
            top: false,
            child: Padding(
              padding: const EdgeInsets.only(top: 6),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                children: [
                  _buildTabItem(
                    index: 0,
                    icon: Icons.home_rounded,
                    label: 'Trang chủ',
                    iconSize: tabIconS,
                    fontSize: tabFontS,
                  ),
                  _buildTabItem(
                    index: 1,
                    icon: Icons.document_scanner_rounded,
                    label: 'Quét',
                    iconSize: tabIconS,
                    fontSize: tabFontS,
                  ),
                  _buildTabItem(
                    index: 2,
                    icon: Icons.mic_rounded,
                    label: 'Hỏi đáp',
                    iconSize: tabIconS,
                    fontSize: tabFontS,
                  ),
                  _buildTabItem(
                    index: 3,
                    icon: Icons.history_rounded,
                    label: 'Ôn tập',
                    iconSize: tabIconS,
                    fontSize: tabFontS,
                  ),
                ],
              ),
            ),
          ),
        ),

        // ── Center voice FAB (elevated above the bar) ──────
        Positioned(
          top: -(fabS * 0.65),
          left: 0,
          right: 0,
          child: Center(
            child: Semantics(
              button: true,
              label: 'Trợ lý giọng nói',
              child: GestureDetector(
                onTap: () {
                  HapticFeedback.heavyImpact();
                  onVoiceTap();
                },
                child: Container(
                  width: fabS,
                  height: fabS,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: isVoiceActive
                        ? const Color(0xFF39FF14)
                        : const Color(0xFF00F0FF),
                    boxShadow: isVoiceActive
                        ? [
                            BoxShadow(
                              color: const Color(0xFF39FF14)
                                  .withValues(alpha: 0.35),
                              blurRadius: 15,
                              spreadRadius: 5,
                            ),
                          ]
                        : null,
                  ),
                  child: Icon(
                    Icons.mic_rounded,
                    size: fabS * 0.5,
                    color: Color(0xFFFFFFFF),
                  ),
                ),
              ),
            ),
          ),
        ),
      ],
    );
  }

  // ── Individual tab item ──────────────────────────────────

  Widget _buildTabItem({
    required int index,
    required IconData icon,
    required String label,
    double iconSize = 26,
    double fontSize = 12,
  }) {
    final bool isSelected = currentIndex == index;

    return Semantics(
      button: true,
      label: label,
      child: GestureDetector(
        onTap: () {
          HapticFeedback.mediumImpact();
          onTabChanged(index);
        },
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              icon,
              size: iconSize,
              color: isSelected
                  ? const Color(0xFF00F0FF)
                  : const Color(0xFF8892B0),
            ),
            const SizedBox(height: 4),
            Text(
              label,
              style: TextStyle(
                fontSize: fontSize,
                color: isSelected
                    ? const Color(0xFF00F0FF)
                    : const Color(0xFF8892B0),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
