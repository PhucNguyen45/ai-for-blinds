import 'dart:ui' show ImageFilter;

import 'package:flutter/material.dart';

import '../utils/responsive.dart';

/// A glassmorphism-style bottom-anchored container with blur backdrop
/// and neon border.
///
/// Meant to be placed at the bottom of a [Stack] or [Column] with [Spacer].
/// It takes up whatever space its content needs (not a fixed height).
class GlassBottomSheetContainer extends StatelessWidget {
  const GlassBottomSheetContainer({
    super.key,
    required this.child,
    this.title,
    this.subtitle,
    this.icon,
    this.color = const Color(0xFF00F0FF),
    this.showDragHandle = true,
  });

  /// The primary content body (fills remaining space below header/divider).
  final Widget child;

  /// Optional bold title displayed in the header row.
  final String? title;

  /// Optional muted subtitle displayed below [title].
  final String? subtitle;

  /// Optional icon shown to the left of [title].
  final IconData? icon;

  /// Tint colour used for the header icon (defaults to primary cyan).
  final Color color;

  /// Whether to render the drag‑handle bar near the top.
  final bool showDragHandle;

  @override
  Widget build(BuildContext context) {
    return ClipRRect(
      borderRadius: const BorderRadius.only(
        topLeft: Radius.circular(28),
        topRight: Radius.circular(28),
      ),
      child: BackdropFilter(
        filter: ImageFilter.blur(sigmaX: 12, sigmaY: 12),
        child: Container(
          decoration: BoxDecoration(
            color: const Color(0xFF141829).withValues(alpha: 0.85),
            border: const Border(
              top: BorderSide(color: Color(0xFF1E2A4A), width: 1),
              left: BorderSide(color: Color(0xFF1E2A4A), width: 1),
              right: BorderSide(color: Color(0xFF1E2A4A), width: 1),
              bottom: BorderSide.none,
            ),
          ),
          child: SafeArea(
            child: Padding(
              padding: const EdgeInsets.only(bottom: 16),
              child: Column(
                children: <Widget>[
                  // ── Drag handle ──────────────────────────────────────────
                  if (showDragHandle)
                    Container(
                      margin: const EdgeInsets.only(top: 12, bottom: 4),
                      width: 40,
                      height: 4,
                      decoration: BoxDecoration(
                        color: const Color(0xFF8892B0),
                        borderRadius: BorderRadius.circular(2),
                      ),
                    ),

                  // ── Header row (icon + title/subtitle) ──────────────────
                  if (title != null)
                    Padding(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 20,
                        vertical: 8,
                      ),
                      child: Row(
                        children: <Widget>[
                          if (icon != null) ...[
                            Icon(icon, size: 28, color: color),
                            const SizedBox(width: 12),
                          ],
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: <Widget>[
                                Text(
                                  title!,
                                  style: TextStyle(
                                    fontSize: Responsive.textScale(context, 24, min: 18, max: 28),
                                    fontWeight: FontWeight.bold,
                                    color: Color(0xFFFFFFFF),
                                  ),
                                ),
                                if (subtitle != null)
                                  Text(
                                    subtitle!,
                                    style: TextStyle(
                                      fontSize: Responsive.textScale(context, 16, min: 13, max: 20),
                                      color: Color(0xFF8892B0),
                                    ),
                                  ),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ),

                  // ── Divider when header is present ──────────────────────────
                  if (title != null)
                    const Divider(
                      color: Color(0xFF1E2A4A),
                      height: 1,
                      thickness: 1,
                    ),

                  // ── Body content ─────────────────────────────────────────
                  Expanded(
                    child: Padding(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 20,
                        vertical: 8,
                      ),
                      child: child,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
