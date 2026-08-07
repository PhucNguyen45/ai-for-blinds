import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../utils/responsive.dart';

/// Large oval/rounded action button for the Neon Pulse theme.
class NeonButton extends StatefulWidget {
  final IconData icon;
  final String label;
  final String? subtitle;
  final Color color;
  final VoidCallback onTap;
  final bool glow;
  final bool fullWidth;
  final String? semanticLabel;

  const NeonButton({
    super.key,
    required this.icon,
    required this.label,
    this.subtitle,
    this.color = const Color(0xFF00F0FF),
    required this.onTap,
    this.glow = true,
    this.fullWidth = true,
    this.semanticLabel,
  });

  @override
  State<NeonButton> createState() => _NeonButtonState();
}

class _NeonButtonState extends State<NeonButton> {
  @override
  Widget build(BuildContext context) {
    final Color textColor = widget.color == const Color(0xFF00F0FF)
        ? const Color(0xFF000000)
        : const Color(0xFFFFFFFF);
    final minH = Responsive.scale(context, 72, min: 56, max: 80);

    return Semantics(
      button: true,
      label: widget.semanticLabel ?? widget.label,
      hint: 'Nhấn hai lần để kích hoạt',
      child: GestureDetector(
        onTap: () {
          HapticFeedback.mediumImpact();
          widget.onTap();
        },
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 200),
          width: widget.fullWidth ? double.infinity : null,
          constraints: BoxConstraints(minHeight: minH),
          decoration: BoxDecoration(
            color: widget.color,
            borderRadius: BorderRadius.circular(20),
            border: Border.all(
              color: widget.color.withValues(alpha: 0.5),
              width: 1,
            ),
            boxShadow: widget.glow
                ? [
                    BoxShadow(
                      color: widget.color.withValues(alpha: 0.3),
                      blurRadius: 12,
                      spreadRadius: 4,
                    ),
                  ]
                : null,
          ),
          padding: EdgeInsets.symmetric(
            horizontal: Responsive.scale(context, 24, min: 16, max: 32),
            vertical: Responsive.scale(context, 20, min: 14, max: 24),
          ),
          child: Row(
            children: [
              Icon(widget.icon, size: 40, color: const Color(0xFFFFFFFF)),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      widget.label,
                      style: TextStyle(
                        fontSize: 22,
                        fontWeight: FontWeight.bold,
                        color: textColor,
                      ),
                    ),
                    if (widget.subtitle != null) ...[
                      Text(
                        widget.subtitle!,
                        style: TextStyle(
                          fontSize: 14,
                          color: const Color(0xFFFFFFFF).withValues(alpha: 0.7),
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

/// Large circular action button for the Neon Pulse theme.
class NeonCircleButton extends StatelessWidget {
  final IconData icon;
  final String label;
  final Color color;
  final double size;
  final VoidCallback onTap;
  final bool glow;
  final String? semanticLabel;

  const NeonCircleButton({
    super.key,
    required this.icon,
    required this.label,
    this.color = const Color(0xFF00F0FF),
    this.size = 140,
    required this.onTap,
    this.glow = true,
    this.semanticLabel,
  });

  double _responsiveSize(BuildContext context) {
    final shortest = MediaQuery.of(context).size.shortestSide;
    return (shortest * (size / 414)).clamp(100.0, size);
  }

  @override
  Widget build(BuildContext context) {
    final s = _responsiveSize(context);
    return Semantics(
      button: true,
      label: semanticLabel ?? label,
      hint: 'Nhấn hai lần để kích hoạt',
      child: GestureDetector(
        onTap: () {
          HapticFeedback.mediumImpact();
          onTap();
        },
        child: Container(
          width: s,
          height: s,
          decoration: BoxDecoration(
            color: color,
            shape: BoxShape.circle,
            border: Border.all(
              color: const Color(0xFFFFFFFF),
              width: 4,
            ),
            boxShadow: glow
                ? [
                    BoxShadow(
                      color: color.withValues(alpha: 0.35),
                      blurRadius: 15,
                      spreadRadius: 5,
                    ),
                  ]
                : null,
          ),
          child: Icon(
            icon,
            size: s * 0.45,
            color: const Color(0xFFFFFFFF),
          ),
        ),
      ),
    );
  }
}

/// Small rectangular media-control button for the Neon Pulse theme.
class NeonIconButton extends StatelessWidget {
  final IconData icon;
  final String label;
  final Color color;
  final VoidCallback onTap;
  final double size;
  final String? semanticLabel;

  const NeonIconButton({
    super.key,
    required this.icon,
    required this.label,
    required this.color,
    required this.onTap,
    this.size = 72,
    this.semanticLabel,
  });

  @override
  Widget build(BuildContext context) {
    final s = Responsive.scale(context, size, min: 56, max: 88);
    final iconS = Responsive.scale(context, 32, min: 24, max: 40);
    final fontS = Responsive.textScale(context, 13, min: 11, max: 16);
    return Semantics(
      button: true,
      label: semanticLabel ?? label,
      hint: 'Nhấn hai lần để kích hoạt',
      child: GestureDetector(
        onTap: () {
          HapticFeedback.mediumImpact();
          onTap();
        },
        child: Container(
          constraints: BoxConstraints(
            minWidth: s,
            minHeight: s * 0.7,
          ),
          decoration: BoxDecoration(
            color: color,
            borderRadius: BorderRadius.circular(16),
          ),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(icon, size: iconS, color: const Color(0xFFFFFFFF)),
              const SizedBox(height: 4),
              Text(
                label,
                style: TextStyle(
                  fontSize: fontS,
                  fontWeight: FontWeight.bold,
                  color: Color(0xFFFFFFFF),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
