import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

/// Data model for a selectable chip in [GlowChipBar].
class GlowChipData {
  final String label;
  final String? subtitle;
  final IconData? icon;
  final Color color;

  const GlowChipData({
    required this.label,
    this.subtitle,
    this.icon,
    this.color = const Color(0xFF00F0FF),
  });
}

/// A selection chip/toggle with a neon glow effect when selected.
///
/// - Displays an optional icon, a primary label, and an optional subtitle.
/// - When [isSelected] is true the chip lights up in [selectedColor] with a
///   soft glow [BoxShadow] when [glow] is true.
/// - Provides [Semantics] for screen readers and [HapticFeedback] on every tap.
class GlowChip extends StatelessWidget {
  final String label;
  final String? subtitle;
  final IconData? icon;
  final bool isSelected;
  final VoidCallback onTap;
  final Color selectedColor;
  final bool glow;

  const GlowChip({
    super.key,
    required this.label,
    this.subtitle,
    this.icon,
    required this.isSelected,
    required this.onTap,
    this.selectedColor = const Color(0xFF00F0FF),
    this.glow = true,
  });

  @override
  Widget build(BuildContext context) {
    const Color surface = Color(0xFF141829);
    const Color border = Color(0xFF1E2A4A);
    const Color textPrimary = Color(0xFFFFFFFF);
    const Color textMuted = Color(0xFF8892B0);

    final Color bgColor;
    final Color borderColor;
    final double borderWidth;
    final Color iconColor;
    final Color labelColor;
    final Color subtitleColor;
    final List<BoxShadow>? shadows;

    if (isSelected) {
      bgColor = selectedColor.withValues(alpha: 0.15);
      borderColor = selectedColor;
      borderWidth = 2;
      iconColor = selectedColor;
      labelColor = textPrimary;
      subtitleColor = textPrimary.withValues(alpha: 0.7);
      if (glow) {
        shadows = [
          BoxShadow(
            color: selectedColor.withValues(alpha: 0.25),
            blurRadius: 8,
            spreadRadius: 2,
          ),
        ];
      } else {
        shadows = null;
      }
    } else {
      bgColor = surface;
      borderColor = border;
      borderWidth = 1;
      iconColor = textMuted;
      labelColor = textMuted;
      subtitleColor = textMuted.withValues(alpha: 0.7);
      shadows = null;
    }

    final String semanticsLabel = label +
        (isSelected ? ', Đang chọn' : '') +
        (subtitle != null ? ', $subtitle' : '');

    return Semantics(
      button: true,
      label: semanticsLabel,
      child: GestureDetector(
        onTap: () {
          HapticFeedback.lightImpact();
          onTap();
        },
        child: Container(
          width: double.infinity,
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: bgColor,
            borderRadius: BorderRadius.circular(16),
            border: Border.all(
              color: borderColor,
              width: borderWidth,
            ),
            boxShadow: shadows,
          ),
          child: Row(
            children: [
              if (icon != null) ...[
                Icon(icon, size: 32, color: iconColor),
                const SizedBox(width: 12),
              ],
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      label,
                      style: TextStyle(
                        fontSize: 20,
                        fontWeight: FontWeight.bold,
                        color: labelColor,
                      ),
                    ),
                    if (subtitle != null)
                      Padding(
                        padding: const EdgeInsets.only(top: 2),
                        child: Text(
                          subtitle!,
                          style: TextStyle(
                            fontSize: 14,
                            fontWeight: FontWeight.normal,
                            color: subtitleColor,
                          ),
                        ),
                      ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

/// A horizontal scrollable bar of [GlowChip] items.
///
/// Converts [items] into a row of selectable chips with 8px gaps.
/// The chip at [selectedIndex] is rendered in its selected state.
class GlowChipBar extends StatelessWidget {
  final List<GlowChipData> items;
  final int selectedIndex;
  final ValueChanged<int> onIndexChanged;

  const GlowChipBar({
    super.key,
    required this.items,
    required this.selectedIndex,
    required this.onIndexChanged,
  });

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      child: Row(
        children: List.generate(items.length, (index) {
          final item = items[index];
          return Padding(
            padding: EdgeInsets.only(
              left: index == 0 ? 0 : 8,
            ),
            child: GlowChip(
              label: item.label,
              subtitle: item.subtitle,
              icon: item.icon,
              isSelected: index == selectedIndex,
              selectedColor: item.color,
              onTap: () => onIndexChanged(index),
            ),
          );
        }),
      ),
    );
  }
}
