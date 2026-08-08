import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../utils/responsive.dart';

/// Represents the current state of the voice interaction.
enum PulseState {
  /// No activity — waiting for input.
  idle,

  /// Microphone active, listening for speech.
  listening,

  /// Text-to-speech is speaking.
  speaking,

  /// Processing a request (e.g. AI inference).
  processing,

  /// An error occurred.
  error,
}

/// An animated pulse circle widget for voice / speech / listening states.
///
/// Used as the main voice interaction UI element. Displays a colored circle
/// with an inner icon, optional expanding pulse rings, and a text label.
class PulseCircle extends StatefulWidget {
  /// The current voice state (controls color, icon, animation).
  final PulseState state;

  /// Overall size of the circle (diameter).
  final double size;

  /// Optional callback when the circle is tapped.
  final VoidCallback? onTap;

  /// Whether to show the text label below the circle.
  final bool showLabel;

  const PulseCircle({
    super.key,
    this.state = PulseState.idle,
    this.size = 160,
    this.onTap,
    this.showLabel = true,
  });

  @override
  State<PulseCircle> createState() => _PulseCircleState();
}

class _PulseCircleState extends State<PulseCircle>
    with TickerProviderStateMixin {
  late final AnimationController _controller;

  // ─── Lifecycle ───────────────────────────────────────

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 2),
    )..repeat();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  // ─── State-derived properties ────────────────────────

  /// Background color of the main circle.
  Color get _stateColor {
    switch (widget.state) {
      case PulseState.idle:
        return const Color(0xFF141829);
      case PulseState.listening:
        return const Color(0xFF39FF14);
      case PulseState.speaking:
        return const Color(0xFF00F0FF);
      case PulseState.processing:
        return const Color(0xFFFFB300);
      case PulseState.error:
        return const Color(0xFFFF1744);
    }
  }

  /// Icon displayed inside the circle.
  IconData get _stateIcon {
    switch (widget.state) {
      case PulseState.idle:
        return Icons.mic_none_rounded;
      case PulseState.listening:
        return Icons.mic_rounded;
      case PulseState.speaking:
        return Icons.volume_up_rounded;
      case PulseState.processing:
        return Icons.hourglass_bottom_rounded;
      case PulseState.error:
        return Icons.close_rounded;
    }
  }

  /// Short label displayed below the circle.
  String get _stateLabel {
    switch (widget.state) {
      case PulseState.idle:
        return 'Idle';
      case PulseState.listening:
        return 'Listening';
      case PulseState.speaking:
        return 'Speaking';
      case PulseState.processing:
        return 'Processing';
      case PulseState.error:
        return 'Error';
    }
  }

  /// Semantics / accessibility label for screen readers.
  String get _semanticsLabel {
    switch (widget.state) {
      case PulseState.idle:
        return 'Trợ lý giọng nói đang chờ. Nhấn để bắt đầu ghi âm.';
      case PulseState.listening:
        return 'Đang lắng nghe. Nhấn để kết thúc và xử lý.';
      case PulseState.speaking:
        return 'Đang đọc.';
      case PulseState.processing:
        return 'Đang xử lý yêu cầu.';
      case PulseState.error:
        return 'Đã xảy ra lỗi. Nhấn để thử lại.';
    }
  }

  /// Color used for the text label and pulse rings.
  Color get _stateLabelColor {
    switch (widget.state) {
      case PulseState.idle:
        return const Color(0xFF8892B0);
      case PulseState.listening:
        return const Color(0xFF39FF14);
      case PulseState.speaking:
        return const Color(0xFF00F0FF);
      case PulseState.processing:
        return const Color(0xFFFFB300);
      case PulseState.error:
        return const Color(0xFFFF1744);
    }
  }

  /// Whether expanded pulse rings should be shown.
  bool get _showPulseRings {
    return widget.state == PulseState.listening ||
        widget.state == PulseState.speaking ||
        widget.state == PulseState.processing;
  }

  // ─── Build ───────────────────────────────────────────

  @override
  Widget build(BuildContext context) {
    return Semantics(
      button: widget.onTap != null,
      label: _semanticsLabel,
      child: GestureDetector(
        onTap: () {
          if (widget.onTap != null) {
            HapticFeedback.selectionClick();
            widget.onTap!();
          }
        },
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            SizedBox(
              width: widget.size,
              height: widget.size,
              child: Stack(
                alignment: Alignment.center,
                children: [
                  // Expanding pulse rings (listening / speaking / processing)
                  if (_showPulseRings)
                    AnimatedBuilder(
                      animation: _controller,
                      builder: (context, _) {
                        return CustomPaint(
                          size: Size(widget.size, widget.size),
                          painter: _PulseRingPainter(
                            animationValue: _controller.value,
                            color: _stateLabelColor,
                            ringSize: widget.size,
                          ),
                        );
                      },
                    ),

                  // Rotating arc ring (processing only)
                  if (widget.state == PulseState.processing)
                    AnimatedBuilder(
                      animation: _controller,
                      builder: (context, _) {
                        return CustomPaint(
                          size: Size(widget.size, widget.size),
                          painter: _RotatingRingPainter(
                            animationValue: _controller.value,
                            color: _stateLabelColor,
                          ),
                        );
                      },
                    ),

                  // Main circle — transitions color smoothly
                  AnimatedContainer(
                    duration: const Duration(milliseconds: 300),
                    width: widget.size * 0.7,
                    height: widget.size * 0.7,
                    decoration: BoxDecoration(
                      color: _stateColor,
                      shape: BoxShape.circle,
                      border: Border.all(
                        color: Colors.white,
                        width: 4,
                      ),
                    ),
                    child: Icon(
                      _stateIcon,
                      color: Colors.white,
                      size: widget.size * 0.4,
                    ),
                  ),
                ],
              ),
            ),

            // Bottom text label
            if (widget.showLabel) ...[
              const SizedBox(height: 12),
              Text(
                _stateLabel,
                style: TextStyle(
                  fontSize: Responsive.textScale(context, 22, min: 16, max: 26),
                  fontWeight: FontWeight.bold,
                  color: _stateLabelColor,
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

// ─── Painters ──────────────────────────────────────────

/// Paints two expanding circular rings that pulse outward with fading opacity.
///
/// Ring 1 follows the raw animation value; ring 2 is offset by half a cycle.
class _PulseRingPainter extends CustomPainter {
  final double animationValue;
  final Color color;
  final double ringSize;

  _PulseRingPainter({
    required this.animationValue,
    required this.color,
    required this.ringSize,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = 3.0
      ..strokeCap = StrokeCap.round;

    final center = Offset(size.width / 2, size.height / 2);

    // Ring diameter expands from ringSize * 0.50 → ringSize * 0.85
    // → radius expands from ringSize * 0.25 → ringSize * 0.425
    const minRadiusFactor = 0.25;
    const maxRadiusFactor = 0.425;
    final baseRadius = minRadiusFactor * ringSize;
    final radiusRange = (maxRadiusFactor - minRadiusFactor) * ringSize;

    // Ring 1 (phase = 0.0)
    final t1 = animationValue;
    final radius1 = baseRadius + radiusRange * t1;
    final opacity1 = 0.3 * (1.0 - t1);
    paint.color = color.withValues(alpha: opacity1);
    canvas.drawCircle(center, radius1, paint);

    // Ring 2 (phase offset = 0.5)
    final t2 = (animationValue + 0.5) % 1.0;
    final radius2 = baseRadius + radiusRange * t2;
    final opacity2 = 0.3 * (1.0 - t2);
    paint.color = color.withValues(alpha: opacity2);
    canvas.drawCircle(center, radius2, paint);
  }

  @override
  bool shouldRepaint(_PulseRingPainter oldDelegate) {
    return oldDelegate.animationValue != animationValue ||
        oldDelegate.color != color;
  }
}

/// Paints a rotating arc ring used in the [PulseState.processing] state.
class _RotatingRingPainter extends CustomPainter {
  final double animationValue;
  final Color color;

  _RotatingRingPainter({
    required this.animationValue,
    required this.color,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = 3.0
      ..strokeCap = StrokeCap.round
      ..color = color.withValues(alpha: 0.6);

    final center = Offset(size.width / 2, size.height / 2);
    final radius = size.width / 2 - 4;

    canvas.drawArc(
      Rect.fromCircle(center: center, radius: radius),
      animationValue * 2 * math.pi,
      1.5 * math.pi, // 270° arc
      false,
      paint,
    );
  }

  @override
  bool shouldRepaint(_RotatingRingPainter oldDelegate) {
    return oldDelegate.animationValue != animationValue;
  }
}
