import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../theme/app_theme.dart';

/// A massive, no-frills button designed for blind users.
/// - Uses ElevatedButton as per design spec
/// - Icon + Label + optional Subtitle in a Column layout
/// - Minimum 48dp touch target (≥80dp recommended)
/// - Clear Semantics label for screen readers
/// - Haptic feedback on every tap
///
/// Design spec: Icon(40) + Text(20, bold) + optional subtitle(14)
class BigButton extends StatelessWidget {
  final IconData icon;
  final String label;
  final String? subtitle;
  final String? semanticLabel;
  final Color? color;
  final Color iconColor;
  final VoidCallback onTap;

  const BigButton({
    super.key,
    required this.icon,
    required this.label,
    this.subtitle,
    this.semanticLabel,
    this.color,
    this.iconColor = Colors.white,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final bgColor = color ?? (isDark ? AppTheme.darkCard : AppTheme.primaryBlue);

    return Semantics(
      label: semanticLabel ?? label,
      hint: 'Nhấn hai lần để kích hoạt',
      button: true,
      child: SizedBox(
        width: double.infinity,
        child: ElevatedButton(
          onPressed: () {
            HapticFeedback.mediumImpact();
            onTap();
          },
          style: ElevatedButton.styleFrom(
            backgroundColor: bgColor,
            foregroundColor: Colors.white,
            minimumSize: const Size(double.infinity, 80),
            padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 20),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(0),
              side: BorderSide(
                color: isDark ? Colors.grey.shade700 : Colors.grey.shade300,
                width: 2,
              ),
            ),
            elevation: 0,
            shadowColor: Colors.transparent,
          ),
          child: Row(
            children: [
              Icon(icon, size: 40, color: iconColor),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      label,
                      style: const TextStyle(
                        fontSize: 20,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    if (subtitle != null) ...[
                      const SizedBox(height: 2),
                      Text(
                        subtitle!,
                        style: const TextStyle(
                          fontSize: 14,
                          fontWeight: FontWeight.normal,
                        ),
                      ),
                    ],
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

/// A massive icon-only round button for primary actions (scan, record).
/// 120px diameter, solid color, no shadows, no animations.
class BigCircleButton extends StatelessWidget {
  final IconData icon;
  final String label;
  final Color color;
  final VoidCallback onTap;

  const BigCircleButton({
    super.key,
    required this.icon,
    required this.label,
    required this.color,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Semantics(
      button: true,
      label: label,
      child: GestureDetector(
        onTap: () {
          HapticFeedback.mediumImpact();
          onTap();
        },
        child: Container(
          width: 120,
          height: 120,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            color: color,
            border: Border.all(
              color: Colors.white,
              width: 3,
            ),
          ),
          child: Icon(icon, size: 56, color: Colors.white),
        ),
      ),
    );
  }
}

/// A big rectangular control button for media controls (play, pause, stop).
/// 72px height, solid color, no animations.
class BigMediaButton extends StatelessWidget {
  final IconData icon;
  final String label;
  final Color color;
  final VoidCallback onTap;

  const BigMediaButton({
    super.key,
    required this.icon,
    required this.label,
    required this.color,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Semantics(
      button: true,
      label: label,
      child: GestureDetector(
        onTap: () {
          HapticFeedback.mediumImpact();
          onTap();
        },
        child: Container(
          constraints: const BoxConstraints(minWidth: 100, minHeight: 72),
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          decoration: BoxDecoration(
            color: color,
            borderRadius: BorderRadius.circular(16),
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(icon, size: 36, color: Colors.white),
              const SizedBox(height: 4),
              Text(
                label,
                style: const TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.w600,
                  color: Colors.white,
                ),
                textAlign: TextAlign.center,
              ),
            ],
          ),
        ),
      ),
    );
  }
}
