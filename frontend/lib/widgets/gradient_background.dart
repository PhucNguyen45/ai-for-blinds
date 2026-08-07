import 'dart:math' as math;
import 'dart:ui';
import 'package:flutter/material.dart';

/// Animated gradient background for the Neon Pulse dark theme.
///
/// Provides a full-screen animated gradient with optional drifting glow circles
/// and subtle CRT-style scan lines overlay. Designed as a base layer for screens
/// that need a rich, living background without distracting from content.
///
/// All animations are very subtle and slow — the gradient shifts over 30 seconds
/// and glow circles drift over 45 seconds.
class GradientBackground extends StatefulWidget {
  /// Optional child widget placed on top of the background.
  final Widget? child;

  /// Whether to show very faint horizontal scan lines (CRT effect).
  /// Defaults to false.
  final bool showScanLines;

  /// Whether to show animated glowing blur circles.
  /// Defaults to false.
  final bool showGlow;

  /// If true, wraps the entire background in a [Semantics] widget with
  /// label `'Nền ứng dụng'` and [excludeSemantics] set to true.
  /// Use for purely decorative backgrounds to hide them from screen readers.
  /// Defaults to false.
  final bool excludeFromSemantics;

  /// Custom gradient colors for the background.
  /// Defaults to deep navy-black tones matching the dark theme:
  /// `[Color(0xFF0A0E1A), Color(0xFF0D1120), Color(0xFF0A0E1A)]`.
  final List<Color>? gradientColors;

  const GradientBackground({
    super.key,
    this.child,
    this.showScanLines = false,
    this.showGlow = false,
    this.excludeFromSemantics = false,
    this.gradientColors,
  });

  @override
  State<GradientBackground> createState() => _GradientBackgroundState();
}

class _GradientBackgroundState extends State<GradientBackground>
    with TickerProviderStateMixin {
  /// Controller for the slow gradient direction shift (30s loop, auto-reverse).
  late final AnimationController _gradientController;
  late final Animation<Alignment> _gradientAnimation;

  /// Controller for the glow circles drift (45s loop, no reverse).
  late final AnimationController _glowController;

  static const List<Color> _defaultColors = [
    Color(0xFF0A0E1A),
    Color(0xFF0D1120),
    Color(0xFF0A0E1A),
  ];

  List<Color> get _colors => widget.gradientColors ?? _defaultColors;

  @override
  void initState() {
    super.initState();

    _gradientController = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 30),
    )..repeat(reverse: true);

    _gradientAnimation = Tween<Alignment>(
      begin: Alignment.topLeft,
      end: Alignment.bottomRight,
    ).animate(_gradientController);

    _glowController = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 45),
    )..repeat();
  }

  @override
  void dispose() {
    _gradientController.dispose();
    _glowController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    Widget content = Stack(
      children: <Widget>[
        // ── 1. Animated gradient background ─────────────
        RepaintBoundary(
          child: AnimatedBuilder(
            animation: _gradientAnimation,
            builder: (BuildContext context, Widget? child) {
              final Alignment alignment = _gradientAnimation.value;
              return Container(
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    begin: alignment,
                    end: Alignment(-alignment.x, -alignment.y),
                    colors: _colors,
                  ),
                ),
              );
            },
          ),
        ),

        // ── 2. Glow effect (large blurred circles that drift) ───
        if (widget.showGlow)
          RepaintBoundary(
            child: _GlowDrift(controller: _glowController),
          ),

        // ── 3. Subtle scan lines overlay ─────────────
        if (widget.showScanLines)
          const Positioned.fill(
            child: RepaintBoundary(
              child: CustomPaint(
                painter: _ScanLinesPainter(),
              ),
            ),
          ),

        // ── 4. Optional child content ────────────────
        if (widget.child != null)
          Positioned.fill(child: widget.child!),
      ],
    );

    // Wrap with Semantics to exclude decorative background from screen readers.
    if (widget.excludeFromSemantics) {
      content = Semantics(
        label: 'Nền ứng dụng',
        excludeSemantics: true,
        child: content,
      );
    }

    return content;
  }
}

/// Paints very faint horizontal scan lines for a retro CRT effect.
///
/// Each line is drawn at 4px vertical intervals with 0.5px stroke width
/// and near-transparent white color (2% opacity).
class _ScanLinesPainter extends CustomPainter {
  const _ScanLinesPainter();

  @override
  void paint(Canvas canvas, Size size) {
    final Paint paint = Paint()
      ..color = Colors.white.withValues(alpha: 0.02)
      ..strokeWidth = 0.5;

    for (double y = 0; y < size.height; y += 4) {
      canvas.drawLine(Offset(0, y), Offset(size.width, y), paint);
    }
  }

  @override
  bool shouldRepaint(covariant _ScanLinesPainter oldDelegate) => false;
}

/// Animated glow circles that slowly drift across the background.
///
/// Paints two large circles (cyan at 30% opacity, purple at 20% opacity)
/// at staggered positions and applies [BackdropFilter] with a heavy blur
/// ([ImageFilter.blur] sigma 120) to create a soft, ambient glow.
///
/// Positions drift slowly over the 45-second animation cycle using
/// sinusoidal offsets with different frequencies for organic motion.
class _GlowDrift extends StatelessWidget {
  final AnimationController controller;

  const _GlowDrift({required this.controller});

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: controller,
      builder: (BuildContext context, Widget? child) {
        final double progress = controller.value;
        final double t = progress * 2 * math.pi;

        // Cyan circle — slowly drifts in the upper-left region.
        final double cx = -0.55 + 0.15 * math.sin(t * 0.7);
        final double cy = -0.45 + 0.12 * math.cos(t * 0.5);

        // Purple circle — slowly drifts in the lower-right region.
        final double px = 0.25 + 0.18 * math.cos(t * 0.6);
        final double py = 0.15 + 0.15 * math.sin(t * 0.4);

        return Stack(
          children: <Widget>[
            // Cyan glow source
            Positioned.fill(
              child: Align(
                alignment: Alignment(cx, cy),
                child: Container(
                  width: 320,
                  height: 320,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: const Color(0xFF00F0FF).withValues(alpha: 0.3),
                  ),
                ),
              ),
            ),

            // Purple glow source
            Positioned.fill(
              child: Align(
                alignment: Alignment(px, py),
                child: Container(
                  width: 380,
                  height: 380,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: const Color(0xFF9D4EDD).withValues(alpha: 0.2),
                  ),
                ),
              ),
            ),

            // BackdropFilter blurs circles and gradient into soft ambient glow.
            // The transparent child means the filtered result is shown directly.
            Positioned.fill(
              child: BackdropFilter(
                filter: ImageFilter.blur(sigmaX: 120, sigmaY: 120),
                child: Container(color: Colors.transparent),
              ),
            ),
          ],
        );
      },
    );
  }
}
